# Temporal Reasoning Sleuth

> Engineers temporal reasoning capabilities for AI agents — enabling them to
> trace decision chains, reconstruct causal sequences, and reason over event
> timelines spanning months or years of organizational history. Use when an
> agent must answer questions like "what decisions led to X", "how did this
> situation evolve", or when handling any query requiring temporal sequencing
> and causation across multiple events.

## Usage

Invoke when an agent must reconstruct a causal chain or event sequence across
organizational history, particularly when context spans more than a few weeks
and the query requires reasoning about *why* things are the way they are.

## Example

**Query:** Our agent needs to answer: 'What decisions led to the current state of our auth service?' The relevant history spans 18 months. How do we engineer this temporal reasoning capability?

**Behavior:** Identifies the two LLM temporal reasoning failure modes (attention degradation, context poisoning), presents the three temporal query types (sequence, causal, counterfactual), provides concrete graph traversal queries for causal chains, and implements windowed context synthesis to fit long event histories into the model context window.

## When NOT to Use

- The query is factual (single-event lookup) — use vector RAG
- The history spans fewer than a few weeks with < 20 events — direct context injection is sufficient
- No event graph exists yet (use `synthesizing-institutional-knowledge` to build it first)

## Related Skills

- [`synthesizing-institutional-knowledge`](../synthesizing-institutional-knowledge/) — building the event graph this skill queries
- [`designing-hybrid-context-layers`](../designing-hybrid-context-layers/) — architectural home for the temporal/episodic store
- [`auditing-intelligence-context-fit`](../auditing-intelligence-context-fit/) — verify model tier can handle long causal chains

## Installation

```bash
cp -r temporal-reasoning-sleuth ~/.claude/skills/
```
