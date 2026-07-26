---
protocol: Furucombo
date: 2021-02-27
attack_type: logic_error
chain: Ethereum
funds_lost_usd: 15000000
source: PeckShield, SlowMist, cmichel.io (see references below)
---

## Summary
Furucombo, a drag-and-drop tool for building custom DeFi transaction sequences, lost roughly $15 million in user funds after an attacker exploited an uninitialized proxy contract that Furucombo had whitelisted, using it to redirect Furucombo's trusted call path to a malicious contract.

## What Happened
Furucombo allowed its core contract to make delegatecalls to a whitelist of trusted external protocol contracts, including an Aave V2 proxy. Delegatecall executes the target's code but uses the caller's own storage — meaning if the target contract expects certain storage values to already be set, and they haven't been set yet from the caller's perspective, that storage slot is effectively still "empty" and can be initialized by anyone. The whitelisted Aave V2 proxy contract had never actually been initialized in the context of Furucombo's storage. The attacker exploited this by calling Furucombo's batch execution function, routing it to the Aave proxy's own `initialize` function, and setting the "implementation" address to a malicious contract they controlled. From that point on, any further delegatecall Furucombo made through that whitelisted address actually ran the attacker's code — with full access to the token approvals that thousands of Furucombo users had previously granted the protocol.

## Root Cause
A business logic flaw, not a coding bug in the traditional sense: the vulnerability existed because a contract that should never have been reachable in an uninitialized state was added to a trust whitelist without verifying that state truly was safe from that whitelist's calling context. No individual line of code was "wrong" — the flaw was in the trust and configuration decision layered on top of otherwise-functioning code.

## Why It Matters
Furucombo is a strong example of why static analysis alone often cannot catch every vulnerability class: the exploited condition depended on which contracts had been added to a dynamic, off-chain-configured whitelist, not on anything visible purely from reading Furucombo's own source code. Forensics analysis of similar "evil contract" or delegatecall-based incidents should specifically check whether a whitelisted or trusted external contract was ever left in an uninitialized or attacker-controllable state.