# Detecting Harness Lock-in

> Identifies and quantifies the compounding switching cost of an AI coding agent
> harness commitment before it becomes invisible. Use when evaluating whether to
> change AI coding agent platforms, when pricing a harness decision for a team or
> organization, or when auditing how much process infrastructure has accumulated
> around a current agent architecture.

## Usage

Invoke when a team is considering switching AI harnesses, when a CTO asks how
much it would cost to switch, or before committing to a harness to price the
future switching cost in advance. Produces a four-layer lock-in audit with a
total switching cost estimate.

## Example

**Query:** We've been using one AI coding agent for 8 months. Our engineers have built custom workflows, we maintain CLAUDE.md files for every project, and we've deployed a dozen MCP connectors. Now the CTO wants to evaluate switching to a different tool. Help us audit and price the true switching cost.

**Behavior:** Runs the four-layer lock-in audit (individual workflows, context investment, team process integration, infrastructure/tooling), estimates switching cost for each layer in person-weeks, notes the compounding rate, and produces a structured lock-in audit report with a recommendation to commit, switch now, or design hybrid workflow.

## When NOT to Use

- You haven't selected a harness yet (use `evaluating-ai-harness-dimensions` first)
- You want to route work between harnesses rather than switch (use `routing-work-across-ai-harnesses`)
- The team has been using the harness for under 2 months (insufficient lock-in to audit)

## Related Skills

- [`evaluating-ai-harness-dimensions`](../evaluating-ai-harness-dimensions/) — evaluate a harness before committing
- [`routing-work-across-ai-harnesses`](../routing-work-across-ai-harnesses/) — reduce single-harness dependency without switching
- [`benchmarking-ai-agents-beyond-models`](../benchmarking-ai-agents-beyond-models/) — understand what you gain/lose in a harness switch

## Installation

```bash
cp -r detecting-harness-lockin ~/.claude/skills/
```
