---
protocol: Wintermute
date: 2022-09-20
attack_type: access_control_failure
chain: Ethereum
funds_lost_usd: 160000000
source: Halborn, Forbes, The Block (see references below)
---

## Summary
Wintermute, a major cryptocurrency market-making firm, lost approximately $160 million from its DeFi operations after an attacker exploited a known cryptographic weakness in a vanity-address generation tool to reconstruct the private key of one of Wintermute's admin wallets.

## What Happened
Wintermute had generated some of its wallet addresses, including an administrative "hot wallet" with permissions over its DeFi vault contract, using a tool called Profanity. Profanity generates vanity addresses (custom addresses with a chosen prefix, such as repeating zeros) by seeding its random number generator with only a 32-bit value rather than a properly large, cryptographically secure seed. Roughly a week before the hack, a separate security disclosure had publicly revealed that this weak seeding made it computationally feasible for an attacker with significant GPU resources to brute-force the seed and reconstruct the private key behind any Profanity-generated address. Wintermute had taken the precaution of removing ether balances from its own vulnerable hot wallet in response to that disclosure, but did not revoke that same wallet's administrative permissions over its DeFi vault contract. An attacker, having independently reconstructed the private key, used the compromised wallet's still-active admin privileges to call a vault function and redirect its funds, draining roughly $160 million across stablecoins, ETH, BTC, and other assets in Wintermute's DeFi vault.

## Root Cause
An access control failure stemming from weak private key generation: the wallet's authority came from possessing a private key, and that key was generated in a way that made it mathematically recoverable by anyone with knowledge of the underlying flaw and enough compute power — no phishing, social engineering, or smart contract bug was involved at all.

## Why It Matters
Wintermute is an important contrast to Ronin and Harmony as an access-control incident: rather than a stolen key, a forgotten permission, or a code vulnerability, the "access control failure" here was that the credential itself — the private key — was never as secret as assumed, because of how it had been generated. This case is also a sharp illustration of incomplete incident response: Wintermute correctly identified the exposure and moved the vulnerable wallet's funds, but failed to also revoke that wallet's administrative permissions elsewhere in the system, leaving the actual attack vector open even after the underlying flaw was publicly known.