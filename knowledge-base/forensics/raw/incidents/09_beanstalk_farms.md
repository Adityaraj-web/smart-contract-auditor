---
protocol: Beanstalk Farms
date: 2022-04-17
attack_type: governance_attack, flash_loan_enabled
chain: Ethereum
funds_lost_usd: 182000000
source: CoinDesk, Immunefi, CertiK (see references below)
---

## Summary
Beanstalk Farms, an Ethereum-based algorithmic stablecoin protocol, lost its entire $182 million in collateral after an attacker used a single, massive flash loan to temporarily acquire more than two-thirds of the protocol's governance voting power and immediately pass a malicious proposal draining the treasury — all within one transaction.

## What Happened
Beanstalk's governance allowed proposals to be executed immediately, without the usual waiting period, if a proposal reached a two-thirds supermajority of voting power through an "emergency commit" function. Voting power was tied directly to how many governance tokens (Stalk) a wallet held at the moment of voting, with no mechanism to prevent that voting power from being acquired and used within the same transaction it was borrowed in. The attacker first submitted an apparently benign governance proposal (publicly framed as a charitable donation) containing hidden malicious code. A day later — satisfying Beanstalk's minimum proposal age requirement — the attacker took out flash loans totaling roughly $1 billion from Aave, Uniswap, and SushiSwap, converted the borrowed funds into Beanstalk's liquidity provider tokens, deposited them to instantly gain over two-thirds of all voting power, and immediately invoked the emergency commit function to execute their proposal. The proposal transferred nearly all of Beanstalk's treasury to the attacker's wallet. The attacker then swapped their gains back into the borrowed assets to repay the flash loans, keeping the profit — all inside a single atomic transaction.

## Root Cause
A governance design flaw: voting power was measured instantaneously rather than based on a time-weighted or pre-existing token balance (a "snapshot"), meaning anyone with enough capital — even capital that only exists for a few seconds via a flash loan — could temporarily out-vote every genuine long-term stakeholder in the protocol.

## Why It Matters
Beanstalk is the canonical example of why on-chain governance systems must be flash-loan resistant, typically by requiring voting power to be based on token holdings from a prior block or snapshot rather than the current transaction's balance. This incident also demonstrates multi-category classification in practice: it is simultaneously a governance attack (the exploited mechanism) and a flash-loan-enabled exploit (the tool that made the attack economically possible without the attacker risking their own capital) — both tags legitimately apply to the same incident.