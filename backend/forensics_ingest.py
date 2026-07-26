"""
backend/forensics_ingest.py

Combines raw EtherscanClient calls into structured, deterministic building
blocks for a forensics report. This module does NOT interpret or narrate
anything — it only fetches and normalizes. Interpretation (attack timeline,
root cause narration) is Phase 3's job, working off this module's output.

Grows across Phase 2 steps:
  2.2 -> fetch_transaction_bundle()   (this step)
  2.3 -> + internal transactions
  2.4 -> + contract source resolution
  2.5 -> + optional multi-tx window
  2.6 -> ingest_transaction() ties all of the above into one call
"""

import json

# Phase 4 addition: prefer the package-style import so this module shares the
# SAME EtherscanClient module identity as anything else loaded via
# `backend.X` (e.g. main.py) — falls back to the flat import so this file
# still works unchanged when run standalone from inside backend/, exactly as
# in Phase 2/3 (e.g. `python forensics_ingest_smoketest.py`).
try:
    from backend.etherscan_client import EtherscanClient
except ImportError:
    from etherscan_client import EtherscanClient


class TransactionNotFoundError(Exception):
    """Raised when Etherscan returns no transaction for the given hash on the
    given chain — most often means either a typo'd hash or the tx exists on
    a *different* chain than the one specified."""
    pass


def _hex_to_int(value):
    """Etherscan's proxy module returns numeric fields as '0x...' hex strings.
    Returns None unchanged (e.g. contract-creation txs have to=None)."""
    if value is None:
        return None
    return int(value, 16)


def fetch_transaction_bundle(client: EtherscanClient, tx_hash: str) -> dict:
    """
    Fetches and normalizes the core transaction facts:
      - the transaction itself (from, to, value, input, gas)
      - its receipt (status, gasUsed, event logs)
      - its block timestamp (requires a second proxy call, since
        eth_getTransactionByHash doesn't include one)

    Returns a single flat dict. Raises TransactionNotFoundError if the hash
    doesn't resolve on the configured chain.
    """
    tx_response = client.get_transaction(tx_hash)
    tx = tx_response.get("result")

    if tx is None:
        raise TransactionNotFoundError(
            f"No transaction found for {tx_hash} on chain '{client.chain_name}'. "
            f"Check the hash, or confirm this tx actually lives on this chain "
            f"(e.g. a mainnet incident hash won't resolve against chain='sepolia')."
        )

    receipt_response = client.get_transaction_receipt(tx_hash)
    receipt = receipt_response.get("result") or {}

    block_number_hex = tx.get("blockNumber")
    block_timestamp = None
    if block_number_hex is not None:
        block_response = client.get_block_by_number(block_number_hex)
        block = block_response.get("result") or {}
        block_timestamp = _hex_to_int(block.get("timestamp"))

    # Raw, undecoded logs at this stage — ABI-based decoding happens in Step 2.4
    # once we know which emitting addresses have verified source available.
    raw_logs = receipt.get("logs", [])

    bundle = {
        "tx_hash": tx_hash,
        "chain": client.chain_name,
        "chain_id": client.chain_id,
        "block_number": _hex_to_int(block_number_hex),
        "block_timestamp": block_timestamp,  # unix epoch seconds, or None if lookup failed
        "from_address": tx.get("from"),
        "to_address": tx.get("to"),  # None => contract creation transaction
        "value_wei": _hex_to_int(tx.get("value")),
        "gas": _hex_to_int(tx.get("gas")),
        "gas_price_wei": _hex_to_int(tx.get("gasPrice")),
        "input_data": tx.get("input"),
        "status": receipt.get("status"),  # '0x1' success, '0x0' reverted
        "gas_used": _hex_to_int(receipt.get("gasUsed")),
        "logs": raw_logs,  # list of {address, topics, data, ...}, undecoded
    }

    return bundle


