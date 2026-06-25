---
category: unchecked-call-return-value
swc_id: SWC-104
source_type: swc
title: Unchecked Call Return Value
source_url: https://swcregistry.io/docs/SWC-104
---

Low-level calls in Solidity — `.call()`, `.send()`, `.delegatecall()`,
`.staticcall()` — do not automatically revert the transaction if the
call fails. Instead, they return a boolean indicating success or
failure, leaving it entirely up to the calling code to check that value.
If the return value is ignored, a failed call is silently treated as
though nothing went wrong, and execution simply continues.

This differs from a normal Solidity function call or `.transfer()`
(prior to certain gas-related changes), which reverts automatically on
failure. With `.send()` in particular, a common but dangerous pattern
is writing `recipient.send(amount);` with no surrounding `if` check —
if the recipient is a contract that rejects the transfer (for example,
because its fallback function runs out of the limited gas stipend
`send` provides), the ETH is never delivered, no error is raised, and
the contract's internal state can end up inconsistent with what
actually happened on-chain.

The standard mitigation is to always check the return value explicitly
— `require(success, "transfer failed")` — or use the modern pattern of
`.call{value: amount}("")` combined with an explicit success check,
which is now generally preferred over `.send()`/`.transfer()` because
it doesn't impose a fixed, easily-outdated gas stipend.