---
protocol: KyberSwap Elastic
date: 2023-11-22
attack_type: logic_error, flash_loan_enabled
chain: Ethereum, Optimism, Polygon, Arbitrum, Avalanche, Base
funds_lost_usd: 48000000
source: Halborn, BlockSec, CertiK (see references below)
---

## Summary
KyberSwap Elastic, a concentrated-liquidity decentralized exchange, lost approximately $48 million across six different blockchain networks after an attacker exploited an extremely subtle rounding error in its liquidity accounting, one so small it required precisely engineered transactions to trigger.

## What Happened
KyberSwap Elastic used a concentrated liquidity design (similar to Uniswap V3), where liquidity providers commit funds to specific price ranges divided into discrete "ticks." When a trade's price crosses one of these tick boundaries, the protocol needs to correctly recalculate how much liquidity is active. The attacker used a flash loan to push a pool's price into a range with no existing liquidity, then carefully constructed a sequence of small swaps designed so that each swap's final price landed just barely on the wrong side of a tick boundary — close enough to functionally cross it, but not close enough to trigger the function responsible for correctly updating the liquidity value. This let the attacker's added liquidity be "double-counted": once from the normal minting process, and again from the protocol's internal accounting failing to properly adjust when the tick boundary was technically crossed. By repeating this pattern across many pools and six different chains, the attacker drained far more in tokens than they had ever actually deposited.

## Root Cause
A logic error in mathematical precision: two different internal calculations that were each individually correct in isolation were assumed to always produce matching results, but a rounding discrepancy between them meant they occasionally disagreed at the exact boundary of a price tick — and that disagreement, though tiny, could be deliberately and repeatedly triggered to corrupt the protocol's understanding of how much liquidity actually existed.

## Why It Matters
KyberSwap is a valuable fourth logic-error example because its root cause is neither a missing check (like Furucombo or Qubit) nor an added-later patch gone wrong (like Euler) — it's a precision/rounding mismatch between two mathematically related but independently implemented calculations. This is a particularly hard class of bug for both human auditors and automated tools to catch, since each individual calculation can pass every unit test in isolation; the flaw only appears at the exact numerical boundary where the two calculations' results diverge. Forensics analysis of complex AMM math should specifically check whether boundary conditions (tick crossings, rounding directions, edge-of-range values) were tested against each other, not just validated independently.