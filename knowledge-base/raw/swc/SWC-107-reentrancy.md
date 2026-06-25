---
category: reentrancy
swc_id: SWC-107
source_type: swc
title: Reentrancy
source_url: https://swcregistry.io/docs/SWC-107
---

Reentrancy occurs when a contract makes an external call to another
contract before finishing its own state updates, and that external call
gives the called party a chance to call back into the original contract
before the first invocation has completed. If the original function
relies on state that hasn't yet been updated, the re-entered call can
repeat actions — most commonly draining funds — multiple times against
state that should have blocked the second pass.

The classic trigger is sending Ether via a low-level call such as
`.call{value: ...}("")` to an address that turns out to be a contract
with a fallback or receive function written to immediately call back
into the original function, before that function has decremented the
caller's balance.

Standard mitigations: follow the checks-effects-interactions pattern
(update all state before making any external call), use a reentrancy
guard (a mutex-style modifier blocking re-entry while a function is
already executing), and be cautious relying on gas stipend limits from
`transfer`/`send` alone — gas costs aren't fixed long-term, and a
contract can still re-enter through other unprotected functions.