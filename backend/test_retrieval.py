from retrieval import retrieve_context

test_findings = [
    "Reentrancy in VulnerableVault.withdraw: external call before state update",
    "Return value of send() ignored in emergencyWithdraw"
]

chunks = retrieve_context(test_findings, top_k=2)

for chunk in chunks:
    print(f"[{chunk['distance']}] {chunk['category']} — {chunk['title']}")
    print(f"  SWC: {chunk['swc_id']}")
    print()