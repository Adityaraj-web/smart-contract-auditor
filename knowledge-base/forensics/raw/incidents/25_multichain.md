---
protocol: Multichain
date: 2023-07-06
attack_type: bridge_cross_chain_exploit, access_control_failure
chain: Ethereum, Fantom, Moonriver, Dogechain
funds_lost_usd: 130000000
source: Chainalysis, CoinDesk, DL News (see references below)
---

## Summary
Multichain, once one of the largest cross-chain bridge protocols with over $1 billion in locked assets, saw approximately $130 million move out of its bridge contracts under unexplained circumstances, shortly before the company revealed that its CEO — who alone held the credentials controlling the bridge's supposedly decentralized custody system — had been detained by Chinese police weeks earlier.

## What Happened
Multichain secured its bridge funds using a multi-party computation (MPC) system, a cryptographic scheme that splits a private key into shares distributed across multiple parties, intended to function similarly to a multisignature wallet so that no single party could unilaterally move funds. In practice, despite this design, all of the MPC key shares and the infrastructure to use them were controlled solely by the company's CEO, known publicly only as Zhaojun. In late May 2023, Multichain began experiencing unexplained technical problems, and the team eventually revealed they had lost contact with Zhaojun. On July 6, 2023, roughly $130 million flowed out of Multichain's bridge contracts on Fantom, Moonriver, and Dogechain to unfamiliar addresses, with the largest share drained from the Fantom bridge specifically. Days later, Multichain confirmed that Chinese police had detained Zhaojun in May, confiscating his computers, phones, hardware wallets, and mnemonic phrases, and that his sister — who had briefly helped operate the system afterward — had also since been detained. The company was never able to definitively establish whether the fund movements were carried out by Zhaojun himself under duress, by Chinese authorities directly, or by an unrelated third party who gained access once the CEO's credentials were compromised.

## Root Cause
A bridge secured by a scheme marketed as decentralized (multi-party computation) that was, in actual operational practice, controlled entirely by a single individual — meaning the true security of over a billion dollars in bridged assets rested on the personal safety, jurisdiction, and continued availability of one person, rather than on any genuinely distributed set of independent key holders.

## Why It Matters
Multichain is an essential and unusual addition to the bridge category because, unlike Ronin's forgotten permission or Harmony's compromised keys, its root cause was a fundamental mismatch between a protocol's advertised security model and its actual operational reality — and because the exact mechanism of fund loss (hack, coerced insider action, or state seizure) may never be conclusively resolved. This is a genuinely important edge case for a forensics tool to recognize: not every large fund loss has a cleanly identifiable single "attacker," and forensics analysis of a bridge or custody failure should always independently verify whether a system's claimed decentralization (MPC, multisig, or otherwise) matches how it is actually operated in practice, since the two can diverge without ever being visible on-chain until something goes wrong.