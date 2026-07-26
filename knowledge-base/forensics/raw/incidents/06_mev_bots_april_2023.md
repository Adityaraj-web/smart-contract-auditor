---
protocol: Multiple MEV Sandwich Bots (via MEV-Boost Relay)
date: 2023-04-03
attack_type: front_running_mev
chain: Ethereum
funds_lost_usd: 25000000
source: Halborn, CoinDesk, Blockhead (see references below)
---

## Summary
A malicious Ethereum validator exploited a flaw in the MEV-Boost relay system — the infrastructure many validators use to auction off block-building rights to specialized "searchers" — to reverse-engineer the contents of several profitable sandwich-attack bundles and steal roughly $25 million in funds that a group of MEV sandwich bots had positioned to capture for themselves.

## What Happened
MEV-Boost relays are designed to let a validator receive a fully-built, signed block from a searcher without seeing its contents in advance, preventing the validator from stealing the searcher's strategy. The malicious validator submitted a deliberately invalid block (with its parent root and state root both set to zero) to the relay. Because the relay's software did not properly handle this malformed submission, it responded by revealing the actual transaction contents that should have gone into that block — including several live sandwich-attack bundles from MEV bots that had already committed real capital to executing profitable trades. With full visibility into those bundles, the validator reconstructed and resubmitted a new, valid block that captured the bots' intended profit for himself, executing this same technique across multiple transactions to drain five different MEV bots.

## Root Cause
An error-handling flaw in the relay software: submitting a deliberately invalid block should have simply been rejected outright, but instead triggered a response that leaked information (the actual intended block contents) that was supposed to remain confidential until the block was finalized.

## Why It Matters
This incident is a useful edge case for a forensics tool to recognize: the "victims" here were themselves automated extractive trading bots, not ordinary users or a DeFi protocol's treasury, and the vulnerability lived in auxiliary blockchain infrastructure (a relay) rather than in a smart contract on-chain. It illustrates that "front-running/MEV" as an attack category isn't limited to a bot sandwiching a human user — it also covers infrastructure-level exploits where extractive actors prey on each other.