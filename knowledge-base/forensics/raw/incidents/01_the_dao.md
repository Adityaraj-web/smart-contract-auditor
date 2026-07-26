---
protocol: The DAO
date: 2016-06-17
attack_type: reentrancy
chain: Ethereum
funds_lost_usd: 60000000
source: The Block, Metana, Hacken (see references below)
---

## Summary
The DAO, an early Ethereum-based investment fund that had raised roughly $150 million from over 11,000 investors, was drained of about 3.6 million ETH (around $60 million at the time) through a reentrancy bug in its withdrawal logic. The incident remains the most consequential smart contract exploit in Ethereum's history, directly leading to the Ethereum/Ethereum Classic chain split.

## What Happened
The attacker deployed a malicious contract whose fallback function called back into The DAO's withdrawal function before the first withdrawal had finished updating the contract's internal balance record. Because the balance check happened after the funds were sent rather than before, each recursive call saw the original, unreduced balance and paid out again. This loop continued, repeatedly draining ether into a "child DAO" until a large portion of the fund's holdings had been diverted. The attack was so significant relative to total ETH supply in circulation at the time that it prompted the Ethereum community to execute a hard fork, rolling back the chain to a pre-attack state — a decision controversial enough that a portion of the community rejected it, continuing the original chain as Ethereum Classic.

## Root Cause
A classic reentrancy vulnerability: external calls (sending ether to the withdrawer) were made before the contract's internal state (the withdrawer's balance) was updated. This violates what later became known as the checks-effects-interactions pattern — state should be finalized before any external call is made, precisely because an external call can call back into the calling contract before it returns.

## Why It Matters
This is the incident that put reentrancy on the map as the canonical smart contract vulnerability class. Virtually every static analysis tool (including Slither) checks for this pattern today, and the checks-effects-interactions pattern along with reentrancy guards exist largely because of the lessons from this single incident. Any forensics case involving unexpected recursive fund drains from a withdrawal-style function should be checked against this pattern first.