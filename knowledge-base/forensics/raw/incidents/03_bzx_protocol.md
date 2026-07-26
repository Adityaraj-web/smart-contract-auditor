---
protocol: bZx Protocol
date: 2020-02-14
attack_type: flash_loan_enabled
chain: Ethereum
funds_lost_usd: 954000
source: CoinDesk, Quadriga Initiative, Aon Cyber Labs (see references below)
---

## Summary
bZx, an Ethereum lending and margin trading protocol, suffered two separate flash-loan-powered attacks within a single week in February 2020 — among the first widely publicized flash loan exploits in DeFi — resulting in combined losses of roughly $954,000. Small by later standards, this pair of incidents effectively introduced the flash loan attack as a distinct category of DeFi exploit.

## What Happened
In the first attack, the attacker borrowed 10,000 ETH via a flash loan, split it between opening a large leveraged short position on bZx's Fulcrum platform and acquiring wrapped Bitcoin (wBTC) on Compound as collateral. The leveraged short position forced bZx to buy a large amount of wBTC on Uniswap, and because the relevant market had low liquidity, this purchase caused severe slippage — driving the price of wBTC on that specific market far above its real value. A bug in bZx's risk logic failed to check for this slippage before finalizing the loan, leaving bZx holding an under-collateralized, effectively insolvent position while the attacker profited from the artificial price spike. Days later, a second attacker used a similar approach, this time manipulating a synthetic stablecoin (sUSD) price via Kyber Network's integrated price feed, again exploiting a check that failed to catch the manipulated collateral value.

## Root Cause
Both attacks exploited the same underlying weakness: a missing or broken slippage/price-sanity check in the loan collateralization logic, made exploitable specifically because flash loans allowed the attacker to deploy far more capital than they actually owned, all within a single atomic transaction with zero real risk of loss if the attack failed.

## Why It Matters
These were among the earliest attacks to demonstrate that DeFi's "composability" — protocols freely calling into each other — is a double-edged sword: it enables powerful financial products, but it also means a price feed sourced from one low-liquidity venue can be manipulated cheaply and then trusted elsewhere as ground truth. Any forensics case involving flash loans combined with unusual price movement on a secondary market should be checked against this exact pattern.