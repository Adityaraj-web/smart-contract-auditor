---
protocol: Cover Protocol
date: 2020-12-28
attack_type: logic_error
chain: Ethereum
funds_lost_usd: 5000000
source: Mudit Gupta, CipherTrace, Cointelegraph (see references below)
---

## Summary
Cover Protocol, a decentralized insurance platform, suffered an infinite token minting exploit after an attacker discovered that its liquidity mining contract cached a key value in memory for gas efficiency but never updated that cached copy after the underlying stored value changed, letting the attacker mint tens of trillions of tokens from what should have been a tightly bounded rewards calculation.

## What Happened
Cover's Blacksmith contract rewarded liquidity providers with COVER tokens based on how long they had staked funds, tracking a cumulative rewards-per-token value that increased over time. To save on gas costs, the contract read this value from storage once into a temporary memory variable at the start of a function, then used that cached copy for later calculations within the same function — a common and normally safe gas-optimization pattern. The bug was that a separate part of the same function updated the actual value in storage partway through execution, but the earlier memory copy was never refreshed to reflect that update. The attacker discovered that by depositing a very small amount of tokens, then immediately withdrawing almost all of it (leaving a tiny residual balance), followed by a second large deposit, the resulting math produced a directly-computed reward payout that was wildly disproportionate to any real, legitimate staking activity — because the "before" and "after" values the calculation relied on had grown artificially far apart due to the stale cached figure. Repeating this pattern let the attacker mint tens of trillions of COVER tokens, some of which were sold for real assets before the exploit was noticed and mining access was restricted.

## Root Cause
A logic error rooted in a classic memory-versus-storage caching mistake: a value was read once for gas efficiency and then treated as still accurate later in the same function, even though the authoritative on-chain value had since changed. The gas-optimization pattern itself is common and often safe, but it becomes dangerous whenever the same function also modifies the value being cached without re-reading it afterward.

## Why It Matters
Cover Protocol is a valuable final addition to this corpus because, unlike Cetus's cross-language shared-library overflow or KyberSwap's tick-boundary precision loss, this bug is conceptually simple and predates most of the more sophisticated exploits in this collection by several years — yet it produced one of the cleanest examples of the "stale cached value" class of bug, a pattern that continues to reappear in various forms across DeFi. It is a useful baseline case for a forensics tool to compare against: not every high-impact exploit requires an attacker to understand advanced mathematics or novel cryptography; sometimes a fundamental and well-understood category of bug, memory-storage desynchronization, is sufficient on its own when it goes unnoticed through review.