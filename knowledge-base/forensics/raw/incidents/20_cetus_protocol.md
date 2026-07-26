---
protocol: Cetus Protocol
date: 2025-05-22
attack_type: logic_error, flash_loan_enabled
chain: Sui
funds_lost_usd: 223000000
source: Halborn, SlowMist, Cyfrin (see references below)
---

## Summary
Cetus Protocol, the largest decentralized exchange on the Sui blockchain, lost approximately $223 million after an attacker exploited a flawed overflow check in a shared math library, allowing them to deposit a single token unit and receive liquidity worth millions in return.

## What Happened
Cetus used a concentrated liquidity design requiring precise math to calculate how many tokens a user must deposit to mint a given amount of liquidity within a specific price range. A helper function called `checked_shlw` was meant to detect when a mathematical operation (a left bit-shift used in this calculation) would overflow — producing a result too large for its numeric type to represent safely. The function's overflow check compared the input against the wrong threshold value: instead of correctly rejecting any value at or above the true overflow boundary, it only rejected a much narrower range near the very top of the number space, leaving a wide gap where genuinely overflow-triggering values would still pass the check as "safe." The attacker took a flash loan, opened a liquidity position within a deliberately tiny price range, and selected a specific liquidity parameter that passed the flawed check while still causing an overflow deeper in the calculation. This overflow caused the required token deposit to be calculated as essentially zero, letting the attacker mint enormous liquidity credit for a single token unit, withdraw the equivalent real value, repay the flash loan, and repeat the process across many pools within about fifteen minutes.

## Root Cause
A logic error in a shared arithmetic utility library: an overflow-detection check used the wrong numerical boundary, meaning it validated against an incorrect assumption about which values were actually safe from overflow. Because this flawed function was a small, reused piece of general-purpose math code rather than something specific to any one trading pair, every pool relying on it inherited the same vulnerability simultaneously.

## Why It Matters
Cetus is an important, very recent addition to the logic-error category because the flaw lived in a shared third-party library rather than in Cetus's own core trading logic — multiple other protocols on the same blockchain used the same vulnerable math primitive and had to rush emergency patches once the root cause became public. This illustrates a forensics pattern worth flagging explicitly: when an exploited function is part of a widely-reused library rather than protocol-specific code, the same root cause is likely to affect other protocols too, and identifying the library-level flaw (not just the single incident) is often the more valuable finding.