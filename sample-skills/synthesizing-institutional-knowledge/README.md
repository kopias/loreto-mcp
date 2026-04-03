# Synthesizing Institutional Knowledge

> Builds organizational memory systems that capture decision provenance,
> causal chains, and institutional context beyond document embeddings. Use
> when designing knowledge bases for AI agents that must answer questions
> about why decisions were made, how situations evolved over time, or what
> historical context drives current organizational state.

## Usage

Invoke when designing or auditing a knowledge base that needs to preserve
the *why* behind organizational decisions, not just the *what* — particularly
when agents must answer questions about decision rationale, historical causation,
or institutional context that embedding-based retrieval cannot capture.

## Example

**Query:** We want to build an org memory system so our AI agents can answer 'why did we choose Postgres over MySQL in 2021?' How should we structure the knowledge and what schema should events follow?

**Behavior:** Classifies the three knowledge types (declarative, episodic, causal), maps each to an appropriate storage layer, and produces a complete institutional event schema with all required provenance fields. Includes an ingestion workflow and query patterns for each knowledge type.

## When NOT to Use

- The knowledge base only needs to answer factual lookup queries (use vector RAG alone)
- You have no ability to capture provenance at ingestion time (retroactive capture is expensive but partially covered)
- The organization's history is under 6 months old (insufficient event history to warrant the investment)

## Related Skills

- [`designing-hybrid-context-layers`](../designing-hybrid-context-layers/) — architecture layer that hosts this knowledge schema
- [`diagnosing-rag-failure-modes`](../diagnosing-rag-failure-modes/) — identifies when provenance loss is causing agent failures
- [`temporal-reasoning-sleuth`](../temporal-reasoning-sleuth/) — querying the causal event graph this skill populates

## Installation

```bash
cp -r synthesizing-institutional-knowledge ~/.claude/skills/
```
