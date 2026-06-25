---
category: integer-overflow-underflow
swc_id: SWC-101
source_type: swc
title: Integer Overflow and Underflow
source_url: https://swcregistry.io/docs/SWC-101
---

Solidity integers have a fixed bit width (uint8, uint256, etc.), and
prior to Solidity 0.8.0 arithmetic on them silently wrapped around on
overflow or underflow instead of raising an error. A uint8 holding 255
that gets incremented by 1 wraps to 0. A uint256 set to 0 that gets
decremented by 1 wraps to the maximum possible uint256 value, an
astronomically large number, instead of going negative or reverting.

This becomes a security issue whenever a contract uses unchecked
arithmetic on values that influence balances, allowances, or access
control — for example, subtracting a withdrawal amount from a balance
without first checking the balance is large enough lets an attacker
underflow their balance to a huge number and withdraw far more than
they ever deposited.

Before 0.8.0, the standard mitigation was OpenZeppelin's SafeMath
library, which wrapped arithmetic operations in functions that revert
on overflow/underflow instead of wrapping silently. As of Solidity
0.8.0, this checking is built into the language by default — addition,
subtraction, and multiplication all revert on overflow/underflow unless
the code is explicitly wrapped in an `unchecked { ... }` block, which a
developer would use deliberately when they've already proven the
overflow can't happen and want the gas savings.