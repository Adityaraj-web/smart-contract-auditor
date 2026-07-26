---
protocol: Poly Network
date: 2021-08-10
attack_type: access_control_failure
chain: Ethereum, BNB Chain, Polygon
funds_lost_usd: 611000000
source: Wikipedia, Kudelski Security, Chainalysis (see references below)
---

## Summary
Poly Network, a cross-chain interoperability protocol, lost approximately $611 million across Ethereum, BNB Chain, and Polygon in what was at the time the largest DeFi theft in history. In an unusual turn, the attacker — who claimed to be a "white hat" exposing the vulnerability — returned nearly all of the funds within about two weeks.

## What Happened
Poly Network's cross-chain design relied on a highly privileged contract (EthCrossChainManager) that was meant to only be callable through a tightly controlled verification process involving a set of trusted "keeper" public keys stored in a separate contract (EthCrossChainData). The attacker discovered that the function responsible for verifying and executing cross-chain transactions could itself be used to call back into the keeper-management contract and simply overwrite the legitimate keeper public keys with the attacker's own. Once the attacker's key was accepted as a valid keeper, any subsequent cross-chain transaction "signed" by that key was treated as fully authorized, allowing the attacker to withdraw assets freely from the locked liquidity pools on all three chains.

## Root Cause
An access control failure: a function intended only to relay verified cross-chain messages was not properly restricted from modifying the very keeper list used to establish that verification's trustworthiness in the first place. This created a privilege escalation path — one contract with legitimate, narrow permissions was able to reach into another contract's most sensitive state.

## Why It Matters
Poly Network is the textbook example of how cross-chain bridges concentrate enormous value behind a small number of privileged functions, and how a single access control oversight in that privileged path can cascade into a nine-figure loss across multiple chains simultaneously. For forensics purposes, this incident underscores why permission boundaries between "message relaying" logic and "critical state modification" logic need to be treated as entirely separate concerns, never conflated even when the same contract deployer controls both.