---
protocol: Nomad Bridge
date: 2022-08-01
attack_type: signature_replay_verification_bypass, bridge_cross_chain_exploit
chain: Ethereum, Moonbeam
funds_lost_usd: 190000000
source: Immunefi, Halborn, The Block (see references below)
---

## Summary
Nomad, a cross-chain messaging and token bridge, lost approximately $190 million in what became known as a "crowd-looted" hack — after a routine contract upgrade accidentally marked an empty, zero-value hash as a "trusted" verification root, the first attacker's discovery was copied almost verbatim by hundreds of unrelated wallets within a couple of hours.

## What Happened
Nomad's bridge verifies cross-chain messages by checking them against a "committed root" — essentially a trusted reference hash proving a message is legitimate. During a routine upgrade, the initialization process set this trusted root to the zero-value hash (0x00) rather than a genuine root. Because uninitialized storage in the Ethereum Virtual Machine defaults to zero, and the verification logic did not explicitly reject a root of exactly zero, every single message — regardless of its actual content — was treated as automatically "proven," since checking it against the trusted root of 0x00 would trivially match. The first attacker to discover this simply called the bridge's processing function directly with a request to withdraw far more tokens than they had ever deposited, with no real proof required at all. Once the exploit transaction became visible on-chain, the attack required no smart contract expertise to replicate: anyone could copy the successful transaction, swap in their own wallet address as the recipient, and drain funds themselves. Within roughly two hours, nearly 300 separate addresses had joined in.

## Root Cause
A signature/message verification bypass caused by an initialization error: a security-critical value (the trusted root) was left at its default zero value, and the verification logic failed to explicitly treat the zero value as untrusted — turning what should have been an impossible-to-forge proof requirement into something that matched by default.

## Why It Matters
Nomad is a valuable companion case to Wormhole: both involve a verification step that appeared to function correctly but was actually checking against a corrupted or meaningless reference value. Nomad additionally demonstrates a unique forensics challenge — a single root-cause vulnerability being exploited by hundreds of independent, unrelated actors almost simultaneously, meaning "who is the attacker" is a genuinely different and harder question here than in a single-actor incident. Forensics tooling analyzing bridge exploits should always check whether a "trusted" reference value could ever equal a default/uninitialized value, and treat that as a critical finding regardless of whether it has been exploited yet.