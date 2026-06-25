---
category: price-oracle-manipulation
source_type: concept
title: Price Oracle Manipulation
source_url: https://github.com/trailofbits/publications
---

DeFi protocols frequently need an on-chain price for an asset — to
determine collateral value, calculate swap rates, or decide if a loan
is undercollateralized. Many protocols source this price directly from
another on-chain source, commonly the token reserve ratio of a
decentralized exchange liquidity pool, rather than from an external,
manipulation-resistant feed.

The vulnerability: a liquidity pool's reported price is just a function
of its current reserves, and reserves can be temporarily and
dramatically shifted within a single transaction by a large enough
trade — particularly when combined with a flash loan providing capital
far beyond what the attacker actually owns. An attacker can borrow a
huge sum, execute a trade that skews the pool's reserves and therefore
its reported price, interact with a victim protocol that reads that
distorted price as if it were legitimate, then reverse the trade and
repay the loan, all within the same atomic transaction.

Mitigation: use time-weighted average prices (TWAPs) computed over a
window rather than a single instantaneous reading, or use independent,
manipulation-resistant external oracle networks rather than deriving
price directly from a single pool's spot reserves.