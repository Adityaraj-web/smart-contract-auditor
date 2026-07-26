---
protocol: Qubit Finance
date: 2022-01-27
attack_type: logic_error, bridge_cross_chain_exploit
chain: Ethereum, BNB Chain
funds_lost_usd: 80000000
source: Halborn, CoinDesk, SlowMist (see references below)
---

## Summary
Qubit Finance, a lending protocol with a cross-chain bridge (QBridge) connecting Ethereum and BNB Chain, lost approximately $80 million after an attacker discovered that calling a legacy, unused deposit function — rather than the newer, correct one — could trick the bridge into minting collateral tokens without any real assets ever being deposited.

## What Happened
QBridge originally had a single `deposit` function for handling incoming transfers, which was later replaced by a newer `depositETH` function specifically for native ETH deposits. The old `deposit` function, however, was never removed from the contract. The attacker called this legacy `deposit` function while attaching zero actual ETH to the transaction, but supplying crafted input data, including a token address of the zero address. Because the contract's internal transfer-verification call did not correctly revert when handed this zero address, the transaction was treated as successful despite no real value ever changing hands. Critically, both the legacy `deposit` function and the newer `depositETH` function emitted the exact same on-chain event when called. The bridge's relaying logic, which watched only for this event to decide when to mint corresponding tokens on BNB Chain, could not distinguish a genuine ETH deposit from this spoofed, valueless one. The attacker repeated this process multiple times, minting a large quantity of collateral tokens (qXETH) on BNB Chain backed by nothing, then used this fabricated collateral to borrow and drain the protocol's real assets.

## Root Cause
A logic error rooted in incomplete cleanup after a code change: an old function was left in production after being functionally superseded, and both the old and new functions emitted identical events, meaning the bridge's off-chain monitoring could not tell which deposit path had actually been used — or verify that real funds had moved at all.

## Why It Matters
Qubit is a valuable complement to Poly Network and Wormhole as a bridge exploit: rather than an access control failure or a cryptographic signature bypass, this incident is a pure "legacy code path" problem — deprecated functionality that should have been removed but wasn't, combined with insufficiently strict validation in a widely-used utility function. It's a useful reminder for forensics analysis that bridges relying on watching for specific events, rather than directly verifying underlying value transfer, are only as trustworthy as the assumption that only one legitimate code path can emit that event.