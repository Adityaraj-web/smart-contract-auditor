"""
Runs realistic test queries against the Chroma collection to validate
that retrieval returns chunks from the correct vulnerability category.
"""

from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "vulnerability_corpus"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3

# Phrased like a Slither finding description, not a category label —
# that's how this gets queried for real in Phase 3.
TEST_QUERIES = [
    {
        "query": "external call sends ETH to an address before the caller's balance is updated",
        "expected_category": "reentrancy",
    },
    {
        "query": "low-level call return value is not checked, transfer may silently fail",
        "expected_category": "unchecked-call-return-value",
    },
    {
        "query": "arithmetic multiplication of user-controlled values may wrap around the max uint256 value",
        "expected_category": "integer-overflow-underflow",
    },
    {
        "query": "sensitive function changing ownership has no onlyOwner or role check",
        "expected_category": "access-control",
    },
    {
        "query": "authorization check uses the original transaction sender instead of the immediate caller",
        "expected_category": "tx-origin",
    },
    {
        "query": "contract executes code from another address using the caller's own storage context",
        "expected_category": "delegatecall",
    },
    {
        "query": "attacker observes a pending transaction in the mempool and submits a competing one with higher gas to execute first",
        "expected_category": "front-running",
    },
    {
        "query": "lottery contract derives a random winning number from the block timestamp",
        "expected_category": "timestamp-dependence",
    },
    {
        "query": "function loops over an array of all participants to pay everyone, gas cost grows with the list and may exceed the block gas limit",
        "expected_category": "dos-unbounded-gas",
    },
    {
        "query": "local struct or array variable defaults to a storage reference pointing at slot zero instead of being explicitly assigned",
        "expected_category": "uninitialized-storage-pointer",
    },
    {
        "query": "a previously valid off-chain signature is resubmitted to trigger the same authorized action a second time",
        "expected_category": "signature-replay",
    },
    {
        "query": "old contract constructor function no longer matches the contract name and becomes a public callable function",
        "expected_category": "default-visibility",
    },
    {
        "query": "protocol reads asset price directly from a liquidity pool's reserves, which can be skewed by a large trade",
        "expected_category": "price-oracle-manipulation",
    },
    {
        "query": "attacker borrows a large uncollateralized sum and repays it within the same transaction to fund a price or governance manipulation",
        "expected_category": "flash-loan-attacks",
    },
    {
        "query": "a small number of privileged signers or validator keys control approval of withdrawals, and compromising enough of them grants full control",
        "expected_category": "centralization-admin-key-risk",
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

        top_category = results["metadatas"][0][0]["category"]
        is_correct = top_category == test["expected_category"]
        passed += is_correct

        print(f"\nQuery: {test['query']}")
        print(f"Expected: {test['expected_category']}  ->  {'PASS' if is_correct else 'FAIL'} (top: {top_category})")

        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            dist = results["distances"][0][i]
            print(f"  {i+1}. [{meta['category']}] {meta['title']} (distance: {dist:.4f})")

    print(f"\n{passed}/{len(TEST_QUERIES)} queries matched the correct top category")


if __name__ == "__main__":
    main()