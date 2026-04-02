# loreto-mcp

MCP server for the [Loreto](https://loreto.io) skill generation API.

Gives Claude Code (and other MCP-compatible agents) a `generate_skills` tool that extracts structured skill packages from any YouTube video, article, PDF, or image — directly inside your coding session.

---

## What this does

When connected, Claude Code can call:

- **`generate_skills`** — Extract ranked skill packages from a URL. Each skill comes back as a `SKILL.md`, `README.md`, reference files, and a test script. Save them to `.claude/skills/` and Claude will apply them automatically on future tasks.
- **`get_quota`** — Check how many API calls remain in your current billing period.

---

## Setup

### 1. Get an API key

Sign up at [loreto.io](https://loreto.io) to get your free API key (`lor_...`).

### 2. Install

```bash
pip install loreto-mcp
```

Or use directly without installing (requires [`uv`](https://docs.astral.sh/uv/)):

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

Then set `LORETO_API_KEY` in your shell environment and teammates do the same with their own keys.

### 4. Verify

Restart Claude Code and run `/mcp` — you should see `loreto` listed with `generate_skills` and `get_quota`.

---

## Usage

Once connected, just ask Claude Code naturally:

```
Use Loreto to extract skills from https://www.youtube.com/watch?v=...
```

```
Check my Loreto quota before we start.
```

```
Extract skills from this article and save them to .claude/skills/
```

Claude will call `generate_skills`, receive the full skill package contents, and can write them directly to your project.

---

## Configuration

| Environment variable | Required | Default | Description |
|---|---|---|---|
| `LORETO_API_KEY` | Yes | — | Your Loreto API key (`lor_...`) |
| `LORETO_BASE_URL` | No | `https://api.loreto.io` | Override for local development |

---

## Plans

Free and paid plans are available. See [loreto.io/pricing](https://loreto.io/pricing) for current limits.

---

## License

MIT
