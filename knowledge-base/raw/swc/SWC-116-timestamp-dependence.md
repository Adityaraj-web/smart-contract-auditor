---
category: timestamp-dependence
swc_id: SWC-116
source_type: swc
title: Block Timestamp Dependence
source_url: https://swcregistry.io/docs/SWC-116
---

Solidity contracts can read `block.timestamp` as a source of "current
time." This value is set by whoever produces the block — historically
miners under proof-of-work, validators under proof-of-stake — and while
network rules constrain it to be reasonably close to real time and
greater than the previous block's timestamp, the block producer still
has some limited discretion over the exact value within that window.

This becomes a vulnerability when contract logic treats block.timestamp
as something an attacker can't influence at all, particularly when it's
used as a source of "randomness" (for example, deriving a winning
number from the timestamp's last few digits) or as a precise deadline
boundary where being off by even a small, producer-controlled margin
changes the outcome. A block producer who is also a participant in the
contract has a direct incentive to nudge the timestamp within their
allowed range to favor themselves.

Mitigation: never use block.timestamp as a randomness source (use a
verifiable randomness solution instead), and where timestamps are used
for deadlines, design the logic so a small, bounded manipulation window
doesn't materially change who benefits.