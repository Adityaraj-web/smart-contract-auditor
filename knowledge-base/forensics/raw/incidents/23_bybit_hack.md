---
protocol: Bybit
date: 2025-02-21
attack_type: access_control_failure
chain: Ethereum
funds_lost_usd: 1500000000
source: NCC Group, Sygnia, Verichains (see references below)
---

## Summary
Bybit, one of the world's largest cryptocurrency exchanges, lost approximately $1.5 billion in ETH from a single cold wallet — the largest cryptocurrency theft ever recorded — after North Korea's Lazarus Group compromised the infrastructure behind Safe{Wallet}, the third-party multisignature platform Bybit relied on, and used it to silently swap what Bybit's own signers saw on screen for a completely different transaction.

## What Happened
Bybit secured its Ethereum cold wallet with a Safe (formerly Gnosis Safe) multisignature contract requiring three authorized signers to approve any transaction. Days before the theft, attackers compromised a developer's machine within Safe{Wallet}'s own infrastructure and used that access to inject malicious JavaScript into a cloud storage bucket serving Safe's web interface — code written to activate only when it detected Bybit's specific cold wallet address. During a routine, previously-approved-pattern transfer from the cold wallet to a warm wallet, Bybit's signers saw exactly what they expected on their screens: a normal transfer of a set amount of ETH. In reality, the compromised interface had silently substituted a different transaction entirely — one that called a hidden function to upgrade the wallet's underlying smart contract logic to a version controlled by the attacker. Each signer, trusting the display, approved and signed what they believed was a routine transfer using their hardware wallets. Once the required signatures were collected, this substituted transaction executed instead, handing the attacker full administrative control over the cold wallet's logic and letting them drain roughly 401,000 ETH in a single subsequent call.

## Root Cause
An access control failure achieved through a supply-chain compromise, one layer removed from Bybit itself: the vulnerability was not in Bybit's own systems, private keys, or smart contracts, but in a third-party vendor's infrastructure that Bybit's entire signing process implicitly trusted. The security guarantee of a multisignature wallet — that multiple independent humans must review and approve a transaction — was defeated not by forging signatures, but by making sure the humans doing the reviewing were shown something other than the truth.

## Why It Matters
Bybit is a critical fourth access-control example, and the largest-scale one in this corpus, because it demonstrates the same fundamental failure mode as Radiant Capital — a compromised display layer defeating an otherwise well-designed multisig process — but originating from a trusted third-party vendor's infrastructure rather than compromising the victim organization's own developers directly. This distinguishes "supply-chain compromise of shared wallet infrastructure" as its own forensics pattern, distinct from a direct malware attack on an organization's own personnel: an incident review must consider not just what a victim's own team controlled, but what third-party services their signing process depended on and implicitly trusted without independent verification.