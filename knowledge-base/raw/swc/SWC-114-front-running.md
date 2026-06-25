---
category: front-running
swc_id: SWC-114
source_type: swc
title: Transaction Order Dependence
source_url: https://swcregistry.io/docs/SWC-114
---

All pending Ethereum transactions sit visibly in a public waiting area
called the mempool before a miner or validator includes them in a
block. Anyone watching the mempool can see a transaction's full
details — including, for example, that it's about to execute a
profitable trade or claim a reward — and submit their own transaction
offering a higher gas price (or use other ordering mechanisms) to get
included first, exploiting that visible information before the
original transaction confirms.

This is broadly called front-running, and it's an inherent property of
how public blockchains order transactions, not a bug specific to any
one contract. It becomes a contract-level vulnerability when contract
logic exposes value to whoever transacts first — a classic example is
a contract paying a reward to whoever submits the correct answer to a
puzzle first, where an attacker simply copies a pending correct answer
from the mempool and resubmits it with higher gas, stealing the reward
intended for the original solver.

Mitigations include commit-reveal schemes (submitting a hashed
commitment first, revealing the actual value later), and architectural
choices that don't expose exploitable ordering value in the first
place.