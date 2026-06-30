# run as: python scripts/backfill_simplestorage.py
from web3 import Web3
from pathlib import Path

src = Path("hardhat/contracts/SimpleStorage.sol").read_text(encoding="utf-8")
h = Web3.keccak(text=src).hex()
print(f"contract_hash: {h}")