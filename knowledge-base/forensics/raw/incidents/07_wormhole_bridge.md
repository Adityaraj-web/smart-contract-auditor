---
protocol: Wormhole
date: 2022-02-02
attack_type: signature_replay_verification_bypass, bridge_cross_chain_exploit
chain: Solana, Ethereum
funds_lost_usd: 326000000
source: Halborn, CertiK, Nomos Labs (see references below)
---

## Summary
Wormhole, a major token bridge connecting Solana and Ethereum, lost approximately $326 million after an attacker found a way to bypass the bridge's guardian signature verification entirely, allowing them to mint 120,000 wrapped ETH on Solana with no legitimate backing whatsoever. The incident remains one of the largest bridge exploits ever recorded.

## What Happened
Minting wrapped assets on Wormhole requires a valid "VAA" (a signed message from Wormhole's guardian network) proving that the equivalent real asset has actually been locked on the source chain. The verification process on Solana relied on a now-deprecated system function to confirm that a separate signature-verification instruction had genuinely been executed immediately beforehand. That deprecated function checked only that some instruction had run — it never confirmed the account passed to it was actually Solana's real, trusted system-provided instructions account. The attacker crafted a fake account that mimicked this expected structure closely enough to pass the check, tricking the contract into believing legitimate guardian signatures had verified a mint request that, in reality, had never been signed by anyone. This forged approval let the attacker mint 120,000 wETH out of nothing, which they then partially bridged back to real ETH on Ethereum.

## Root Cause
A signature/account verification bypass: the code checked for the mere existence of a prior verification step rather than cryptographically confirming which specific account had performed it, allowing a spoofed account to satisfy a check it should never have passed.

## Why It Matters
Wormhole demonstrates a particularly subtle and dangerous class of vulnerability — not a missing check, but a check that exists and appears to do its job while actually verifying the wrong thing. It is also, fundamentally, a bridge exploit: the entire attack surface existed because Wormhole's design requires trusting a signature-verification step to authorize minting assets across chains, the same structural pattern that makes any token bridge a high-value target. For forensics purposes, incidents involving unauthorized minting on a bridge should always prompt close inspection of exactly what an account or signature verification step confirms versus what it's assumed to confirm; the gap between the two is often where the exploit lives.