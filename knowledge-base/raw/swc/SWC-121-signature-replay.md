---
category: signature-replay
swc_id: SWC-121
source_type: swc
title: Missing Protection against Signature Replay Attacks
source_url: https://swcregistry.io/docs/SWC-121
---

Contracts sometimes accept an off-chain signed message as proof of
authorization instead of requiring an on-chain transaction directly —
for example, a user signs a message off-chain authorizing a transfer,
and a relayer submits it on their behalf, saving the user gas. The
contract verifies the signature came from the right address, then
executes the authorized action.

If the contract only checks that the signature is valid and doesn't
also track which signed messages have already been used, the exact
same valid signature can be submitted again — "replayed" — to trigger
the same authorized action a second time, a third time, or however
many times the attacker chooses, since a valid signature alone doesn't
expire or self-invalidate after first use.

This also applies across separate deployments and even separate
chains: a signature valid for one contract or one network can,
without proper safeguards, be replayed against a different deployment
of the same contract, or the same contract address on a different
chain. Mitigation: include a unique nonce in every signed message and
track used nonces on-chain, and include a chain ID and contract address
in the signed data itself so a signature is only ever valid in the
exact context it was created for.