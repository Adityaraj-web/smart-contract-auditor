---
protocol: dForce (Lendf.Me)
date: 2020-04-18
attack_type: reentrancy
chain: Ethereum
funds_lost_usd: 25000000
source: PeckShield, Quantstamp, dForce post-mortem (see references below)
---

## Summary
Lendf.Me, a Compound-style lending market built by dForce, lost approximately $25 million after an attacker exploited a reentrancy vulnerability made possible specifically by a lesser-known token standard (ERC777) that the platform had chosen to accept as collateral, ultimately draining about 99.5% of the protocol's total funds.

## What Happened
Lendf.Me allowed users to deposit various tokens as collateral, including imBTC — a synthetic Bitcoin token built on the ERC777 standard rather than the more common ERC20. Unlike ERC20, ERC777 tokens can notify a receiving smart contract the moment tokens are sent to it, via an automatic callback function, before the transfer itself is considered fully complete. The attacker first deposited a real amount of imBTC as collateral through Lendf.Me's supply function. They then triggered a second, tiny supply transaction — but embedded within the ERC777 callback this second transaction generated, before that second supply had finished updating Lendf.Me's records, the attacker called Lendf.Me's withdraw function to pull out their original deposit. Because Lendf.Me's internal accounting relied on stale, already-read balance data rather than rechecking the true state after the callback's interruption, the platform's records showed the attacker's original collateral as still present even though it had already been withdrawn. Repeating this cycle rapidly inflated the attacker's recorded imBTC collateral to a huge, entirely fictitious value, which they then used to borrow and drain nearly every other asset available across the platform's twelve lending markets.

## Root Cause
A reentrancy vulnerability enabled specifically by a token standard feature: ERC777's callback-on-transfer mechanism gave the attacker a reentry point that a standard ERC20 token, which has no equivalent automatic callback, would never have provided. Lendf.Me's core lending logic had been written and reasoned about as if all supported tokens behaved like simple ERC20 transfers, without accounting for the fact that accepting an ERC777 token as collateral silently introduced a reentrancy opportunity into every function that token could be deposited through.

## Why It Matters
Lendf.Me is a valuable fifth reentrancy example because, unlike The DAO's classic single-function pattern or Curve's compiler-level bug, this vulnerability was introduced by a token integration decision rather than anything in the lending contract's own core logic being obviously flawed in isolation. It illustrates a forensics pattern worth checking specifically: whenever a protocol accepts a token as collateral or for deposits, the token's own standard and callback behavior needs to be treated as part of that protocol's attack surface, not just the protocol's own internal function code. A contract can be reentrancy-safe against all the tokens its developers tested with and still be vulnerable the moment a token with automatic callbacks is added to its supported asset list.