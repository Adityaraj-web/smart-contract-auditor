---
protocol: Curve Finance
date: 2023-07-30
attack_type: reentrancy
chain: Ethereum
funds_lost_usd: 61000000
source: Halborn, Hacken, CertiK (see references below)
---

## Summary
Curve Finance, one of the largest decentralized exchanges for stablecoin trading, lost around $61 million (with related protocols like Alchemix, JPEG'd, and Metronome accounting for further losses) after attackers discovered that several of its liquidity pools were vulnerable to reentrancy — not because of a mistake in Curve's own Solidity-equivalent code, but because of a zero-day bug in the Vyper compiler itself.

## What Happened
Curve writes some of its contracts in Vyper, a Python-inspired smart contract language that competes with Solidity. Certain Vyper compiler versions (0.2.15, 0.2.16, and 0.3.0) contained a bug in how they implemented reentrancy locks — a standard protection meant to prevent a function from being called again before its first execution finishes. The compiler bug caused two different functions that were each individually protected by a reentrancy lock to use separate, non-shared storage slots for tracking whether the lock was active, rather than one shared slot. This meant that while a single function correctly blocked being re-entered by itself, an attacker could still re-enter a *different* function on the same contract mid-execution, because that second function's lock variable had never actually been triggered. Attackers exploited this cross-function gap on Curve's alETH/msETH/pETH stablecoin pools, repeatedly draining liquidity through interleaved calls to different pool functions before balances were finalized.

## Root Cause
A compiler-level defect, not a developer logic error: the reentrancy guard mechanism itself, generated automatically by the affected Vyper versions, failed to properly share lock state across functions in the same contract. Any project that compiled with one of the three affected Vyper versions carried this same latent vulnerability regardless of how carefully its own Solidity-equivalent source code had been written or audited.

## Why It Matters
This incident is an important counterpoint to the standard reentrancy narrative established by The DAO: not every reentrancy vulnerability stems from a developer forgetting the checks-effects-interactions pattern. Sometimes the vulnerability is introduced by the toolchain itself, invisible even to a careful line-by-line audit of the source code, and only discoverable by knowing which compiler version compiled the deployed bytecode. Forensics analysis of a reentrancy-pattern exploit should always check compiler version and known compiler-level CVEs, not just the contract's own source logic.