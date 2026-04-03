# Retrieval Decision Matrix

Use this matrix to select the appropriate retrieval layer(s) for a given query.

## Primary Classification

| Query Characteristic | Layer 1 (RAG) | Layer 2 (Graph) | Layer 3 (Temporal) |
|----------------------|:---:|:---:|:---:|
| Answer in a single document | ✓ | — | — |
| Requires joining 2+ documents | — | ✓ | — |
| Involves named entities and their relationships | — | ✓ | — |
| Requires knowing event order | — | — | ✓ |
| Requires causal reasoning ("why") | — | partial | ✓ |
| Spans a time period | — | — | ✓ |
| Lookup of current state/config | ✓ | — | — |
| Policy or procedure lookup | ✓ | — | — |
| Dependency or ownership mapping | — | ✓ | — |
| Decision provenance ("who approved this") | — | ✓ | ✓ |
| Incident post-mortem | — | ✓ | ✓ |
| Architecture evolution | — | partial | ✓ |

## Query Starters → Likely Layer

| Query starts with... | Likely layer |
|----------------------|-------------|
| "What is / What does..." | Layer 1 |
| "List all / Find all..." | Layer 1 (with metadata filter) |
| "Who owns / Who is responsible for..." | Layer 2 |
| "What depends on / What uses..." | Layer 2 |
| "What connects / What links..." | Layer 2 |
| "How did / How did we get to..." | Layer 3 |
| "What led to / What caused..." | Layer 3 |
| "When did / What changed between..." | Layer 3 |
| "Why did we / Why was this..." | Layer 2 + 3 |
| "What should we / Should we..." | All layers → synthesis |

## Compound Query Decomposition

For queries that span multiple layers, decompose before retrieval:

**Example**: "Should we renew the contract with vendor X?"
- Sub-query 1: "What does the current contract say?" → Layer 1
- Sub-query 2: "What teams use vendor X's services?" → Layer 2
- Sub-query 3: "What incidents involved vendor X in the past 2 years?" → Layer 3
- Sub-query 4: "What was the reasoning when we originally selected them?" → Layer 3

Retrieve all four independently, then synthesize with the model.
