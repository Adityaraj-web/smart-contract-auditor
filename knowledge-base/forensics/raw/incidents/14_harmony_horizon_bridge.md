---
protocol: Harmony Horizon Bridge
date: 2022-06-23
attack_type: bridge_cross_chain_exploit, access_control_failure
chain: Harmony, Ethereum, BNB Chain
funds_lost_usd: 100000000
source: CNBC, Halborn, Elliptic (see references below)
---

## Summary
The Harmony Horizon Bridge, connecting the Harmony blockchain to Ethereum and BNB Chain, lost approximately $100 million after attackers — later linked to North Korea's Lazarus Group — compromised just two of the five private keys needed to approve withdrawals from the bridge's multisig wallet.

## What Happened
Horizon's bridge secured withdrawals with a multisignature scheme requiring only 2 of 5 total signing keys to approve any transaction — a notably low threshold for a bridge holding this much value. Attackers obtained two of these five private keys, reportedly through a compromise of the systems or processes used to manage them (each individual key was encrypted with a passphrase and a key management service, but ultimately the attacker gained functional control of two of them). With two valid signatures in hand, the attacker was able to authorize fraudulent withdrawal transactions directly, draining roughly 85,837 ETH along with other assets across eleven separate transactions on the Ethereum and BNB Chain sides of the bridge.

## Root Cause
An access control and operational security failure, not a smart contract code bug: Harmony's own investigation found no vulnerability in the bridge's contract logic itself. The vulnerability was that the security of the entire bridge rested on protecting only five private keys, with just two of them sufficient to move funds — a threshold that gave an attacker a comparatively easy target once they found any means to compromise even a small number of the key holders or their key management processes.

## Why It Matters
Harmony is an important contrast case for a forensics tool to have alongside Ronin and Wormhole: all three are bridge exploits, but Harmony's root cause was purely about how few real-world individuals or systems needed to be compromised to move funds, entirely separate from any code-level flaw. This reinforces that "bridge exploit" as a category spans a wide range of underlying causes — smart contract logic bugs, cryptographic verification bypasses, and pure operational key-management failures all fall under the same outward symptom (unauthorized funds leaving a bridge), but require completely different remediation.