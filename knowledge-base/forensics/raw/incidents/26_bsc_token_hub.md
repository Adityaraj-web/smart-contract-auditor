---
protocol: BSC Token Hub (BNB Chain / Binance Bridge)
date: 2022-10-06
attack_type: signature_replay_verification_bypass, bridge_cross_chain_exploit
chain: BNB Beacon Chain, BNB Smart Chain
funds_lost_usd: 586000000
source: Immunefi, Halborn, Elliptic (see references below)
---

## Summary
BSC Token Hub, the native bridge connecting BNB Beacon Chain and BNB Smart Chain, was exploited for approximately $586 million in newly minted BNB after an attacker discovered a way to forge a cryptographic Merkle proof, tricking the bridge into believing a fabricated withdrawal request had genuinely been verified.

## What Happened
The bridge verified cross-chain transactions using a Merkle proof system borrowed from Cosmos software, where a valid proof traces a path from a specific piece of data up through a tree of cryptographic hashes to a trusted root hash. The attacker first registered as an authorized "relayer" by depositing the required collateral, then took a real, legitimate proof from a transaction confirmed two years earlier and modified its payload — changing the recipient address and the amount to 1 million BNB. Under normal circumstances, altering the underlying data this way should have produced a completely different, invalid root hash when the proof was recalculated. However, a flaw in the underlying proof-verification library meant that certain modifications to specific parts of the tree structure could be made without actually changing the computed root hash, allowing the forged proof to pass verification as if it were the original, legitimate one. The attacker successfully repeated this twice, minting 2 million BNB directly into their own address before the network was halted.

## Root Cause
A signature/proof verification bypass at the cryptographic library level: the Merkle proof verification logic failed to ensure that every part of a submitted proof structure actually contributed to the computed root hash, leaving a gap where an attacker could alter proof contents in ways that didn't change the final hash the system checked against.

## Why It Matters
BSC Token Hub is a valuable third example in the signature/verification-bypass category because its mechanism is distinct from both Wormhole (a spoofed account satisfying an existence check) and Nomad (a trusted root accidentally left at zero): here, the cryptographic proof-verification math itself contained a flaw that allowed genuinely forged data to produce a valid-looking proof. This illustrates that verification bypasses can occur at multiple layers — application logic, initialization state, or the underlying cryptographic library itself — and forensics analysis of any exploited proof or signature check should examine all three layers rather than assuming a bug must be in the application code alone.