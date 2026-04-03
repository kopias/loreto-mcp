# Diagnosing RAG Failure Modes

> Diagnoses RAG system failures by classifying queries as factual-lookup-safe
> vs. relational-temporal (where RAG breaks). Use when a RAG pipeline is
> returning poor results, an agent fails on multi-hop or causal queries,
> or when a team asks why their retrieval system cannot answer questions about
> decision histories, event sequences, or organizational causation chains.

## Usage

Invoke when a RAG pipeline is returning poor results or when queries about
multi-hop relationships, event sequences, or causal histories consistently fail.
Produces a structured failure classification report with a specific architecture fix.

## Example

**Query:** Our RAG pipeline keeps failing on this query: 'What sequence of decisions led to our current microservices authentication architecture?' The retrieval returns relevant docs but the answer is always incomplete or wrong. Diagnose what's happening and classify the failure.

**Behavior:** Applies the two-class query taxonomy to classify the query as Class B (relational/temporal), identifies the specific failure pattern (temporal sequencing failure), and produces a RAG failure diagnosis report with a recommended architecture change — in this case, a timeline/episodic index.

## When NOT to Use

- The query is a simple factual lookup (single document, single hop) — RAG should work
- You already know the failure pattern and need architecture design (use `designing-hybrid-context-layers`)
- You are diagnosing model reasoning quality rather than retrieval quality (use `auditing-intelligence-context-fit`)

## Related Skills

- [`designing-hybrid-context-layers`](../designing-hybrid-context-layers/) — architecture remediation after diagnosis
- [`synthesizing-institutional-knowledge`](../synthesizing-institutional-knowledge/) — building org memory to prevent provenance failures
- [`temporal-reasoning-sleuth`](../temporal-reasoning-sleuth/) — engineering temporal reasoning for causal query types

## Installation

```bash
cp -r diagnosing-rag-failure-modes ~/.claude/skills/
```
