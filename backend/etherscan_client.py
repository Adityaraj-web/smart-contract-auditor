"""
backend/etherscan_client.py

Etherscan API V2 client for the forensics ingestion layer.
Handles chain routing, rate limiting, and retries, and wraps the specific
free-tier endpoints needed to reconstruct a transaction's on-chain footprint.

Known free-tier limitations (documented deliberately, not papered over):
  - "Internal Transactions by Block Range" became a Pro-only endpoint as of
    July 1, 2026. Multi-tx window reconstruction here falls back to
    address-scoped txlistinternal/txlist queries instead (see
    get_internal_transactions_by_address / get_normal_transactions_by_address).
  - txlistinternal (by txhash or by address) only returns NON-ZERO-VALUE
    internal calls. Zero-value internal calls — common in exploits that move
    tokens via ERC-20 accounting rather than native ETH — are invisible to
    this endpoint. Decoded event logs from the transaction receipt partially
    compensate, since token movement usually still emits a Transfer event.
"""

import os
import time
import requests
from typing import Optional


CHAIN_IDS = {
    "mainnet": 1,
    "ethereum": 1,
    "sepolia": 11155111,
}

BASE_URL = "https://api.etherscan.io/v2/api"


class EtherscanRateLimiter:
    """Sleep-based throttle to stay under the free-tier 5 calls/sec cap."""

    def __init__(self, calls_per_second: float = 4.0):
        self._min_interval = 1.0 / calls_per_second
        self._last_call = 0.0

    def wait(self):
        elapsed = time.monotonic() - self._last_call
        remaining = self._min_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_call = time.monotonic()


class EtherscanClient:
    def __init__(self, chain: str, api_key: Optional[str] = None):
        """
        chain is required — no default. Forensics targets are almost always
        mainnet incidents, while the audit side of this project deploys to
        Sepolia. Silently defaulting to either one risks a call running
        against the wrong network without erroring.
        """
        self.api_key = api_key or os.environ.get("ETHERSCAN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ETHERSCAN_API_KEY not set. Add it to .env or pass api_key explicitly."
            )
        self.chain_id = CHAIN_IDS.get(chain.lower())
        if self.chain_id is None:
            raise ValueError(f"Unsupported chain '{chain}'. Supported: {list(CHAIN_IDS)}")
        self.chain_name = chain.lower()
        self._limiter = EtherscanRateLimiter()

    def _request(self, params: dict, max_retries: int = 3) -> dict:
        query = {"chainid": self.chain_id, "apikey": self.api_key, **params}
        data = {}

        for attempt in range(max_retries):
            self._limiter.wait()
            resp = requests.get(BASE_URL, params=query, timeout=15)

            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue

            resp.raise_for_status()
            data = resp.json()

            benign_empty = data.get("message") in ("No transactions found", "No records found")
            if data.get("status") == "0" and not benign_empty and attempt < max_retries - 1:
                time.sleep(1)
                continue

            return data

        return data

    # ---- Proxy module: the transaction itself ----

    def get_transaction(self, tx_hash: str) -> dict:
        return self._request({
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": tx_hash,
        })

    def get_block_by_number(self, block_number_hex: str) -> dict:
        """block_number_hex must be a '0x...' hex string (as returned by
        eth_getTransactionByHash) — used only to recover the block timestamp,
        since the transaction object itself doesn't carry one."""
        return self._request({
            "module": "proxy",
            "action": "eth_getBlockByNumber",
            "tag": block_number_hex,
            "boolean": "false",
        })

    def get_transaction_receipt(self, tx_hash: str) -> dict:
        """Includes status, gasUsed, and the full event-log list scoped to this
        tx — this is why we don't need the address+block-range getLogs endpoint
        at all for the single-tx case."""
        return self._request({
            "module": "proxy",
            "action": "eth_getTransactionReceipt",
            "txhash": tx_hash,
        })

    # ---- Account module: internal + normal transactions ----

    def get_internal_transactions_by_hash(self, tx_hash: str) -> dict:
        """Free tier. Returns ONLY non-zero-value internal calls — see module
        docstring."""
        return self._request({
            "module": "account",
            "action": "txlistinternal",
            "txhash": tx_hash,
        })

    def get_internal_transactions_by_address(
        self, address: str, start_block: int, end_block: int, page: int = 1, offset: int = 1000
    ) -> dict:
        """Free-tier substitute for the now-Pro-only block-range endpoint."""
        return self._request({
            "module": "account",
            "action": "txlistinternal",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "page": page,
            "offset": offset,
            "sort": "asc",
        })

    def get_normal_transactions_by_address(
        self, address: str, start_block: int, end_block: int, page: int = 1, offset: int = 1000
    ) -> dict:
        return self._request({
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "page": page,
            "offset": offset,
            "sort": "asc",
        })

    # ---- Contract module: source resolution ----

    def get_source_code(self, address: str) -> dict:
        """Verified-contract endpoints remain fully free regardless of the
        July 2026 tier changes."""
        return self._request({
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
        })