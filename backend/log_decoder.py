"""
backend/log_decoder.py

Deterministic event log decoding for the forensics pipeline.

Two-tier strategy, in order of precedence:
  1. If the emitting contract has a verified ABI (from Phase 2's contract
     resolution), decode using that ABI directly - the precise,
     contract-specific source of truth.
  2. Otherwise, fall back to a small, deliberately conservative table of
     TRULY universal, standardized event signatures: ERC-20/ERC-721
     Transfer/Approval, and WETH Deposit/Withdrawal. These have been
     unchanged and identical across virtually all compliant contracts for
     years, so this fallback is still fully deterministic - not a guess.

     Protocol-specific events (Aave's Borrow/Repay/FlashLoan, Compound-style
     events, etc.) are deliberately EXCLUDED from this fallback table: their
     exact signatures vary across protocol versions (Aave V1 vs V2 vs V3
     differ), so hardcoding one would misrepresent a protocol-specific,
     versioned event as if it were a universal standard. Major DeFi
     protocols are typically verified on Etherscan anyway (confirmed in the
     Phase 2 Euler smoke test), so tier 1 (verified ABI) is expected to
     handle these correctly instead.

Anything matching neither tier is returned as explicitly "undecoded" with
just the raw topic0, rather than silently dropped.

Deliberately uses eth_abi + Web3.keccak (both stable, public APIs) rather
than web3.py's internal event-decoding helpers (web3._utils.events), which
are not part of web3's public API contract and could change without notice.

IMPORTANT VERSION NOTE, found via direct testing rather than assumed: as of
web3.py v7 / hexbytes v1.x, HexBytes.hex() returns hex WITHOUT a '0x' prefix
(a breaking change from earlier versions). Etherscan's log topics always
include the '0x' prefix. _event_topic0() below explicitly normalizes this so
topic0 comparisons never silently fail due to a prefix mismatch.
"""

from typing import Optional
from eth_abi import decode as abi_decode
from web3 import Web3


def _event_topic0(signature: str) -> str:
    """Computes the 32-byte topic0 hash for an event signature string,
    e.g. 'Transfer(address,address,uint256)' -> '0x...' (always prefixed
    and lowercased, regardless of installed web3.py/hexbytes version)."""
    raw = Web3.keccak(text=signature).hex()
    if not raw.startswith("0x"):
        raw = "0x" + raw
    return raw.lower()


def _normalize_topic(topic: str) -> str:
    if not topic.startswith("0x"):
        topic = "0x" + topic
    return topic.lower()


def _decode_indexed_param(topic_hex: str, solidity_type: str):
    topic_hex = _normalize_topic(topic_hex)
    topic_bytes = bytes.fromhex(topic_hex[2:])
    return abi_decode([solidity_type], topic_bytes)[0]


def _decode_non_indexed_params(data_hex: str, solidity_types: list):
    if not solidity_types:
        return []
    data_hex = data_hex or "0x"
    data_bytes = bytes.fromhex(data_hex[2:] if data_hex.startswith("0x") else data_hex)
    if not data_bytes:
        return [None] * len(solidity_types)
    return list(abi_decode(solidity_types, data_bytes))


# Deliberately small and conservative - see module docstring for why
# protocol-specific events are excluded. Keyed by (topic0, topic_count),
# since Transfer/Approval have two valid interpretations (ERC-20 vs ERC-721)
# that share the same topic0 but differ in how many params are indexed.
_KNOWN_EVENT_DEFINITIONS = {
    "Transfer(address,address,uint256)": {
        3: {"standard": "ERC-20", "event_name": "Transfer",
            "indexed": [("from", "address"), ("to", "address")],
            "data": [("value", "uint256")]},
        4: {"standard": "ERC-721", "event_name": "Transfer",
            "indexed": [("from", "address"), ("to", "address"), ("tokenId", "uint256")],
            "data": []},
    },
    "Approval(address,address,uint256)": {
        3: {"standard": "ERC-20", "event_name": "Approval",
            "indexed": [("owner", "address"), ("spender", "address")],
            "data": [("value", "uint256")]},
        4: {"standard": "ERC-721", "event_name": "Approval",
            "indexed": [("owner", "address"), ("approved", "address"), ("tokenId", "uint256")],
            "data": []},
    },
    "Deposit(address,uint256)": {
        2: {"standard": "WETH", "event_name": "Deposit",
            "indexed": [("dst", "address")],
            "data": [("wad", "uint256")]},
    },
    "Withdrawal(address,uint256)": {
        2: {"standard": "WETH", "event_name": "Withdrawal",
            "indexed": [("src", "address")],
            "data": [("wad", "uint256")]},
    },
}

