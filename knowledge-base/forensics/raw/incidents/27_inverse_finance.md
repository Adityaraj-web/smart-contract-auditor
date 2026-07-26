---
protocol: Inverse Finance
date: 2022-04-02
attack_type: oracle_manipulation
chain: Ethereum
funds_lost_usd: 15600000
source: PeckShield, CoinDesk, RedStone Oracles (see references below)
---

## Summary
Inverse Finance, an Ethereum lending protocol, lost approximately $15.6 million after an attacker manipulated the time-weighted average price (TWAP) oracle tracking its own governance token, briefly inflating its value enough to borrow far more than legitimate collateral would allow.

## What Happened
Inverse Finance's Anchor lending market accepted its own governance token, INV, as loan collateral, priced using a TWAP oracle sourced from a low-liquidity trading pool on SushiSwap. TWAP oracles are specifically designed to resist manipulation by averaging price over a window of time rather than trusting a single instantaneous price — but the specific window size Inverse's oracle used was too short relative to the pool's thin liquidity. The attacker withdrew funds from Tornado Cash to obscure their source, then executed a carefully sequenced set of trades across two adjacent blocks in the INV trading pool, sized precisely to manipulate the TWAP calculation despite its averaging mechanism. The attacker also funded 241 separate wallet addresses in advance and used them to crowd out the specific transaction ordering slot needed, ensuring their manipulation transaction would be included in the exact next block required for the exploit to work, and pre-empting any arbitrage bots that might have corrected the price before the attacker could act. With INV's oracle price temporarily and artificially elevated, the attacker deposited the now-overvalued token as collateral and borrowed a large basket of other assets, walking away with the difference once the price normalized.

## Root Cause
An oracle manipulation vulnerability distinct from a naive spot-price oracle: even a TWAP mechanism, specifically designed to resist manipulation, can still be exploited if its averaging window is too short relative to the liquidity of its underlying price source, and if an attacker is capable enough to precisely control transaction ordering across the small number of blocks that window actually spans.

## Why It Matters
Inverse Finance is a valuable fourth oracle example because it demonstrates that TWAP oracles — the standard prescribed fix for the kind of single-block manipulation seen in Mango Markets and PancakeBunny — are not automatically manipulation-proof; their safety depends entirely on the window length being long enough relative to the underlying pool's liquidity and typical trading volume. A forensics tool evaluating an oracle-manipulation incident should check not just whether a TWAP or averaging mechanism was present, but whether its specific parameters (window size, minimum liquidity assumptions) were adequate for the asset in question, since "we used a TWAP" is not by itself proof of manipulation resistance.