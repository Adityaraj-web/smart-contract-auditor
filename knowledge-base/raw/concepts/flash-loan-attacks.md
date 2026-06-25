---
category: flash-loan-attacks
source_type: concept
title: Flash Loan Attack Pattern
source_url: https://github.com/trailofbits/publications
---

A flash loan lets a borrower take out an uncollateralized loan of
essentially any size, on the condition that it's borrowed and fully
repaid within the same transaction — if repayment doesn't happen by the
end of that transaction, the entire transaction, loan included, reverts
as if it never occurred. This is a legitimate and useful DeFi primitive
on its own, used for things like arbitrage and collateral swaps.

It becomes an attack tool when combined with another underlying
weakness — most commonly price oracle manipulation, but also
governance vote manipulation or exploiting reentrancy — because it
removes the normal capital constraint an attacker would otherwise face.
Without a flash loan, manipulating a price or vote outcome meaningfully
might require capital the attacker doesn't have. With one, an attacker
can temporarily command a sum far larger than their actual holdings,
use it to distort some on-chain condition, exploit a victim contract
that trusts that condition, and repay the loan, all atomically and risk
-free if the attack succeeds, with the only cost on failure being gas.

The flash loan itself usually isn't the vulnerability — it's an
amplifier. The actual fix is closing whatever underlying weakness
(typically oracle design) the borrowed capital is being used to exploit.