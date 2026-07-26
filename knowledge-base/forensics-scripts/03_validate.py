"""
Runs realistic test queries against the historical_exploits Chroma
collection to validate that retrieval returns chunks tagged with the
correct attack-pattern category.

Queries are phrased like a forensics investigator's description of
on-chain findings, not like a category label — that's how this will
actually get queried in Phase 3, once a transaction trace is turned
into a query string.
"""

from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "historical_exploits"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3

TEST_QUERIES = [
    {
        "query": "a withdrawal function sends funds out and only updates the caller's recorded balance afterward, letting a callback trigger the withdrawal again before the balance is reduced",
        "expected_category": "reentrancy",
    },
    {
        "query": "an attacker uses a large trade on a thinly traded market to temporarily inflate the price a lending protocol reads directly from that pool",
        "expected_category": "oracle_manipulation",
    },
    {
        "query": "borrowed capital that must be repaid within the same transaction is used to briefly acquire an oversized position with no real collateral at risk",
        "expected_category": "flash_loan_enabled",
    },
    {
        "query": "a privileged administrative function meant to be restricted was callable by an address that should never have had that permission",
        "expected_category": "access_control_failure",
    },
    {
        "query": "a safety check inside a rarely used function fails to verify a fundamental invariant that every other function in the contract enforces",
        "expected_category": "logic_error",
    },
    {
        "query": "an automated on-chain actor observes a pending profitable opportunity and inserts its own transaction ahead of it to capture the value first",
        "expected_category": "front_running_mev",
    },
    {
        "query": "a verification step designed to confirm cryptographic approval technically passes even though no legitimate signer actually authorized the action",
        "expected_category": "signature_replay_verification_bypass",
    },
    {
        "query": "assets locked on one chain are represented by newly minted tokens on another chain, and the mechanism approving that minting was defeated",
        "expected_category": "bridge_cross_chain_exploit",
    },
    {
        "query": "a proposal submitted through a protocol's normal voting process is used to grant the proposer control over protocol funds",
        "expected_category": "governance_attack",
    },
]


def main():
    model = SentenceTransformer(EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    passed = 0
    for test in TEST_QUERIES:
        query_embedding = model.encode([test["query"]]).tolist()
        results = collection.query(query_embeddings=query_embedding, n_results=TOP_K)

        top_meta = results["metadatas"][0][0]
        # attack_type may be multi-tagged as a comma-joined string
        # (e.g. "governance_attack,flash_loan_enabled") — a match on
        # any one of those tags counts as correct.
        top_tags = [t.strip() for t in top_meta["attack_type"].split(",")]
        is_correct = test["expected_category"] in top_tags
        passed += is_correct

        print(f"\nQuery: {test['query']}")
        print(f"Expected: {test['expected_category']}  ->  {'PASS' if is_correct else 'FAIL'} (top tags: {top_tags})")

        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            dist = results["distances"][0][i]
            print(f"  {i+1}. [{meta['attack_type']}] {meta['protocol']} — {meta['section']} (distance: {dist:.4f})")

    print(f"\n{passed}/{len(TEST_QUERIES)} queries matched the correct top category")


if __name__ == "__main__":
    main()