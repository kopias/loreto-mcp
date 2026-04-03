# Auditing Intelligence-Context Fit

> Audits the fit between a model's reasoning capability and the complexity of
> the context it receives. Use when an AI system is underperforming despite
> good retrieval, when teams are unsure whether to upgrade their model or
> improve their context pipeline, or when diagnosing the "long context and weak
> reasoning equals harmful output" pattern in production agent systems.

## Usage

Invoke when an AI system's output quality is poor despite apparently good
retrieval, or when upgrading the model didn't help, or when answers sound
plausible but are subtly wrong in ways that suggest context overload.

## Example

**Query:** We're using Claude Haiku to answer questions about 2 years of incident history and architectural decisions. The answers sound plausible but keep being wrong in subtle ways. Run a fit audit and tell us what's happening.

**Behavior:** Classifies the context complexity level (Level 4–5 causal/temporal), identifies the Haiku tier as insufficient for that complexity, diagnoses the specific mismatch scenario (Scenario A: context too complex for model tier), and prescribes the fix — upgrade to Sonnet or Opus, or decompose queries to lower complexity.

## When NOT to Use

- Retrieval quality is clearly poor (wrong documents returned) — fix retrieval first with `diagnosing-rag-failure-modes`
- The model is clearly appropriate and the problem is prompt engineering
- You are evaluating harness performance rather than model-context fit (use `evaluating-ai-harness-dimensions`)

## Related Skills

- [`diagnosing-rag-failure-modes`](../diagnosing-rag-failure-modes/) — diagnose retrieval failures before auditing model fit
- [`designing-hybrid-context-layers`](../designing-hybrid-context-layers/) — architecture changes that reduce context complexity
- [`temporal-reasoning-sleuth`](../temporal-reasoning-sleuth/) — windowed compression to bring temporal context within model capability

## Installation

```bash
cp -r auditing-intelligence-context-fit ~/.claude/skills/
```
