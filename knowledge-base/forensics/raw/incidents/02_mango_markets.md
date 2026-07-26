---
protocol: Mango Markets
date: 2022-10-11
attack_type: oracle_manipulation
chain: Solana
funds_lost_usd: 116000000
source: Blockworks, CoinDesk, Chainalysis (see references below)
---

## Summary
Mango Markets, a margin trading and lending platform on Solana, lost around $116 million after a trader named Avraham Eisenberg manipulated the price of the platform's own governance token (MNGO) to artificially inflate his collateral value, then borrowed the platform's entire treasury against that inflated collateral. Unusually, the attacker later negotiated with Mango's DAO to keep a portion of the funds as a "bug bounty" in exchange for returning the rest.

## What Happened
The attacker funded two separate accounts with USDC. Using one account, he opened a massive long position on the MNGO perpetual futures market; using the other, he took the opposite short position. He then used a relatively small amount of capital (a few million dollars) to aggressively buy MNGO on external, low-liquidity spot markets, driving its price up over 20x within minutes. Because Mango's price oracle referenced this same thin market, the inflated price flowed directly into Mango's own valuation of the attacker's leveraged MNGO position. With his position now valued far above its real worth, the attacker borrowed heavily against it, draining most of Mango's available treasury in stablecoins, SOL, and other assets before the price collapsed back down.

## Root Cause
Mango's oracle faithfully reported the real, if artificially inflated, market price of MNGO — the oracle infrastructure itself worked exactly as designed. The actual vulnerability was architectural: the platform allowed a thinly-traded, low-liquidity token to be used as high-value collateral without any position size limits or safeguards against rapid, extreme price movements in that specific market.

## Why It Matters
This incident is frequently cited as the clearest example of "oracle manipulation without any code bug" — nothing in Mango's smart contracts malfunctioned, and no line of Solidity or Rust was flawed in the traditional sense. The lesson for forensics analysis is that not every major fund loss traces back to a static-analysis-detectable code flaw; some trace back to insufficient economic safeguards around illiquid or manipulable price feeds, which static analysis tools like Slither cannot catch since the code itself is technically correct.