def _decimal_to_int(value):
    """Account-module endpoints (txlistinternal, txlist) return numeric fields
    as plain base-10 strings, NOT '0x...' hex like the proxy module does.
    Using _hex_to_int on these would silently misparse or crash — this is a
    deliberately separate helper so the two conventions never get mixed up."""
    if value is None or value == "":
        return None
    return int(value)


def fetch_internal_transactions(client: EtherscanClient, tx_hash: str) -> dict:
    """
    Fetches internal (message-call) transactions triggered by tx_hash.

    IMPORTANT LIMITATION, surfaced explicitly rather than hidden: this
    endpoint only returns internal calls that transferred non-zero native
    value. Internal calls that carry no ETH but still trigger contract logic
    (e.g. an internal call into a token contract's transfer/transferFrom,
    or a delegatecall used purely for logic execution) will NOT appear here.
    Those are more likely to surface later as decoded Transfer-style events
    in the receipt's logs (see fetch_transaction_bundle), once Step 2.4 gives
    us the ABI needed to decode them.

    An empty result therefore means "no non-zero-value internal ETH
    transfers" — it must NOT be read as "no internal activity occurred."
    """
    response = client.get_internal_transactions_by_hash(tx_hash)
    raw_results = response.get("result") or []

    # Etherscan returns a bare string (e.g. "No transactions found") in
    # `result` for some empty/error cases instead of a list — guard against
    # treating that string as iterable transaction data.
    if not isinstance(raw_results, list):
        raw_results = []

    internal_txs = []
    for entry in raw_results:
        internal_txs.append({
            "from_address": entry.get("from"),
            "to_address": entry.get("to"),
            "value_wei": _decimal_to_int(entry.get("value")),
            "contract_address": entry.get("contractAddress") or None,  # set for internal CREATEs
            "input_data": entry.get("input"),
            "call_type": entry.get("type"),  # e.g. "call", "create", "delegatecall"
            "gas": _decimal_to_int(entry.get("gas")),
            "gas_used": _decimal_to_int(entry.get("gasUsed")),
            "is_error": entry.get("isError") == "1",
            "err_code": entry.get("errCode") or None,
        })

    return {
        "internal_transactions": internal_txs,
        "limitation_note": (
            "Only non-zero-value internal calls are captured. Zero-value "
            "internal calls (common in token-accounting-only exploit steps) "
            "are absent from this list and must be inferred from decoded "
            "event logs instead."
        ),
    }


def collect_involved_addresses(bundle: dict, internal_result: dict) -> set:
    """
    Gathers every address that appears anywhere in the evidence collected so
    far, so each one can be resolved for verified source exactly once.
    Sources scanned: the tx's own from/to, every internal call's from/to/
    contractAddress (for internal CREATEs), and every log's emitting address.
    """
    addresses = set()

    if bundle.get("from_address"):
        addresses.add(bundle["from_address"])
    if bundle.get("to_address"):
        addresses.add(bundle["to_address"])

    for log in bundle.get("logs", []):
        if log.get("address"):
            addresses.add(log["address"])

    for internal_tx in internal_result.get("internal_transactions", []):
        for key in ("from_address", "to_address", "contract_address"):
            if internal_tx.get(key):
                addresses.add(internal_tx[key])

    # Normalize case — Etherscan is generally consistent but downstream
    # dict-keying by address should never silently split "0xAbc..." and
    # "0xabc..." into two separate entries.
    return {addr.lower() for addr in addresses if addr}


