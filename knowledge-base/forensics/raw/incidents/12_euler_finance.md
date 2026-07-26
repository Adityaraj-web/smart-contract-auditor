---
protocol: Euler Finance
date: 2023-03-13
attack_type: logic_error, flash_loan_enabled
chain: Ethereum
funds_lost_usd: 197000000
source: BlockSec, Hacken, Chainalysis (see references below)
---

## Summary
Euler Finance, an Ethereum lending protocol, lost approximately $197 million — the largest DeFi hack of 2023 at the time — after an attacker exploited a missing solvency check in a function called `donateToReserves`, artificially creating a severely under-collateralized position that could then be profitably liquidated by the same attacker.

## What Happened
Euler allowed users to "donate" their deposited eTokens (interest-bearing tokens representing a deposit) to the protocol's reserves via the `donateToReserves` function. The function let a user reduce their own collateral position without any check that they remained solvent afterward. The attacker took out a large flash loan, deposited part of it into Euler to receive eTokens, then borrowed heavily against that deposit to receive dTokens (debt tokens). Next, the attacker called `donateToReserves` to give away a large portion of their eToken collateral — an action that should have been blocked by a health check but was not — leaving their account with far more debt than remaining collateral. Because the position was now deeply undercollateralized, the attacker (using a second, coordinated address acting as liquidator) liquidated their own position, which under Euler's liquidation discount rules let them seize the remaining discounted collateral at a steep advantage rather than losing value, netting a large profit that was then used to repay the original flash loan.

## Root Cause
A logic error: the `donateToReserves` function had been added later as a fix for an earlier, smaller "first depositor" bug, but the fix itself was never tested for the specific combination of borrowing first and then donating collateral afterward — a gap that let a user manufacture their own liquidatable, undercollateralized position on demand.

## Why It Matters
Euler is one of the clearest examples of how a security patch, introduced to fix one vulnerability, can itself introduce a new and more severe one if it isn't tested against every existing code path it touches — in this case, the interaction between a newly-added donation function and the protocol's pre-existing liquidation logic. It is also a useful example of "self-liquidation for profit" as a distinct exploitation pattern, worth checking for whenever a forensics case involves the same address appearing as both the position being liquidated and the liquidator.