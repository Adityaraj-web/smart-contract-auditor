---
protocol: Cream Finance
date: 2021-10-27
attack_type: oracle_manipulation, flash_loan_enabled
chain: Ethereum
funds_lost_usd: 130000000
source: Halborn, Immunefi, ImmuneBytes (see references below)
---

## Summary
Cream Finance, a lending protocol forked from Compound, lost approximately $130 million — its third major exploit within the same year — after an attacker manipulated the exchange rate of a yield-bearing token (yUSD) that Cream's own price oracle trusted directly, allowing the attacker to borrow far more than their real collateral was worth.

## What Happened
Cream allowed users to deposit yUSD, a token representing a share of a Yearn Finance vault, as loan collateral. Cream's oracle calculated yUSD's price based on the ratio between the vault's total underlying assets and the number of yUSD tokens in circulation — a value called "price per share." The attacker used a combination of flash loans from Aave and a flash mint from MakerDAO to construct a large, layered position across two coordinated smart contracts, and then sent additional funds directly into the underlying Yearn vault contract using a plain token transfer rather than the vault's normal deposit function. Because this direct transfer bypassed the vault's standard accounting logic, it inflated the vault's recorded assets without minting any corresponding new yUSD shares — artificially doubling the reported price per share. Cream's oracle picked up this manipulated price, valuing the attacker's yUSD collateral roughly twice as high as it actually was. Using this inflated collateral, the attacker borrowed and drained Cream's entire available liquidity in that lending market before repaying the original flash loans, walking away with the difference.

## Root Cause
An oracle relying on a manipulable, directly-computed on-chain value (the vault's asset-to-share ratio) rather than a time-resistant or externally-validated price source, combined with a vault design that allowed its internal accounting to be skewed by a raw token transfer that bypassed its normal deposit path entirely.

## Why It Matters
Cream Finance is a strong second example of oracle manipulation distinct from Mango Markets: rather than manipulating an external market price through wash trading, this attack manipulated an internal, on-chain accounting ratio directly, using a quirk in how the underlying vault contract computed its own asset valuation. It reinforces a pattern worth flagging in forensics reports: any oracle that derives price from a ratio of on-chain balances is only as trustworthy as the assumption that those balances can only change through the contract's intended entry points — an assumption a plain token transfer can quietly violate.