---
protocol: JaredfromSubway.eth (MEV Bot)
date: 2026-06-20
attack_type: front_running_mev
chain: Ethereum
funds_lost_usd: 7500000
source: Blockaid, Chainalysis, The Defiant (see references below)
---

## Summary
JaredfromSubway.eth, Ethereum's most prolific sandwich-attack bot — responsible for an estimated 70% of all sandwich attacks on the network — was itself drained of roughly $7.5 million after an attacker spent weeks building a "reverse honeypot" specifically engineered to exploit the bot's own automated, profit-seeking decision logic.

## What Happened
JaredfromSubway's bot operates by continuously scanning Ethereum's public mempool for pending trades it can profitably sandwich, automatically executing trades and approving token spending to whatever contracts its logic identifies as legitimate opportunities, with no human reviewing each individual decision. The attacker deployed 66 fake token contracts closely mimicking well-known assets like WETH, USDC, and USDT, pairing each with a fabricated liquidity pool designed to look, from the bot's automated perspective, like a genuine profitable sandwich opportunity. Over several weeks, the bot repeatedly interacted with these decoy pools exactly as it was programmed to, granting token-spending approvals to attacker-controlled helper contracts each time — approvals that, per its normal operating pattern, were never revoked afterward. Once enough standing approvals had accumulated across all 66 fake contracts, the attacker triggered a single coordinated transaction that called every backdoor at once, sweeping the bot's real holdings of ETH and stablecoins into an attacker-controlled wallet in one shot.

## Root Cause
A front-running/MEV-adjacent vulnerability turned inward: rather than the bot exploiting an ordinary trader, the bot's own automated, non-human-reviewed decision loop was itself the target. The exploit required no smart contract bug, phishing, or private key compromise — it succeeded purely because the bot's execution logic granted lasting token approvals to unvetted counterparty contracts as a routine part of chasing profitable-looking trades, with no mechanism to revoke or expire those approvals afterward.

## Why It Matters
This incident is an important second example for the front-running/MEV category because its root cause is entirely different from the earlier relay-level exploit: rather than infrastructure (a validator/relay bug), this attack exploited the automated decision-making logic of the extractive actor itself. It reframes what "MEV exploitation" can mean for a forensics tool — not just a bot preying on an ordinary user, but an attacker studying a bot's own operating pattern closely enough to build bait tailored precisely to what that bot's logic is designed to chase. Any automated on-chain trading system that grants standing token approvals without expiration or revocation carries this same structural risk, regardless of how sophisticated its opportunity-detection logic is.