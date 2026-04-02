# loreto-mcp

Turn any YouTube video, article, PDF, or image into a reusable Claude Code skill — without leaving your editor.

---

## What it does

Loreto analyzes a content source and extracts **structured skill packages** that Claude Code can apply to future tasks. Each skill contains:

- **`SKILL.md`** — Principles, failure modes, implementation steps, and architectural patterns
- **`README.md`** — Overview and usage context
- **Reference files** — Supporting patterns and data structures
- **Test script** — Runnable validation for the skill's core concepts

Save skills to `.claude/skills/` and Claude picks them up automatically on relevant tasks — reducing hallucinations, token usage, and re-explaining the same concepts over and over.

---

## Example: What a generated skill looks like

The skill below was extracted from a technical video on AI agent memory systems. One command. No copy-paste.

<details>
<summary><strong>engineering-temporal-reasoning</strong> — extracted from a YouTube video on AI agent architecture</summary>

```markdown
---
name: engineering-temporal-reasoning
description: >
  Engineers temporal reasoning capabilities for AI agents — enabling them to
  trace decision chains, reconstruct causal sequences, and reason over event
  timelines spanning months or years of organizational history. Use when an
  agent must answer questions like "what decisions led to X", "how did this
  situation evolve", or when handling any query requiring temporal sequencing
  and causation across multiple events.
---

## Why LLMs Struggle with Temporal Reasoning at Scale

LLMs have two temporal reasoning failure modes:

**1. Attention degradation**: When a long context contains hundreds of events
in chronological order, attention distributes across the entire sequence. The
model cannot reliably identify which events are causally linked vs. merely
adjacent in time. "Lost in the middle" is the symptom.

**2. Context poisoning**: Events retrieved without their causal context
contaminate reasoning. If you retrieve "auth service migrated to OAuth2"
without "auth breach incident that caused it", the model may draw wrong
conclusions about the migration's purpose.

The fix is not bigger context windows — it is structured temporal storage and
targeted retrieval that feeds the model a curated causal slice, not a raw
timeline dump.

## The Three Temporal Query Types

### Type 1: Sequence Queries
"What happened between A and B?"
- Retrieve all events in a time window for a set of entities
- Return in chronological order with timestamps
- Model synthesizes into a narrative

### Type 2: Causal Queries
"What caused X?" or "What led to Y?"
- Start from a target event node
- Traverse causal_predecessors edges (up to N hops)
- Reconstruct the causal chain

### Type 3: Counterfactual Queries
"What if decision D had been different?"
- Retrieve the full causal subgraph downstream of the decision
- Feed it as structured context to the model

## Windowed Context Synthesis

def build_temporal_context(events, query_date):
    distant = [e for e in events if (query_date - e.timestamp).days > 180]
    recent  = [e for e in events if 30 < (query_date - e.timestamp).days <= 180]
    immediate = [e for e in events if (query_date - e.timestamp).days <= 30]
    # compress distant → structured recent → full detail immediate
```

</details>

This is one skill from one video. Loreto extracts up to 3 skills per source, each with the same depth.

---

## Setup

### 1. Get an API key

Sign up at [loreto.io](https://loreto.io) to get your free API key (`lor_...`).

### 2. Install

```bash
pip install loreto-mcp
```

Or run directly without installing (requires [`uv`](https://docs.astral.sh/uv/)):

```bash
uvx loreto-mcp
```

### 3. Configure Claude Code

**User-scoped** (works across all your projects) — add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "loreto": {
      "command": "uvx",
      "args": ["loreto-mcp"],
      "env": {
        "LORETO_API_KEY": "lor_..."
      }
    }
  }
}
```

**Project-scoped** (shared with your team) — add to `.mcp.json` at your project root:

```json
{
  "mcpServers": {
    "loreto": {
      "command": "uvx",
      "args": ["loreto-mcp"],
      "env": {
        "LORETO_API_KEY": "${LORETO_API_KEY}"
      }
    }
  }
}
```

### 4. Verify

Restart Claude Code and run `/mcp` — you should see `loreto` listed with `generate_skills` and `get_quota`.

---

## Usage

Once connected, just ask Claude Code naturally:

```
Use Loreto to extract skills from https://www.youtube.com/watch?v=...
```

```
Extract skills from this article and save them to .claude/skills/
```

```
Check my Loreto quota before we start.
```

Claude calls `generate_skills`, receives the full skill package, and can write the files directly to your project.

---

## Available tools

| Tool | Description |
|---|---|
| `generate_skills` | Extract ranked skill packages from a URL. Returns full file contents ready to save. |
| `get_quota` | Check calls used, monthly limit, and plan for your API key. |

### `generate_skills` parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `source` | `str` | required | URL to analyze — YouTube, article, public PDF, or image |
| `source_type` | `str` | `"auto"` | `"auto"` \| `"youtube"` \| `"article"` \| `"pdf"` \| `"image"` |
| `test_language` | `str` | `"python"` | `"python"` \| `"typescript"` \| `"javascript"` |
| `include_visuals` | `bool` | `true` | Embed Mermaid diagrams in `SKILL.md` |
| `context` | `str` | `null` | 1–3 sentence hint to guide extraction (max 500 chars) |
| `themes_to_process` | `list[str]` | `null` | Follow-up call: skill names from a previous response's queued themes |

---

## Supported sources

| Source | Notes |
|---|---|
| YouTube videos | Up to 60 minutes |
| Web articles | Any publicly accessible URL |
| PDFs | Up to 100 pages |
| Images | Diagrams, whiteboards, slides (up to 20 MB) |

---

## Configuration

| Environment variable | Required | Default | Description |
|---|---|---|---|
| `LORETO_API_KEY` | Yes | — | Your Loreto API key (`lor_...`) |
| `LORETO_BASE_URL` | No | `https://api.loreto.io` | Override for local development |

---

## Plans

Free and paid plans available. See [loreto.io/pricing](https://loreto.io/pricing) for current limits.

---

## License

MIT
