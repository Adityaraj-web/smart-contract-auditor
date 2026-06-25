---
category: dos-unbounded-gas
swc_id: SWC-128
source_type: swc
title: Denial of Service via Block Gas Limit
source_url: https://swcregistry.io/docs/SWC-128
---

Every Ethereum block has a maximum amount of gas all its transactions
combined can consume. A function that loops over a data structure whose
size can grow without bound — most commonly an array of all users,
depositors, or participants — risks eventually requiring more gas to
execute fully than the block gas limit allows, once that structure
grows large enough.

Once that point is reached, the function becomes permanently
uncallable: any transaction invoking it will always exceed the gas
limit and revert, regardless of how much gas the caller is willing to
spend, because no single block can ever fit it. If that function was
the only path to, for example, distributing funds back to all
participants, those funds can become permanently stuck with no
remaining mechanism to retrieve them — the contract logic itself, not
just one transaction, is dead.

Mitigation: avoid unbounded loops over growable on-chain data entirely.
Use a "pull" pattern instead — let each user withdraw their own funds
individually in their own transaction — rather than a "push" pattern
that pays everyone out in a single loop.