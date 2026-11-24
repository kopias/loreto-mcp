<p align="center">
  <img src="https://raw.githubusercontent.com/kopias/loreto-mcp/main/assets/banner.png" alt="Stop babysitting your open model. Open models loop, stall, and say done too soon; a harness tuned to the model breaks the loop, keeps it moving, and holds it to your checks. npx loreto add qwen3.8-27b --agent opencode. For Hermes, OpenCode, Claude Code, Codex and DeepSeek. Qwen3.8 27B is known for thinking for an hour and writing nothing; its harness is built for a first edit sooner, for fewer tokens." width="100%">
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/loreto"><img src="https://img.shields.io/npm/v/loreto?label=npx%20loreto&color=a6411f" alt="npm"></a>
  <a href="https://pypi.org/project/loreto-mcp/"><img src="https://img.shields.io/pypi/v/loreto-mcp?label=loreto-mcp&color=2f6a6d" alt="PyPI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/licence-MIT-15110e" alt="MIT"></a>
  <a href="https://loreto.io/harnesses"><img src="https://img.shields.io/badge/harnesses-69%20open%20models-c49a52" alt="69 open models"></a>
</p>

# Loreto: free harnesses for open models

**Stop babysitting your open model.**

Open models *loop*, *stall*, and say *"done"* too soon. Usually that is not the weights. It is the harness around them: settings meant for a different model, no limit on the loop, and nothing that checks the work before the agent calls it finished.

Loreto writes a harness for **one model in one coding agent**, from that model's own public bug reports, and installs it with one line:

```bash
npx loreto add qwen3.8-27b --agent opencode
```

Free, no account, no key. **69 open models** (Qwen, Gemma, DeepSeek, GLM, gpt-oss, Nemotron, Mistral, MiniMax, Kimi, MiMo, Granite, Step and more) in **Hermes, OpenCode, Claude Code, Codex and DeepSeek's harness**.

## What it changes

| The model… | The harness… | How |
|---|---|---|
| **loops**: reads the same file again, retries the same search | **breaks the loop** | In Claude Code, Codex and Hermes, `loop_guard.py` blocks an identical call repeated with no edit in between, and a long run of reading with nothing written. In OpenCode, which has no such hook, the steps are capped. |
| **stalls**: thinks for an hour, re-checks a plan it already has | **keeps it moving** | The reasoning effort and sampling its template and card actually accept, a server thinking budget, and a rule: check a plan once, then make the first edit. |
| **says "done" too soon** | **holds it to your checks** | `gates.py` runs the checks you already have (parse, types, tests) and the agent must show the output. A skipped check is not a pass. |

