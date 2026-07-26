---
protocol: Audius
date: 2022-07-23
attack_type: governance_attack, logic_error
chain: Ethereum
funds_lost_usd: 6000000
source: Audius post-mortem, CryptoSlate, Three Sigma (see references below)
---

## Summary
Audius, a decentralized music streaming platform, lost roughly $6 million from its community treasury after an attacker exploited a storage layout collision introduced during a prior contract upgrade, allowing them to re-initialize the platform's governance contract and appoint themselves as its administrator.

## What Happened
Audius's governance system used an upgradeable proxy pattern, where a lightweight proxy contract stores data while delegating its logic to a separate implementation contract. At some point, developers added a new variable, proxyAdmin, to the proxy contract's own storage, intending it to hold an administrator address. They did not realize that this new variable occupied the same storage slot the implementation contract used for its "initialized" flag — the value the contract checked to determine whether its one-time setup function had already been run. Because the proxyAdmin address happened to be a non-zero value, the implementation contract's logic read that slot and concluded, incorrectly, that it had never been initialized. This let the attacker call the contract's initialize function again, long after deployment, appointing themselves as the governance system's controlling address. From there, they submitted and passed a governance proposal — one that any genuine governance process would never have approved — transferring the entire community treasury to their own wallet.

## Root Cause
A logic error in upgradeable contract design, functioning as a governance attack: a storage collision between a newly added proxy variable and an existing implementation variable meant two conceptually unrelated pieces of data ended up sharing the same storage location, causing the contract to misread its own initialization state and permit a re-initialization that should have been permanently impossible.

## Why It Matters
Audius is an important third governance example because it required no flash loan, no large capital position, and no social engineering of voters at all — the attacker simply became the sole legitimate-looking administrator of the governance system itself, at which point "passing a vote" was a formality rather than a genuine contest. This contrasts sharply with both Beanstalk (temporary capital-based vote-buying) and Tornado Cash (a deceptive but honestly-voted-on proposal): here, the attacker bypassed the concept of a vote entirely by exploiting a storage-layout mistake left over from a routine, seemingly unrelated code change. It underscores that any upgradeable governance contract's storage layout across every version needs careful auditing whenever new variables are added, since the collision itself may have nothing to do with governance logic on its face.