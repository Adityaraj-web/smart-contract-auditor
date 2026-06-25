---
category: delegatecall
swc_id: SWC-112
source_type: swc
title: Delegatecall to Untrusted Callee
source_url: https://swcregistry.io/docs/SWC-112
---

`delegatecall` executes code from another contract in the context of
the calling contract — the called code runs using the caller's storage,
balance, and address, not its own. This is the mechanism behind
upgradeable proxy patterns and shared library contracts, but it means
the calling contract is fully trusting the callee to behave correctly,
since the callee can modify the caller's storage directly.

If the address being delegatecalled to is attacker-controlled, or if a
trusted library contract itself contains a bug, the consequences are
severe: an attacker can overwrite arbitrary storage slots in the
calling contract, including ownership variables, or — if the library
contract contains a `selfdestruct`, even one the original developers
considered safe — destroy the calling contract entirely, since
selfdestruct executed via delegatecall destroys the caller, not the
library.

Mitigation: only delegatecall to immutable, audited, trusted addresses,
and never to a library contract that itself contains a selfdestruct
reachable in any callable function.