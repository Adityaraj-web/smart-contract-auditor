---
protocol: Ronin Network (Axie Infinity)
date: 2022-03-23
attack_type: bridge_cross_chain_exploit
chain: Ronin, Ethereum
funds_lost_usd: 625000000
source: CoinDesk, Halborn, Nordis Global (see references below)
---

## Summary
The Ronin Network, an Ethereum sidechain built to support the play-to-earn game Axie Infinity, lost approximately $625 million in ETH and USDC — at the time the largest crypto theft ever recorded — after attackers compromised enough validator private keys to forge fraudulent withdrawals from the Ronin bridge. The breach went undetected for six days.

## What Happened
Ronin's bridge required signatures from 5 of its 9 validator nodes to approve any withdrawal. Sky Mavis (Ronin's developer) directly controlled 4 of those validators. The 5th signature the attackers needed came from a third-party validator operated by the Axie DAO — one that had been temporarily granted permission to sign on Sky Mavis's behalf back in late 2021 to help manage high transaction volume, via an allowlist entry on a gas-free RPC node. That permission was never revoked even after it was no longer needed. Attackers who had compromised Sky Mavis's systems used this forgotten backdoor to obtain a signature from the Axie DAO validator, combined it with signatures from the 4 validators they already controlled directly, and used the resulting 5 valid signatures to authorize two large fraudulent withdrawals from the bridge contract.

## Root Cause
A combination of two failures: a centralization risk (Sky Mavis alone controlled 4 of the 9 signatures needed, well short of requiring broad, truly independent consensus) and an access control failure — a temporary, no-longer-needed permission grant to an RPC node was left active long after its purpose had ended, creating a forgotten path to a signature that should have required a fully independent, uncompromised validator's genuine participation.

## Why It Matters
Ronin is frequently cited as the definitive example of bridge security depending as much on validator decentralization and operational hygiene as on the correctness of the smart contract code itself — the bridge contract's logic worked exactly as intended, but the number of signatures effectively under one party's control, combined with a stale permission nobody remembered to clean up, made the "decentralized" 5-of-9 threshold far weaker than it appeared. Forensics analysis of bridge incidents should always ask not just "was the signature valid" but "how independent were the parties who actually held signing authority."