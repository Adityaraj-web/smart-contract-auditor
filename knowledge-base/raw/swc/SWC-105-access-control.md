---
category: access-control
swc_id: SWC-105
source_type: swc
title: Unprotected Functions and Access Control
source_url: https://swcregistry.io/docs/SWC-105
---

Access control vulnerabilities occur when a function that should only
be callable by a specific role — an owner, an admin, a particular
contract — is missing the check that enforces that restriction, or has
a check that's incorrect or bypassable. Common causes: a function meant
to be internal is left public, a modifier like `onlyOwner` is forgotten
on a sensitive function (changing ownership, withdrawing funds, pausing
the contract), or the check exists but compares against the wrong
value.

Standard mitigation is consistent use of access-control modifiers
(OpenZeppelin's `Ownable` or `AccessControl` contracts are the common
choice) applied to every state-changing function that should be
restricted, plus explicit tests confirming unauthorized callers revert.