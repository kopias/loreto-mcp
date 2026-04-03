# Architecture Patterns for Hybrid Context Layers

## Pattern A: Parallel Retrieval + Model Synthesis

Retrieve independently from each applicable layer, then pass all results to the model as structured context blocks.

```
User Query
    │
    ▼
Query Classifier
    ├── Layer 1 query → Vector DB → factual chunks
    ├── Layer 2 query → Graph DB  → entity subgraph
    └── Layer 3 query → Event DB  → timeline slice
                                        │
                                        ▼
                              Context Assembly
                              [facts | graph | timeline]
                                        │
                                        ▼
                                   LLM Synthesis
```

**When to use**: Compound queries, general-purpose agents
**Trade-off**: Higher latency (3 parallel retrievals); richer context

---

## Pattern B: Cascading Retrieval

Start narrow, expand only if the answer is incomplete.

```
User Query → Layer 1 (Vector RAG)
    │
    ├── Answer found? → DONE
    │
    └── Insufficient? → Layer 2 (Graph)
            │
            ├── Answer found? → DONE
            │
            └── Insufficient? → Layer 3 (Temporal)
                        │
                        └── Synthesize
```

**When to use**: Latency-sensitive systems; majority of queries are factual
**Trade-off**: Lower latency on simple queries; can miss relational context that wasn't triggered

---

## Pattern C: Graph-Guided RAG

Use the knowledge graph to identify relevant entity neighborhoods, then use those as filters for vector search.

```
User Query → Graph traversal → [relevant node IDs]
                                        │
                                        ▼
                              Vector Search (filtered by node IDs)
                                        │
                                        ▼
                                   LLM Synthesis
```

**When to use**: When you have a knowledge graph but want to keep serving answers from document chunks
**Trade-off**: Requires graph and vector DB in sync; better precision than unfiltered RAG

---

## Pattern D: Windowed Temporal Synthesis

For long-horizon temporal queries, compress distant history and expand recent context.

```
Query: "How did X evolve over the past 2 years?"
    │
    ▼
Temporal Index: pull all events in range
    │
    ▼
Summarization Pass:
    - Events > 6 months ago → compress to 1-paragraph summaries
    - Events 1–6 months ago → keep structured event nodes
    - Events < 1 month ago → full detail
    │
    ▼
Windowed context → LLM (fits in context window)
```

**When to use**: Long-horizon causal/historical queries
**Trade-off**: Compression loses detail in distant history; tune the window based on query type

---

## Recommended Technology Stack

| Layer | Open Source | Managed |
|-------|-------------|---------|
| Factual (Vector) | pgvector, Weaviate, Qdrant | Pinecone, Zilliz |
| Relational (Graph) | Neo4j Community, Memgraph | Neo4j Aura, Amazon Neptune |
| Temporal (Events) | TimescaleDB, InfluxDB | Timescale Cloud, InfluxDB Cloud |
| Orchestration | LangGraph, LlamaIndex | —  |

For most enterprise orgs starting out: **pgvector + Neo4j + TimescaleDB** on Postgres-adjacent infrastructure minimizes operational complexity.
