---
protocol: Tornado Cash
date: 2023-05-20
attack_type: governance_attack
chain: Ethereum
funds_lost_usd: 2173500
source: Halborn, CoinDesk, Cointelegraph (see references below)
---

## Summary
Tornado Cash, the privacy-focused Ethereum mixing protocol, had its governance DAO effectively taken over after an attacker submitted a proposal that appeared nearly identical to a previously approved one, but secretly contained code allowing the attacker to grant themselves an overwhelming majority of voting power once the proposal passed.

## What Happened
Tornado Cash's governance system allowed token holders to vote on proposals that, once approved, executed arbitrary code via delegate call to update the protocol. The attacker submitted a proposal whose visible logic closely mirrored an earlier, legitimate proposal that the community had already reviewed and trusted — but the new proposal contained an additional, hidden function. Voters, relying on the proposal's resemblance to prior approved work, voted it through the normal governance process. Once passed, the attacker invoked this hidden function (an "emergency stop" mechanism) to self-destruct the proposal's own contract and redeploy different, malicious code to that same address — a capability delegate-call-based governance systems can allow if not carefully restricted. The newly substituted code granted the attacker's own addresses a combined 1.2 million governance votes, dwarfing the roughly 700,000 votes held by all legitimate token holders combined. With total control of the DAO, the attacker withdrew locked governance tokens and liquidated them for a profit of approximately $2.17 million.

## Root Cause
A governance design flaw distinct from a flash-loan-based attack: there was no guaranteed correspondence between what a proposal's code appeared to do (based on resemblance to a trusted prior proposal) and what it actually did once executed. The ability to self-destruct and redeploy new logic at the same address, combined with insufficient scrutiny of a proposal that looked routine, let a completely different, malicious implementation slip through a normal, un-rushed voting period.

## Why It Matters
Tornado Cash is an essential second governance example alongside Beanstalk because it demonstrates governance can be subverted with no flash loan and no urgency at all — the attack unfolded over the DAO's normal voting timeline, relying purely on social trust in a proposal's apparent similarity to past work rather than on any economic or capital-based exploit. This tells a forensics tool that "governance attack" should not be conflated with "flash-loan-enabled" as if they always co-occur; the underlying vulnerability here was in code-review practices and delegate-call safety, not in how quickly voting power could be acquired.