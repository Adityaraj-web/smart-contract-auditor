---
category: tx-origin
swc_id: SWC-115
source_type: swc
title: Authorization through tx.origin
source_url: https://swcregistry.io/docs/SWC-115
---

`tx.origin` returns the address that originally sent a transaction,
even if that transaction passed through several intermediate contract
calls. `msg.sender`, by contrast, returns whoever directly called the
current function — which could be the original wallet, or could be
another contract acting on its behalf.

Using `tx.origin` for authorization (`require(tx.origin == owner)`) is
unsafe because it can be bypassed via a phishing-style attack: if the
legitimate owner is tricked into interacting with a malicious contract
(for example, by calling one of its functions, or simply sending it a
transaction), that malicious contract can call into the target contract
on the owner's behalf. `tx.origin` still resolves to the real owner's
address — because they did, technically, originate the transaction —
so the check passes, even though the call didn't come directly from
the owner's intent.

This is a well-known enough pattern that it appears as a standard
teaching example in security training (notably Ethernaut's "Telephone"
challenge), rather than being tied to one specific incident. The fix is
simple: always use `msg.sender` for authorization checks, never
`tx.origin`.