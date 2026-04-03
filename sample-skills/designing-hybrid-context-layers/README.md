# Designing Hybrid Context Layers

> Designs hybrid AI context architectures that combine RAG, knowledge graphs,
> episodic memory, and long-context synthesis appropriately. Use when building
> an agent system that must handle both factual lookup and relational or temporal
> organizational queries, or when asked to architect a context layer, memory
> system, or retrieval pipeline for enterprise or institutional knowledge.

## Usage

Invoke when designing or rearchitecting a retrieval pipeline that must handle
more than simple factual lookup — specifically when agents need to answer
relational, multi-hop, or temporal queries about organizational history.

## Example

**Query:** I'm building an agent for a 500-person engineering org. It needs to answer both 'what does policy X say?' and 'what chain of decisions led to our current cloud vendor?' Design the context architecture.

**Behavior:** Applies the three-layer context model (vector RAG + knowledge graph + temporal/episodic store), produces a query routing decision tree, and explains which query types each layer handles. Includes an implementation roadmap for teams starting from RAG-only.

## When NOT to Use

- Queries are exclusively factual lookups (single-document point queries) — standard RAG is sufficient
- The knowledge base is under 10,000 documents and query complexity is low
- You need to diagnose what is failing before designing the fix (use `diagnosing-rag-failure-modes` first)

## Related Skills

- [`diagnosing-rag-failure-modes`](../diagnosing-rag-failure-modes/) — classify failures before designing the architecture
- [`synthesizing-institutional-knowledge`](../synthesizing-institutional-knowledge/) — schema and ingestion for the episodic and causal layers
- [`auditing-intelligence-context-fit`](../auditing-intelligence-context-fit/) — verify model tier matches the architecture's context complexity

## Installation

```bash
cp -r designing-hybrid-context-layers ~/.claude/skills/
```
