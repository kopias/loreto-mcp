# Routing Work Across AI Harnesses

> Designs hybrid agent workflows that route tasks intelligently between AI coding
> agent harnesses based on task characteristics rather than defaulting to one tool
> for everything. Use when a team uses multiple AI coding agents, when deciding
> which harness handles which task type, or when designing handoff protocols between
> agents with different architectural dispositions.

## Usage

Invoke when a team uses multiple AI coding agents and wants to improve quality by
routing the right work to the right harness, or when designing explicit handoff
contracts between a planning harness and an implementation harness.

## Example

**Query:** We use both Claude Code and Codex on our team. We keep defaulting to one tool for everything and getting suboptimal results. Design a workflow that routes planning tasks vs. implementation tasks to the right harness, with a handoff protocol between them.

**Behavior:** Presents the two harness dispositions (collaborative/local vs. isolated/enforced), applies the four-axis routing framework (planning vs. implementation, depth vs. breadth, autonomy vs. oversight, tool access), produces the recommended hybrid workflow pattern, and defines explicit handoff contracts for both transition directions.

## When NOT to Use

- The team uses only one harness (use `evaluating-ai-harness-dimensions` to compare options first)
- You are deciding whether to switch harnesses rather than use both (use `detecting-harness-lockin`)
- Task types are not well-defined yet — routing requires knowing what you're routing

## Related Skills

- [`evaluating-ai-harness-dimensions`](../evaluating-ai-harness-dimensions/) — understand each harness's architectural disposition before routing
- [`detecting-harness-lockin`](../detecting-harness-lockin/) — audit whether routing dependencies create their own lock-in
- [`benchmarking-ai-agents-beyond-models`](../benchmarking-ai-agents-beyond-models/) — measure the performance gains from correct routing

## Installation

```bash
cp -r routing-work-across-ai-harnesses ~/.claude/skills/
```
