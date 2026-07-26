---
protocol: Radiant Capital
date: 2024-10-16
attack_type: access_control_failure
chain: Arbitrum, BNB Chain
funds_lost_usd: 53000000
source: Halborn, Decrypt, Radiant Capital post-mortem (see references below)
---

## Summary
Radiant Capital, a cross-chain lending protocol, lost approximately $53 million after attackers — later linked to North Korean state-sponsored hacking groups — used sophisticated malware to trick three of its trusted developers into unknowingly signing malicious transactions that handed over control of its lending contracts.

## What Happened
Radiant secured its contracts with a multisignature scheme requiring 3 of 11 trusted signers to approve any critical transaction, using hardware wallets and a standard transaction-verification tool (Safe, formerly Gnosis Safe) as an extra layer of protection. The attackers first compromised at least three developers' devices using malware, reportedly delivered through a social-engineering approach involving a contact posing as a former contractor. Once installed, the malware could intercept and silently alter transaction data at the device level: developers would see what appeared to be a completely normal, routine transaction on their screen and in their transaction-simulation tools, but the actual data sent to their hardware wallet for cryptographic signing had been swapped for a malicious one — specifically, a call to transfer contract ownership to the attacker. Because hardware wallets sign whatever raw data they're given without independently re-verifying it against what the screen displayed, each developer unknowingly signed a legitimate-looking cryptographic approval for an action they never intended. Once the attacker collected three such poisoned signatures, they gained ownership control over Radiant's lending pool contracts and drained user funds from its markets on Arbitrum and BNB Chain.

## Root Cause
An access control failure achieved through device-level compromise rather than any code vulnerability: the security model assumed that if a human reviewed a transaction on screen and it looked correct, the signature that resulted genuinely authorized that same transaction — an assumption malware operating beneath the display layer was able to violate completely, undetected by hardware wallets, transaction simulators, or the developers' own careful review process.

## Why It Matters
Radiant Capital is a critical third access-control example because — unlike Ronin (a forgotten permission), Poly Network (a code-level privilege escalation), or Wintermute (a weak key-generation algorithm) — every individual security practice here was followed correctly: hardware wallets, transaction simulation, multiple independent signers, geographic distribution of signers. The attack succeeded anyway because the compromise happened at a layer none of those practices were designed to verify: whether the data a signer sees is actually the data being signed. This is a crucial forensics pattern to recognize — the presence of "best practice" security measures does not rule out access-control compromise, and forensics analysis should specifically consider device-level or supply-chain compromise as a distinct root cause from code-level or key-generation failures.