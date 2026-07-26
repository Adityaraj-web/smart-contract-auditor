---
protocol: Platypus Finance
date: 2023-02-16
attack_type: logic_error, flash_loan_enabled
chain: Avalanche
funds_lost_usd: 8500000
source: Immunefi, CoinDesk, BlockApex (see references below)
---

## Summary
Platypus Finance, a stablecoin-focused decentralized exchange on Avalanche, lost approximately $8.5 million after an attacker discovered that its emergency withdrawal function never actually verified that a user's outstanding debt had been repaid before releasing their deposited collateral.

## What Happened
Platypus allowed users to deposit liquidity tokens as collateral and borrow its native stablecoin, USP, against that collateral through its MasterPlatypusV4 contract. The contract included an "emergencyWithdraw" function, intended as a safety valve letting depositors retrieve their tokens in unusual situations. The attacker took a large flash loan, deposited it as collateral, and borrowed a substantial amount of USP against it — well within the platform's allowed borrowing limit. The attacker then called the emergency withdrawal function. Critically, this function's only safety check confirmed that the user's existing debt did not exceed their borrowing limit — a check that remained satisfied regardless of whether the collateral backing that debt was still present. The function let the attacker withdraw their full original collateral deposit while their USP debt remained entirely outstanding and unpaid, effectively creating profit out of debt the protocol could never actually collect. The attacker repaid the flash loan and kept the borrowed USP, which they then swapped for real, redeemable stablecoins from Platypus's own liquidity pools.

## Root Cause
A logic error involving an incomplete safety check: the emergency withdrawal function verified that debt remained within an allowed limit, but never verified the far more basic condition that collateral could not be withdrawn while any debt against it remained outstanding — an assumption so fundamental to how lending is supposed to work that it was apparently never explicitly tested for the emergency-path function specifically.

## Why It Matters
Platypus Finance is a valuable addition to the logic-error category precisely because of its simplicity relative to KyberSwap's precision rounding or Cetus's overflow-check math: this was a single, conceptually basic missing check — "don't let collateral leave while debt remains" — in a function explicitly labeled for emergency use, a part of the codebase that may receive less rigorous testing than a protocol's primary user-facing paths. This is a useful pattern for forensics analysis to flag: functions named "emergency," "admin," or "backup" often bypass some of the same invariant checks enforced elsewhere in a contract, and deserve the same scrutiny as primary application logic rather than being assumed safe because they are rarely used.