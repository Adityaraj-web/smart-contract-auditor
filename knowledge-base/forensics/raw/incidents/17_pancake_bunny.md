---
protocol: PancakeBunny
date: 2021-05-19
attack_type: flash_loan_enabled, oracle_manipulation
chain: BNB Chain
funds_lost_usd: 45000000
source: Halborn, Amber Group, CoinDesk (see references below)
---

## Summary
PancakeBunny, a yield-farming aggregator on BNB Chain, lost around $45 million after an attacker used flash loans to distort the price of its BUNNY governance token within its own reward-minting logic, tricking the protocol into minting nearly 7 million BUNNY tokens for the attacker out of thin air.

## What Happened
PancakeBunny's reward-minting function calculated how many BUNNY tokens to award a user based on the current market value of BNB and USDT within specific liquidity pools it referenced directly on-chain, rather than through an independent, manipulation-resistant price feed. The attacker took out a very large flash loan of BNB and USDT across multiple pools, then used part of it to violently swing the price ratio in the exact liquidity pools that PancakeBunny's minting function consulted. With the pool's reported price now artificially skewed, the attacker triggered PancakeBunny's reward-claim function, which calculated a mint amount based on this manipulated price — resulting in a reward payout worth vastly more than what the attacker had legitimately earned. The attacker immediately sold the freshly minted BUNNY tokens on the open market, crashing its price by more than 95% in the process, then repaid the flash loans, keeping the difference as profit.

## Root Cause
An oracle manipulation vulnerability made exploitable specifically by flash loans: the protocol's own reward logic trusted a real-time, on-chain price calculation from a liquidity pool that could be temporarily and dramatically distorted within a single transaction, with no safeguard (such as a time-weighted average price) to smooth out or reject such an extreme, momentary swing.

## Why It Matters
PancakeBunny is a useful third flash-loan example alongside bZx and Cream Finance because the exploited mechanism is neither a borrowing/collateral check (bZx) nor an internal accounting ratio (Cream) — it is a token *minting* function whose payout size directly depends on a manipulable price. This distinguishes "flash loan used to steal existing funds" from "flash loan used to mint new tokens the protocol never intended to create," a meaningfully different failure mode worth its own recognition pattern in forensics analysis.