def fetch_contract_info(client: EtherscanClient, address: str) -> dict:
    """
    Resolves a single address to its verification status and, if verified,
    its source code / ABI / proxy metadata. Unverified addresses (very
    common for throwaway attacker contracts) are returned with
    verified=False rather than raising — an unverified contract is itself a
    forensically meaningful signal, not an error condition.
    """
    response = client.get_source_code(address)
    results = response.get("result") or []

    if not isinstance(results, list) or not results:
        return {"address": address, "verified": False, "resolution_error": True}

    entry = results[0]
    source_code = entry.get("SourceCode", "") or ""
    verified = source_code.strip() != ""

    info = {
        "address": address,
        "verified": verified,
        "contract_name": entry.get("ContractName") or None,
        "compiler_version": entry.get("CompilerVersion") or None,
        "is_proxy": entry.get("Proxy") == "1",
        "implementation_address": entry.get("Implementation") or None,
        "source_code": source_code if verified else None,
        "abi": None,
    }

    if verified:
        raw_abi = entry.get("ABI", "")
        try:
            info["abi"] = json.loads(raw_abi)
        except (json.JSONDecodeError, TypeError):
            # Some verified-but-proxy contracts return a placeholder ABI
            # string instead of real JSON — don't let that crash ingestion,
            # just leave abi=None and let Phase 3 fall back to raw logs.
            info["abi"] = None

    return info


def resolve_contracts(client: EtherscanClient, addresses: set) -> dict:
    """Resolves a batch of addresses, one getsourcecode call each (this is
    the endpoint that stays free regardless of the July 2026 tier changes).
    Returns {address: fetch_contract_info(...)} keyed by lowercased address."""
    return {address: fetch_contract_info(client, address) for address in addresses}


def _normalize_normal_tx(entry: dict) -> dict:
    return {
        "tx_hash": entry.get("hash"),
        "block_number": _decimal_to_int(entry.get("blockNumber")),
        "timestamp": _decimal_to_int(entry.get("timeStamp")),
        "from_address": entry.get("from"),
        "to_address": entry.get("to") or None,
        "value_wei": _decimal_to_int(entry.get("value")),
        "is_error": entry.get("isError") == "1",
        "method_id": entry.get("methodId") or None,
        "function_name": entry.get("functionName") or None,
    }


def _normalize_internal_tx(entry: dict) -> dict:
    return {
        "tx_hash": entry.get("hash"),
        "block_number": _decimal_to_int(entry.get("blockNumber")),
        "timestamp": _decimal_to_int(entry.get("timeStamp")),
        "from_address": entry.get("from"),
        "to_address": entry.get("to"),
        "value_wei": _decimal_to_int(entry.get("value")),
        "contract_address": entry.get("contractAddress") or None,
        "call_type": entry.get("type"),
        "is_error": entry.get("isError") == "1",
    }


def fetch_related_transactions(
    client: EtherscanClient,
    address: str,
    center_block: int,
    exclude_tx_hash: str,
    block_window: int = 2,
    max_pages: int = 3,
) -> dict:
    """
    Opt-in Step 2.5: reconstructs a candidate multi-tx window around the main
    transaction by scanning a single address's activity over a small block
    range. This is the free-tier substitute for the now-Pro-only "internal
    transactions by block range" endpoint (see module docstring in
    etherscan_client.py) — instead of scanning the whole block range for all
    activity, we scope to one address (typically the suspected attacker EOA,
    i.e. the main tx's from_address).

    This function only *fetches candidates* — deciding which of these, if
    any, actually form a coherent multi-step attack sequence is Phase 3's
    job, not this ingestion layer's.

    Caveat: if `address` is unusually active (e.g. it happens to be an
    exchange hot wallet or popular contract rather than a one-off attacker
    EOA), even a small block window could exceed max_pages * 1000 records.
    In that case results are truncated and `truncated=True` is set rather
    than silently fetching an unbounded number of pages.
    """
    start_block = max(0, center_block - block_window)
    end_block = center_block + block_window

    def _paginate(fetch_fn, normalize_fn):
        collected = []
        truncated = False
        for page in range(1, max_pages + 1):
            response = fetch_fn(address, start_block, end_block, page=page, offset=1000)
            raw_results = response.get("result") or []
            if not isinstance(raw_results, list) or not raw_results:
                break
            collected.extend(normalize_fn(e) for e in raw_results)
            if len(raw_results) < 1000:
                break
            if page == max_pages:
                truncated = True
        return collected, truncated

    normal_txs, normal_truncated = _paginate(
        client.get_normal_transactions_by_address, _normalize_normal_tx
    )
    internal_txs, internal_truncated = _paginate(
        client.get_internal_transactions_by_address, _normalize_internal_tx
    )

    # The main transaction will naturally appear in its own address's normal-tx
    # history within the window — exclude it here since it's already fully
    # represented by fetch_transaction_bundle(), and duplicating it under
    # "related" would misleadingly suggest it's a *separate* related event.
    normal_txs = [tx for tx in normal_txs if tx["tx_hash"] != exclude_tx_hash]

    return {
        "window_start_block": start_block,
        "window_end_block": end_block,
        "scanned_address": address.lower(),
        "related_normal_transactions": normal_txs,
        "related_internal_transactions": internal_txs,
        "truncated": normal_truncated or internal_truncated,
        "note": (
            "Candidates only — scoped to a single address over a small block "
            "window as a free-tier substitute for block-range internal-tx "
            "scanning. Whether these actually form part of the same attack "
            "sequence is an interpretive judgment, not decided here."
        ),
    }


