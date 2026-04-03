# Benchmarking AI Agents Beyond Models

> Separates harness contribution from model contribution when evaluating AI agent
> performance, so that benchmark scores and practitioner comparisons reflect
> real-world system behavior rather than isolated model capability. Use when
> interpreting AI coding agent benchmark results, when a team's agent is
> underperforming relative to benchmark expectations, or when leadership is making
> procurement decisions based on published model comparisons.

## Usage

Invoke when interpreting published AI benchmark scores for procurement decisions,
when an agent underperforms despite strong model benchmarks, or when leadership
cites "Model A scores X%" as a reason to standardize on that tool.

## Example

**Query:** Our leadership read that Model A scored 78% on SWE-bench and Model B scored 42%, and now wants to standardize on Model A. But our engineers say performance in practice doesn't match the benchmarks. Explain what's going on and how to properly evaluate these systems for our use case.

**Behavior:** Explains the benchmark blind spot (model vs. harness contribution), presents the performance decomposition model (agent performance = model capability × harness multiplier), walks through the three benchmark evaluation questions (which harness? task type match? harness held constant?), and produces a five-step harness-aware evaluation protocol with a system-level performance report template.

## When NOT to Use

- You are comparing two versions of the same model in the same harness (benchmarks are more predictive here)
- The evaluation is for academic research rather than team deployment decisions
- You need to evaluate harness architecture rather than interpret benchmark scores (use `evaluating-ai-harness-dimensions`)

## Related Skills

- [`evaluating-ai-harness-dimensions`](../evaluating-ai-harness-dimensions/) — structural evaluation framework that complements benchmark interpretation
- [`detecting-harness-lockin`](../detecting-harness-lockin/) — implications of choosing a harness based on benchmark performance
- [`routing-work-across-ai-harnesses`](../routing-work-across-ai-harnesses/) — performance optimization by routing to the better-suited harness

## Installation

```bash
cp -r benchmarking-ai-agents-beyond-models ~/.claude/skills/
```
