# Engineering Notes: Forensics Extension — Post-Incident On-Chain Analysis

The forensics extension adds a second, independent mode to the auditor: instead of analyzing a contract *before* deployment, it takes a transaction hash for an incident that has *already happened* and generates a structured post-mortem — historical pattern matching against 31 real-world exploits, a decoded event timeline, and its own separate on-chain attestation trail.

This doc is the detailed companion to the summary in the main [`README.md`](../README.md).

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution / Pipeline](#solution--pipeline)
- [Attack Taxonomy](#attack-taxonomy)
- [Architecture](#architecture)
- [On-Chain Attestation & Gating Logic](#on-chain-attestation--gating-logic)
- [Key Engineering Decisions](#key-engineering-decisions)
- [Real Bugs Found & Fixed](#real-bugs-found--fixed)
- [Explorer UI](#explorer-ui)
- [Setup](#setup)
- [Usage Walkthrough](#usage-walkthrough)
- [Known Limitations](#known-limitations)

---

## Problem Statement

Post-incident analysis of DeFi exploits today is almost entirely manual: someone reads Etherscan, cross-references it against writeups of past hacks they happen to remember, and publishes a Twitter thread or a blog post. There's no structured, repeatable way to ask "does this transaction resemble a known attack pattern, and which one" — and no way to make that analysis independently verifiable after the fact, the way the pre-deployment audit side already does with attestation.

## Solution / Pipeline

1. **Ingest** the transaction from Etherscan — the main transaction, its internal call sequence, and its full log sequence, decoding events via verified ABIs where available and known signatures otherwise.
2. **Retrieve** the most similar historical incidents from a dedicated ChromaDB collection (`historical_exploits`) built from 31 curated exploit write-ups, kept entirely separate from the audit side's vulnerability corpus.
3. **Score** the transaction against a fixed 9-category attack taxonomy, combining retrieval similarity with any direct on-chain signals.
4. **Generate** a narrative (summary, timeline, root cause, why-it-matters, and a per-category assessment) via the same local Ollama model used for audits — then validate it, checking for fabricated evidence and bare protocol-name conflation before it's ever shown as trustworthy.
5. **Attest** the report on-chain, gated on that validation passing, via a dedicated `ForensicsAttestationRegistry` contract.

## Attack Taxonomy

A fixed, ordered list of 9 categories, encoded as a `uint16` bitmask on-chain (since a real incident can — and often does — match more than one category simultaneously, unlike the audit side's single overall risk level):

```
0. reentrancy
1. oracle_manipulation
2. flash_loan_enabled
3. access_control_failure
4. logic_error
5. front_running_mev
6. signature_replay_verification_bypass
7. bridge_cross_chain_exploit
8. governance_attack
```

## Architecture

```
                         ┌─────────────────────┐
                         │   User (Browser)      │
                         └──────────┬────────────┘
                                    │
                         ┌──────────▼────────────┐
                         │   Next.js Frontend      │
                         │  /forensics (input)     │
                         │  /forensics/[txHash]    │
                         │  (report + attest)      │
                         └──────────┬────────────┘
                                    │ REST (local only)
                         ┌──────────▼────────────┐
                         │   FastAPI Backend       │
                         │  /forensics/generate    │
                         │  /forensics/attest      │
                         └──┬───────┬───────┬──────┘
                            │       │       │
              ┌─────────────┘   ┌───┘   ┌───┘
              ▼                 ▼       ▼
     ┌────────────────┐ ┌──────────┐ ┌─────────────┐
     │ Etherscan API   │ │ Chroma    │ │ Ollama       │
     │ (tx + logs +    │ │ historical│ │ (local LLM,  │
     │ internal calls) │ │ _exploits │ │ llama3.2:3b) │
     └────────────────┘ └──────────┘ └─────────────┘
                            │
                            ▼
                  ┌──────────────────────┐
                  │  Forensics Report      │
                  │  (timeline, pattern    │
                  │  scores, narrative,    │
                  │  quality flags)        │
                  └─────────┬─────────────┘
                            │ narrative_validation_failed?
                            │  no → gated attest, exact report
                            ▼
                 ┌──────────────────────┐
                 │  Supabase              │
                 │  forensics_attestations│
                 └──────────┬─────────────┘
                            │
                            ▼
                 ┌───────────────────────────┐
                 │  Sepolia Testnet            │
                 │  ForensicsAttestationRegistry│
                 └───────────────────────────┘
```

## On-Chain Attestation & Gating Logic

The `ForensicsAttestationRegistry` contract records, per transaction hash: the chain ID, attestor, timestamp, a hash of the full report, the category bitmask, and a single `hasConflationFlags` boolean. All gating is enforced in Python before submission — the contract simply records what's already been decided:

- **`narrative_validation_failed = true` → hard block.** This is treated as a correctness failure, not a severity gradient, and is never attestable.
- **Quality flags (protocol conflation or fabricated evidence) → warn, but still attest.** These are documented heuristics with known false positives/negatives; blocking on them would deny legitimate reports. Both checks are OR'd into the single on-chain `hasConflationFlags` bit to avoid a contract redeploy — full detail (which check fired, on which field) remains visible in the API response and the report itself, only the single on-chain bit loses the distinction between the two.

## Key Engineering Decisions

**Attest exactly what was reviewed, not what gets regenerated.** `/forensics/attest` accepts an already-generated report and attests it as-is, rather than silently re-running the LLM pipeline. This was a deliberate fix (see bug #5 below) once it became clear the narrative isn't deterministic run-to-run — regenerating at attest time could otherwise put a different report on-chain than the one a user actually reviewed, undermining the entire point of attestation.

**Category bitmask, not a single label.** Unlike the audit side's single `overall_risk`, a real incident can simultaneously be, say, a flash-loan-enabled governance attack — both tags legitimately apply. The 9-category order is fixed and treated as a permanent on-chain contract, not an implementation detail that can silently change.

**Separate phase counter, separate corpus, separate registry — same repo.** Rather than spinning up a new project, the forensics extension shares the base auditor's repo, environment, and LLM, but keeps its ChromaDB collection, contract, Supabase table, and phase numbering independent, so the two modes can evolve without risk of cross-contamination.

**Dual-invocation-safe imports.** Several forensics modules can be run either as part of the FastAPI app (`backend.X` package imports) or standalone for smoketesting (`cd backend; python X.py`, flat imports). A try/except import fallback pattern supports both without duplicating any module that holds meaningful state (notably `retrieval.py`'s ChromaDB client) — see bug #3 below for why that mattered.

## Real Bugs Found & Fixed

Documented here in the same spirit as the audit side's own known limitations — these were caught through live testing against a real Sepolia transaction, not hypothesized in advance.

1. **Gas limit too low.** The forensics attestation call initially copied the audit side's hardcoded gas limit. It reverted on Sepolia with an out-of-gas error, since `ForensicsAttestation`'s struct has more fields than the audit side's. Fixed by estimating gas dynamically (`estimate_gas()` + a 30% buffer) instead of guessing a new fixed number.
2. **Receipt-wait timeout too short.** A real Sepolia confirmation, under low ambient gas prices, took longer than an initial 120-second timeout, even though it eventually mined successfully. Fixed by raising the timeout to 300 seconds, plus writing a one-off reconciliation script to backfill Supabase for the one attestation that had already confirmed late.
3. **Import module duplication risk.** A forensics module using flat sibling imports, if loaded through the FastAPI app's package-style imports, would have caused Python to load `retrieval.py` a second time under a different module name — creating a second, separate ChromaDB client against the same on-disk path in one process, with a real risk of "database is locked" errors. Caught by reasoning through the import graph before it caused a live failure, and fixed with a try/except import fallback pattern.
4. **LLM fabricating "direct evidence" claims.** A sparse test transaction with zero decoded logs still produced category assessments tagged as directly observed evidence — but the LLM was actually describing a retrieved historical incident's specifics as if it had seen them in the analyzed transaction itself. This is a stricter failure than simple protocol-name conflation: it asserts a false fact about the transaction's own evidence, not just borrows a name. Fixed by cross-checking every "direct evidence" claim in the narrative against that category's actual detected signals, flagging any mismatch.
5. **Non-deterministic attest-time regeneration.** `/forensics/attest` originally re-ran the full pipeline independently of `/forensics/generate`, rather than reusing whatever the user had already reviewed. Since the LLM narrative isn't deterministic run-to-run, this meant the report a user reviewed in the explorer UI could differ from the one that actually got attested on-chain — silently breaking the core trust guarantee that attestation is supposed to provide. Fixed by having `/forensics/attest` accept an already-generated report directly (validated for matching tx hash, chain, and schema version) and attest it as-is, only falling back to full regeneration for standalone/scripted use where no prior report exists.

## Explorer UI

Two new routes, in the same visual language as the audit side:

- **`/forensics`** — a landing page for entering a transaction hash and chain, which redirects to the report route on submission.
- **`/forensics/[txHash]`** — the report view: a decode summary strip, a quality-flags panel (shown only when flags are present), the full narrative, one expandable card per candidate category with its historical matches, and — if validation passed — an **Attest On-Chain** button.

Because uint256-range token amounts inside decoded log arguments (e.g. transfer amounts, protocol balances) exceed what a JS `number` can represent exactly, the forensics API responses are parsed with `lossless-json` rather than the browser's native `JSON.parse`, converting only the fields that would otherwise silently lose precision into exact strings.

## Setup

Requires a free [Etherscan API key](https://etherscan.io/apis) in addition to the base prerequisites in the main README.

**1. Build the historical exploit corpus:**
```bash
python knowledge-base/forensics-scripts/01_chunk.py
python knowledge-base/forensics-scripts/02_embed_and_store.py
python knowledge-base/forensics-scripts/03_validate.py
```

**2. Deploy the forensics attestation contract:**
```bash
cd hardhat
npx hardhat run scripts/deploy-forensics.js --network sepolia
```
Copy the deployed address into the root `.env`:
```
ETHERSCAN_API_KEY=your_etherscan_api_key
FORENSICS_CONTRACT_ADDRESS=0xYOUR_DEPLOYED_FORENSICS_ADDRESS
```

**3. Create the `forensics_attestations` table in Supabase** (SQL Editor):
```sql
create table forensics_attestations (
    id uuid primary key default gen_random_uuid(),
    tx_hash text unique not null,
    chain text not null,
    chain_id integer not null,
    attestor_address text not null,
    category_bitmask integer not null,
    has_conflation_flags boolean not null,
    report_hash text not null,
    attestation_tx_hash text not null,
    block_number integer not null,
    attested_at timestamptz not null
);
alter table forensics_attestations enable row level security;
```

**4. Install the frontend's big-number-safe JSON parser:**
```bash
cd explorer
npm install lossless-json
```

Visit `http://localhost:3000/forensics` to use it.

## Usage Walkthrough

1. Go to `/forensics` and paste a transaction hash (mainnet or the chain your Etherscan key supports), then click **Generate Report**.
2. The pipeline fetches the transaction, decodes its event logs, retrieves the most similar historical incidents from the exploit corpus, and generates a narrative — this can take a couple of minutes on CPU.
3. The report page shows a decode summary, any protocol-conflation or fabricated-evidence quality flags, the narrative (summary / timeline / root cause / why it matters), and one expandable card per candidate attack category with its historical matches.
4. If the narrative passed validation, an **Attest On-Chain** button appears. Clicking it submits *exactly the report you're looking at* — not a freshly regenerated one — for gated attestation on Sepolia (see bug #5 above for why that distinction matters).
5. Visiting a `/forensics/[txHash]` link directly (e.g. a shared URL) re-runs the pipeline fresh rather than reading a cached report — see [Known Limitations](#known-limitations) below.

## Known Limitations

- `/forensics/[txHash]` re-runs the full pipeline on every visit rather than reading a cached report — neither the on-chain record nor the Supabase table stores the full report JSON, only its hash and category bitmask. This means a shared report link, or a page refresh, can show a slightly different narrative (different quality-flag count, different citations) than an earlier visit, even though nothing about the transaction itself has changed. This mirrors an existing limitation on the audit side, where `Attestation` records similarly don't store the full report.
- The `hasConflationFlags` on-chain bit conflates two distinct checks (protocol conflation and fabricated evidence) into one boolean to avoid a contract redeploy; the full, separated detail remains available in the report and API response.
- `pattern_scores[category].direct_signals` and the shape of a populated `fabricated_evidence_flags` entry are both based on code inspection rather than a real-world example with actual data in them — every transaction analyzed so far has left both empty. Worth revisiting if a genuinely fabricated-evidence case shows up in practice.
- Etherscan's free-tier rate limits constrain how quickly a freshly-specified transaction can be ingested.