_TOPIC0_TO_DEFINITIONS = {
    _event_topic0(signature): variants
    for signature, variants in _KNOWN_EVENT_DEFINITIONS.items()
}


def _decode_known_signature(log: dict) -> Optional[dict]:
    topics = log.get("topics", [])
    if not topics:
        return None
    topic0 = _normalize_topic(topics[0])
    variants = _TOPIC0_TO_DEFINITIONS.get(topic0)
    if not variants:
        return None
    variant = variants.get(len(topics))
    if not variant:
        # topic0 matched a known signature but the topic count doesn't match
        # any known shape for it - safer to leave undecoded than guess.
        return None

    args = {}
    for (name, sol_type), topic_hex in zip(variant["indexed"], topics[1:]):
        args[name] = _decode_indexed_param(topic_hex, sol_type)

    data_types = [t for _, t in variant["data"]]
    data_values = _decode_non_indexed_params(log.get("data"), data_types)
    for (name, _), value in zip(variant["data"], data_values):
        args[name] = value

    return {
        "event_name": variant["event_name"],
        "standard": variant["standard"],
        "args": args,
        "decode_method": "known_signature",
    }


def _build_abi_event_index(abi: list) -> dict:
    index = {}
    if not abi:
        return index
    for entry in abi:
        if entry.get("type") != "event":
            continue
        inputs = entry.get("inputs", [])
        type_list = ",".join(i["type"] for i in inputs)
        signature = f"{entry['name']}({type_list})"
        index[_event_topic0(signature)] = entry
    return index


def _decode_with_abi(log: dict, abi_event_index: dict) -> Optional[dict]:
    topics = log.get("topics", [])
    if not topics or not abi_event_index:
        return None
    topic0 = _normalize_topic(topics[0])
    event_entry = abi_event_index.get(topic0)
    if not event_entry:
        return None

    inputs = event_entry.get("inputs", [])
    indexed_inputs = [i for i in inputs if i.get("indexed")]
    data_inputs = [i for i in inputs if not i.get("indexed")]

    if len(indexed_inputs) != len(topics) - 1:
        # ABI's indexed-param count disagrees with this log's actual topic
        # count - inconsistent, don't guess, fall through as undecoded.
        return None

    args = {}
    for input_def, topic_hex in zip(indexed_inputs, topics[1:]):
        args[input_def["name"]] = _decode_indexed_param(topic_hex, input_def["type"])

    data_types = [i["type"] for i in data_inputs]
    data_values = _decode_non_indexed_params(log.get("data"), data_types)
    for input_def, value in zip(data_inputs, data_values):
        args[input_def["name"]] = value

    return {
        "event_name": event_entry.get("name"),
        "standard": "verified_abi",
        "args": args,
        "decode_method": "verified_abi",
    }


def decode_all_logs(logs: list, contracts: dict) -> list:
    """
    Decodes every raw log from a transaction's receipt, in topic0/tier order
    described in the module docstring. Builds each verified contract's ABI
    event index once and reuses it across all matching logs, since the same
    few contracts (e.g. a single token) typically emit many logs in one tx.

    `contracts` is the {address: contract_info} dict from Phase 2's
    resolve_contracts() output (already lowercased keys).

    Returns a list sorted by logIndex - the one ordering key raw logs
    actually carry, so this track is safely, deterministically orderable
    (unlike trying to merge it with the internal-call track - see
    timeline_builder.py).
    """
    abi_index_cache = {}

    def get_abi_index(address: str) -> dict:
        if address not in abi_index_cache:
            abi = contracts.get(address, {}).get("abi")
            abi_index_cache[address] = _build_abi_event_index(abi) if abi else {}
        return abi_index_cache[address]

    decoded_logs = []
    for log in logs:
        address = (log.get("address") or "").lower()
        abi_index = get_abi_index(address)

        decoded = _decode_with_abi(log, abi_index) if abi_index else None
        if not decoded:
            decoded = _decode_known_signature(log)
        if not decoded:
            topics = log.get("topics", [])
            decoded = {
                "event_name": None,
                "standard": None,
                "args": None,
                "decode_method": "undecoded",
                "raw_topic0": _normalize_topic(topics[0]) if topics else None,
            }

        decoded["contract_address"] = address
        log_index_raw = log.get("logIndex")
        decoded["log_index"] = int(log_index_raw, 16) if log_index_raw else None
        decoded_logs.append(decoded)

    decoded_logs.sort(key=lambda d: d["log_index"] if d["log_index"] is not None else -1)
    return decoded_logs