Same model, different harness, different result: Mistral Large 4 scored **41.4%** on Terminal Bench 4.0 in one agent and **24.7%** in another at the same effort ([Artificial Analysis figures, quoted here](https://huggingface.co/mistralai/Mistral-Large-4-1T-A52B/discussions/17); neither harness is ours). Most of what decides whether an open model is usable sits outside the weights.

**Honest limits.** A harness does not make a 27B model match a frontier model on hard problems. In agents without hooks, the rules and checks are instructions the model is asked to follow, not walls it cannot climb. And we have not benchmarked these harnesses yet: treat them as fixes for reported problems, not a score.

## Example: Qwen3.8 27B in OpenCode

Reported on the model's page: 45 to 80+ minutes of thinking on a 5K token plan before writing a line ([#178](https://huggingface.co/Qwen/Qwen3.8-27B/discussions/178)). OpenCode offers a "high" effort the template does not have, so every request fails with a 500 and is retried five times ([opencode#53202](https://github.com/anomalyco/opencode/issues/53202)). The harness:

```jsonc
// opencode.json (the parts that matter)
"effort": ["low", "medium", "xhigh"],                 // only the levels it has
"temperature": 0.6, "top_p": 0.95, "top_k": 20,       // what the card and the thread agree on
"reasoning_effort": "medium"
```

```markdown
<!-- AGENTS.md -->
- Check a plan once. If it holds, make the first edit or run the first command.
  A second "wait, let me double-check" means act now.
- Before you say done, run gates.py check and show what it printed.
```

Plus a serving note for the cap the agent cannot set (`llama-server … --reasoning-budget 6144`), and a known issues file that links every report above so you can check our reading of them.

## Install

**With npx** (Node 18+), in the repository you are working in:

```bash
npx loreto list qwen                                   # find your model
npx loreto add qwen3.8-27b --agent opencode            # install its harness
npx loreto add gemma-4-31b --agent hermes --mode defend
```

- `--agent`: `claude-code` (default), `opencode`, `codex`, `hermes` or `deepseek`
- `--mode`: `balanced` (Everyday, default), `economy` (Quick fixes), `attack` (Hard problems), `defend` (Careful changes)
- `--build`: a published build, e.g. `unsloth/Qwen3.8-27B-GGUF`
- `--zip`: save the files instead of installing them

Files you already have (`CLAUDE.md`, `AGENTS.md`, your agent config) are kept: Loreto's section is merged between markers, so running it again replaces only that section. `git status` shows exactly what changed.

**With your agent, over MCP:**

```bash
claude mcp add loreto -- uvx loreto-mcp
```

Then ask: *"Install the Loreto harness for Qwen3.8 27B."* Or in any MCP client config:

```json
{ "mcpServers": { "loreto": { "command": "uvx", "args": ["loreto-mcp"] } } }
```

**Or read every file first** at [loreto.io/harnesses](https://loreto.io/harnesses).

## What a harness holds

The OpenCode harness for Qwen3.8 27B, as installed (each agent gets its own layout):

```
AGENTS.md                                   rules for this model, merged into yours
opencode.json                               effort levels, sampling, step limit
.opencode/skills/qwen3-8-27b-playbook/
  SKILL.md                                  how to work as this model
  references/known-issues.md                every public report it answers, linked
  references/serving.md                     server settings the agent can't set
  references/design.md                      why each choice was made
  scripts/gates.py  gates.json              the checks before "done"
  scripts/doctor.py                         asks your server what an agent will (tools, template, effort)
.opencode/agents/qwen3-8-27b-playbook-reviewer.md   a second pass on the diff
```

In Claude Code, Codex and Hermes there is also `scripts/loop_guard.py`, wired in as a before-tool hook. Everything is plain files and stdlib Python. Nothing runs from the network, and `gates.py` never installs or edits anything.

## Then tune it to your repository ($5)

The free harness fixes what the model gets wrong everywhere. Your repository has its own history: code that was added and reverted, modules everything imports, deprecated calls still in use, blocks copied between files. Loreto reads it and adds:

- **Anti-patterns** your team already reverted. Guard rails block them.
- **Abstractions** the rest of the code imports. The agent reuses them instead of writing a second one.
- **Deprecated code**, what replaced it and who still calls it. A new call gets a warning.
- **Simplification**: duplicated blocks, helpers defined many times, modules nothing imports.

Reading is free and shows every finding first. The tuned harness is **$5 once**, or **$2 a file**. Ask your agent *"Read github.com/your-org/your-repo with Loreto"*, or paste the repository at [loreto.io/tune](https://loreto.io/tune).

## Private repositories

Public repositories need nothing. A private one is read through **your own GitHub connection**, so Loreto only ever sees what you chose to share:

1. Sign in at [loreto.io](https://loreto.io) and press the **GitHub** button. Loreto's GitHub App is read-only, and you pick the repositories it can see (change them any time at [github.com/settings/installations](https://github.com/settings/installations)).
2. Create a key at [loreto.io/dashboard/developer](https://loreto.io/dashboard/developer) and give it to the server:
   ```bash
   claude mcp add loreto -e LORETO_API_KEY=lor_... -- uvx loreto-mcp
   ```
3. Ask your agent to read the repository as usual.

If a repository isn't reachable, `read_repo` says which of these steps is missing instead of failing. Private reads belong to your account and are never shown to anyone else. The repository is cloned read-only on Loreto's server to read its history and code, and the evidence your files are written from (figures from git, plus the first lines of a few of the busiest source files) goes to the model provider that writes them; nothing is published.

Want the code to stay on your machine? `check_approach` and `plan_change` run **Gitology locally** and need no account at all.

---

## Tools

| Tool | Cost | What it does |
|---|---|---|
| `list_model_harnesses(query?)` | free | The open models with a free harness (Qwen, GLM, DeepSeek, Gemma, gpt-oss, Nemotron…). |
| `get_model_harness(model, agent, mode, path)` | free | Installs the harness for the model you run: rules for its known problems, agent settings, the checks before done, a loop guard (where the agent has hooks), a reviewer and a server check. |
| `list_agents` | free | The supported agents and where each reads its files. |
| `read_repo(repo, agent)` | free | Reads the history; returns what it says, the files, the prices and a `read_id`. |
| `buy_harness(read_id, agent, files?)` | $5 / $2 a file | Returns a Stripe checkout link **for the person to pay**. The agent cannot pay. |
| `get_harness(path)` | — | After payment: waits for the files and installs them into the repository at `path`. |
| `ask_repo(question)` | included | Why was this reverted? Who knows this code? Answered from the history. |
| `check_approach(approach, path?)` | free, local | Should I build it this way here? Good to go, risky or don't merge, with the evidence and a better route. Runs [Gitology](#gitology-ask-before-you-build). |
| `plan_change(request, path?)` | free, local | A change kit: `SPEC.md`, and `STEPS.md` small enough for a small model to build. Runs Gitology. |

A typical session:

> **You:** arm Claude Code with this repo
>
> **Agent:** *(read_repo)* Half of the last 400 commits touch 2 files or fewer… `src/api/routes.py` and `src/api/schema.py` changed together 17 times… The harness is $5. *(buy_harness)* Here is the checkout link.
>
> **You:** paid
>
> **Agent:** *(get_harness)* Armed Claude Code: `~ CLAUDE.md (kept yours, added the Loreto section)`, `+ .claude/skills/…`

## Gitology: ask before you build

[Gitology](https://loreto.io/gitology) maps a repository on your machine into a graph of what exists (modules, files, symbols, endpoints, tests, decision records, owners) and how it holds together (imports, changes-with, reverted-by, tested-by), and keeps it current through git hooks. `check_approach` and `plan_change` call it:

> **You:** add retries to PaymentClient.capture
>
> **Agent:** *(check_approach)* **DON'T MERGE.** This exact change was made in `823cc78`, captured cards twice, and was reverted in `fac848a`; ADR-014 says retries belong in workers. Better route: wrap the call in `CaptureWorker` with `with_backoff`. *(plan_change)* Kit written: 4 steps.

Install it once (Python 3.9+), and the tools find it:

```bash
curl -fsSL https://loreto.io/gitology/install.sh | sh
```

The graph is built locally. Only the verdict and the change kit call a model, they send it the excerpts and history that bear on the question, and the model can be local: set `GITOLOGY_MODEL=ollama:<model>`, or `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` in the MCP server's `env`. Gitology also runs on its own as a CLI and MCP server: see [loreto.io/gitology](https://loreto.io/gitology).

## For agents with a wallet: x402

An agent holding USDC on Base can buy without a person or a browser, over [x402](https://www.x402.org). The harness is written **before** anyone pays, and the paid call answers with the files, so a payment settles only on a delivery:

```
POST https://api.loreto.io/api/v1/harness/prepare        {"repo": "...", "agent": "claude-code"}   free
GET  https://api.loreto.io/api/v1/harness/prepare/{id}   poll until "ready"                         free
POST https://api.loreto.io/api/v1/harness/x402           {"prepare_id": "..."}                      $5
POST https://api.loreto.io/api/v1/harness/x402/file      {"prepare_id": "...", "file": "skill"}     $2
```

Public repositories only. A harness that is not ready yet answers 409 and nothing is charged. Full walkthrough with a Python x402 client: [loreto.io/docs#x402](https://loreto.io/docs#x402). This MCP server does not sign payments.

## Changes in 1.3.0

- Free model harnesses: `list_model_harnesses` and `get_model_harness` fit Claude Code, OpenCode, Codex, Hermes or DeepSeek Harness to an open-weight model's known problems. No account, no payment. The same files as [loreto.io/harnesses](https://loreto.io/harnesses).

## Changes in 1.2.0

- Every agent the site writes for, including DeepSeek Harness, Antigravity and GitHub Copilot (checked against the live list).
- `read_repo` leads with what it found: anti-patterns it will block, abstractions to reuse, deprecated code still in use, duplication worth simplifying.
- A private repository gets the three steps to read it (connect GitHub, create a key, set `LORETO_API_KEY`) instead of an error.
- Descriptions say what a harness holds now: six references and the skill's guard-rail scripts.

## Changes in 1.1.1

`check_approach` speaks plain words: good to go, risky, don't merge, not sure (from Gitology's new labels).

## Changes in 1.1

`check_approach` and `plan_change`, through Gitology. Nothing else changed.

## Changes in 1.0

loreto-mcp used to wrap Loreto's skill generator and marketplace. Loreto is now about one thing, the harness, and the generator is no longer public. The `generate_skills`, catalog, `marketplace_*` and `agent_*` tools are gone; pin `loreto-mcp<1` if you depended on them.

---

If a harness saved you an hour of watching a model think, a ⭐ helps the next person find it. Found a model behaving badly that we don't cover? [Open an issue](https://github.com/kopias/loreto-mcp/issues) with the report.

[loreto.io](https://loreto.io) · [Harnesses](https://loreto.io/harnesses) · [Gitology](https://loreto.io/gitology) · [Pricing](https://loreto.io/pricing) · MIT licence
