---
category: default-visibility
swc_id: SWC-100
source_type: swc
title: Function Default Visibility
source_url: https://swcregistry.io/docs/SWC-100
---

Prior to Solidity 0.4.22, a function with no explicit visibility
keyword defaulted to `public`, meaning any address could call it
directly — not just other functions within the same contract, and not
just an intended set of callers. A developer who simply forgot to mark
a sensitive function as `private` or `internal` would unknowingly leave
it open to anyone.

This was especially dangerous around constructor-like setup functions
in versions of Solidity where a constructor had to be named identically
to the contract itself rather than using the `constructor` keyword —
if the contract was ever renamed during development and the function
wasn't renamed to match, it silently stopped being treated as a
constructor at all and became an ordinary public function instead,
callable by anyone, at any time, not just once at deployment.

Solidity 0.4.22 introduced the `constructor` keyword specifically to
remove the name-matching fragility, and later versions require explicit
visibility on every function, eliminating the implicit-public default
entirely. The pattern remains relevant when reviewing any older,
pre-0.4.22 contract.