def _related_window_addresses(related: dict) -> set:
    """Extracts any addresses appearing in the window results that weren't
    already captured from the main transaction's own evidence — so Step 2.4's
    resolve_contracts() is never called twice for the same address."""
    addresses = set()
    for tx in related.get("related_normal_transactions", []):
        for key in ("from_address", "to_address"):
            if tx.get(key):
                addresses.add(tx[key])
    for tx in related.get("related_internal_transactions", []):
        for key in ("from_address", "to_address", "contract_address"):
            if tx.get(key):
                addresses.add(tx[key])
    return {addr.lower() for addr in addresses if addr}


def ingest_transaction(
    tx_hash: str,
    chain: str,
    include_window: bool = False,
    block_window: int = 2,
    api_key: str = None,
) -> dict:
    """
    Top-level Phase 2 entry point. Fetches and normalizes everything Phase 3
    needs to reconstruct a deterministic attack timeline, without performing
    any interpretation itself — no root-cause guessing, no LLM calls, no
    taxonomy tagging. Just facts, structured, with every known gap in that
    evidence surfaced explicitly rather than hidden.

    chain must be passed explicitly ("mainnet" or "sepolia") — see the
    reasoning in EtherscanClient's constructor: forensics targets are almost
    always mainnet, while this project's audit side deploys to Sepolia, and
    a silent default risks running against the wrong chain without erroring.

    include_window=True additionally scans the main tx's sender address over
    a small block range (default ±2 blocks) as a free-tier substitute for
    the now-Pro-only block-range internal-tx endpoint. Off by default since
    it's an extra ~2-6 API calls and only useful when a multi-step attack is
    suspected.
    """
    client = EtherscanClient(chain=chain, api_key=api_key)

    bundle = fetch_transaction_bundle(client, tx_hash)
    internal_result = fetch_internal_transactions(client, tx_hash)

    addresses = collect_involved_addresses(bundle, internal_result)
    contracts = resolve_contracts(client, addresses)

    related_window = None
    if include_window:
        if not bundle.get("from_address"):
            raise ValueError(
                "Cannot build a related-transaction window without a from_address "
                "on the main transaction — this shouldn't normally happen."
            )
        related_window = fetch_related_transactions(
            client=client,
            address=bundle["from_address"],
            center_block=bundle["block_number"],
            exclude_tx_hash=tx_hash,
            block_window=block_window,
        )
        # Resolve any newly-discovered addresses from the window, but never
        # re-resolve one already fetched from the main tx's own evidence.
        new_addresses = _related_window_addresses(related_window) - set(contracts.keys())
        if new_addresses:
            contracts.update(resolve_contracts(client, new_addresses))

    return {
        "schema_version": "forensics-ingest-v1",
        "tx_hash": tx_hash,
        "chain": chain,
        "transaction": bundle,
        "internal_transactions": internal_result,
        "contracts": contracts,
        "related_window": related_window,  # None unless include_window=True
    }