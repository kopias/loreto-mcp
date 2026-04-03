# Evaluating AI Harness Dimensions

> Evaluates AI coding agent platforms across five structural dimensions — execution
> philosophy, state and memory, context management, tool integration, and multi-agent
> architecture — that determine real-world performance independently of model quality.
> Use when selecting an AI coding agent platform, comparing two agents beyond benchmark
> scores, or auditing why the same model performs differently in different environments.

## Usage

Invoke when selecting, comparing, or auditing an AI coding agent harness. Produces
a structured five-dimension assessment with fit scores and a recommendation — before
a team commits to a harness or before citing a benchmark score as predictive.

## Example

**Query:** Our team is choosing between two AI coding agents. Both use the same underlying model. One runs in our local terminal with full shell access; the other runs tasks in isolated cloud containers. Walk us through how to evaluate these two systems across the key harness dimensions that will affect our team's work.

**Behavior:** Applies the five-dimension framework (execution philosophy, state/memory, context management, tool integration, multi-agent architecture), presents trade-off tables for each dimension, and produces a scored assessment template identifying which dimensions fit the team's needs and which create mismatches.

## When NOT to Use

- You need to compare model capability rather than harness architecture (see published benchmarks, but read `benchmarking-ai-agents-beyond-models` first)
- You are already committed to a harness and want to audit switching cost (use `detecting-harness-lockin`)
- You want to design task routing between two harnesses (use `routing-work-across-ai-harnesses`)

## Related Skills

- [`detecting-harness-lockin`](../detecting-harness-lockin/) — price the switching cost after committing to a harness
- [`routing-work-across-ai-harnesses`](../routing-work-across-ai-harnesses/) — route work between harnesses based on task type
- [`benchmarking-ai-agents-beyond-models`](../benchmarking-ai-agents-beyond-models/) — interpret benchmark scores in context of harness differences

## Installation

```bash
cp -r evaluating-ai-harness-dimensions ~/.claude/skills/
```
