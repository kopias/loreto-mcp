"""
Loreto MCP Server

Exposes Loreto skill generation as MCP tools so AI coding agents
(Claude Code, Codex, OpenCode) can call generate_skills directly.

Billing — Loreto runs two parallel paths:
  • API key (lor_...) — what this MCP uses; free tier + Pro plan.
  • x402 pay-per-call — flat $0.75/call in USDC on Base mainnet, no signup.
    The MCP itself does not sign x402 payments — for x402 use
    POST /api/v1/skills/x402/generate directly with the x402 Python SDK
    (https://pypi.org/project/x402/). See https://loreto.io/docs-x402.

Required environment variable:
    LORETO_API_KEY  —  your Loreto API key (lor_...)

Optional:
    LORETO_BASE_URL        —  override the API base URL (default: https://api.loreto.io)
    LORETO_PUBLIC_BASE_URL —  override the marketing site URL  (default: https://loreto.io)

Usage (stdio transport, for Claude Code):
    uvx loreto-mcp
    # or: python -m loreto_mcp.server
"""

from __future__ import annotations

import json as _json
import os
import textwrap
from typing import Optional

import httpx
from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_API_KEY = os.environ.get("LORETO_API_KEY", "")
_BASE_URL = os.environ.get("LORETO_BASE_URL", "https://api.loreto.io").rstrip("/")
# Public marketing site — serves skills_data.json (the catalog), no auth.
_PUBLIC_BASE_URL = os.environ.get("LORETO_PUBLIC_BASE_URL", "https://loreto.io").rstrip("/")

if not _API_KEY:
    raise RuntimeError(
        "LORETO_API_KEY environment variable is not set. "
        "Get your API key at https://loreto.io and add it to your MCP config."
    )

_HEADERS = {
    "X-API-Key": _API_KEY,
    "Content-Type": "application/json",
}

_PORTAL_HEADERS = {
    "X-Portal-Key": _API_KEY,
}

# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="Loreto Skills",
    instructions=textwrap.dedent("""
        Loreto generates structured skill packages from content sources.
        Each skill contains a SKILL.md (principles, failure modes, implementation
        steps), README.md, reference files, and a runnable test script.

        Two billing paths run side-by-side on the Loreto API:

          • API key (lor_...) — what this MCP uses by default. Free tier (2/mo)
            and Pro ($29/mo for 100 calls). Set LORETO_API_KEY in the MCP env.

          • x402 pay-per-call — flat $0.75 per generation in USDC on Base
            mainnet. No signup, no monthly cap. The MCP itself does not sign
            x402 payments; for x402 use the REST endpoint
            POST /api/v1/skills/x402/generate directly with the x402 Python SDK
            (https://pypi.org/project/x402/). See https://loreto.io/docs-x402.

        Tools by access level:

          • generate_skills, get_quota — require LORETO_API_KEY. get_quota is
            irrelevant on x402 (no monthly cap; you pay per call).

          • list_skills, get_skill, verify_artifacts, estimate_cost — call
            public endpoints. No API key or payment needed. Use them freely to
            discover, inspect, and verify skills before recommending or
            generating.

        Every successful generation — API-key OR x402 — returns a generation_id
        (uuid4). Pass it to verify_artifacts to fetch the provenance manifest
        (source URL, theme plan, quality scores, artifact byte counts, bundle
        sha256) without re-running the pipeline.
    """).strip(),
)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def generate_skills(
    source: str,
    source_type: str = "auto",
    test_language: str = "python",
    include_visuals: bool = True,
    context: Optional[str] = None,
    themes_to_process: Optional[list[str]] = None,
) -> str:
    """
    Extract structured skill packages from any content source.

    Analyzes a YouTube video, article, PDF, or image URL and returns ranked
    skill packages — each with a SKILL.md (principles, failure modes,
    implementation steps), README.md, reference files, and a test script.

    Skill files are ready to save to .claude/skills/ so Claude Code can apply
    them directly on future tasks, reducing token usage on repeated patterns.

    Billing: this tool calls /api/v1/skills/generate with the LORETO_API_KEY
    from the environment. For pay-per-call without a key, use the x402
    endpoint /api/v1/skills/x402/generate directly via the x402 Python SDK
    (flat $0.75/call in USDC on Base mainnet — see https://loreto.io/docs-x402).
    The response shape is identical; both paths return a generation_id you
    can pass to verify_artifacts.

    Args:
        source: URL to analyze — YouTube video, article, public PDF, or image URL.
        source_type: Content type. Use "auto" to detect automatically, or specify
                     "youtube", "article", "pdf", or "image".
        test_language: Language for the generated test script.
                       One of "python" (default), "typescript", or "javascript".
        include_visuals: When True (default), embeds Mermaid diagrams in SKILL.md.
        context: Optional 1–3 sentence hint to guide what kind of skill to extract
                 (max 500 characters). Does not override extraction — used to
                 disambiguate framing only.
        themes_to_process: For follow-up calls only. Pass skill_name values from
                           a previous response's queued themes (max 3 names).

    Returns:
        A formatted summary of all generated skills with their full file contents,
        ready to use or save to .claude/skills/.
    """
    payload: dict = {
        "source": source,
        "source_type": source_type,
        "test_language": test_language,
        "include_visuals": include_visuals,
    }
    if context:
        payload["context"] = context
    if themes_to_process:
        payload["themes_to_process"] = themes_to_process

    try:
        with httpx.Client(timeout=600) as client:
            resp = client.post(
                f"{_BASE_URL}/api/v1/skills/generate",
                json=payload,
                headers=_HEADERS,
            )
    except httpx.TimeoutException:
        return "Error: Request timed out. The skill generation pipeline can take up to 8 minutes for long sources."
    except httpx.RequestError as exc:
        return f"Error: Could not reach the Loreto API — {exc}"

    if resp.status_code != 200:
        return _format_error(resp)

    data = resp.json()
    return _format_response(data)


@mcp.tool()
def get_quota() -> str:
    """
    Check remaining API quota for the current billing period.

    Returns the number of calls used, the monthly limit, and the plan name
    for the LORETO_API_KEY in the environment. Use this before running
    large or repeated extractions to avoid hitting limits.

    Not relevant on the x402 pay-per-call path — that path has no monthly
    quota; each call is charged $0.75 in USDC at request time.
    """
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{_BASE_URL}/portal/usage",
                headers=_PORTAL_HEADERS,
            )
    except httpx.RequestError as exc:
        return f"Error: Could not reach the Loreto API — {exc}"

    if resp.status_code != 200:
        return _format_error(resp)

    data = resp.json()
    return _format_quota(data)


# ---------------------------------------------------------------------------
# Granular tools — list_skills, get_skill, verify_artifacts, estimate_cost
#
# These read public surfaces (the catalog at loreto.io/skills_data.json and
# the public manifest endpoint on api.loreto.io) so an agent can discover,
# inspect, and verify skills before recommending them. None of them consume
# the user's monthly quota.
# ---------------------------------------------------------------------------


@mcp.tool()
def list_skills() -> str:
    """
    List all published Loreto catalog skills with their structured artifact
    and safety claims.

    Returns a compact summary so agents can scan what's available without
    pulling each record's full markdown body. Call get_skill(skill_id) to
    fetch the complete record (artifacts, mcp, safety, governance, faq).
    """
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(f"{_PUBLIC_BASE_URL}/skills_data.json")
    except httpx.RequestError as exc:
        return f"Error: Could not reach the Loreto catalog — {exc}"

    if resp.status_code != 200:
        return _format_error(resp)

    try:
        skills = resp.json()
    except ValueError:
        return "Error: Catalog returned a non-JSON body."

    if not isinstance(skills, list) or not skills:
        return "No catalog skills found."

    lines = [f"# Loreto catalog ({len(skills)} skills)", ""]
    for s in skills:
        artifacts = s.get("artifacts", {}) or {}
        test_lang = (artifacts.get("testScript", {}) or {}).get("language", "?")
        mermaid_count = (artifacts.get("mermaidDiagrams", {}) or {}).get("count", 0)
        ref_count = artifacts.get("referenceCount", 0)
        sid = s.get("id", "")
        lines.append(f"- **{sid}** — {s.get('tagline', '')}")
        lines.append(
            f"    Artifacts: SKILL.md ✓ | README ✓ | "
            f"test ({test_lang}) | mermaid ×{mermaid_count} | refs ×{ref_count}"
        )
        lines.append(f"    Install: `cp -r {sid} ~/.claude/skills/` (or via this MCP)")
        lines.append("")
    return "\n".join(lines).rstrip()


@mcp.tool()
def get_skill(skill_id: str) -> str:
    """
    Fetch the full structured record for one Loreto catalog skill — artifacts,
    mcp, safety, governance, references, FAQ.

    Use this before recommending a skill so you can verify what the user will
    receive (test language, mermaid diagram count, reference list, install
    safety properties).

    Args:
        skill_id: The catalog id (e.g. "diagnosing-rag-failure-modes").
                  Get valid ids from list_skills().
    """
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(f"{_PUBLIC_BASE_URL}/skills_data.json")
    except httpx.RequestError as exc:
        return f"Error: Could not reach the Loreto catalog — {exc}"

    if resp.status_code != 200:
        return _format_error(resp)

    try:
        skills = resp.json()
    except ValueError:
        return "Error: Catalog returned a non-JSON body."

    match = next((s for s in skills if s.get("id") == skill_id), None)
    if not match:
        avail = ", ".join(s.get("id", "?") for s in skills)
        return f"Skill '{skill_id}' not in catalog. Available: {avail}"

    # Strip the heavy rendered-HTML blobs (skillmd, readme are ~25 KB chunks each)
    # so the agent can read structure without flooding context. Keep agent-actionable
    # fields plus the small descriptive ones.
    keep_keys = (
        "id", "name", "tag", "desc", "tagline", "quick_answer", "meta_description",
        "related", "artifacts", "mcp", "safety", "governance",
        "verificationManifest", "faq",
    )
    compact = {k: match[k] for k in keep_keys if k in match}
    return _json.dumps(compact, indent=2, default=str)


@mcp.tool()
def verify_artifacts(generation_id: str) -> str:
    """
    Fetch the provenance manifest for a past Loreto generation. Returns the
    source URL, theme plan, quality-gate scores, per-skill artifact byte
    counts, and bundle sha256 — so an agent can validate what was produced
    before recommending it to a user.

    Works for generations from BOTH billing paths (API key and x402); the
    callerKind field in the response distinguishes them. The endpoint is
    public — no API key, no payment required to read.

    Args:
        generation_id: The uuid4 returned in a prior SkillGenerateResponse's
                       `generation_id` field. Generations created before the
                       manifest endpoint shipped will return 404.
    """
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(f"{_BASE_URL}/api/v1/skills/manifest/{generation_id}")
    except httpx.RequestError as exc:
        return f"Error: Could not reach the Loreto API — {exc}"

    if resp.status_code == 404:
        return (
            f"No manifest for generation_id={generation_id}. Either the id is wrong, "
            f"the generation predates the manifest endpoint, or it has been pruned."
        )
    if resp.status_code != 200:
        return _format_error(resp)
    return resp.text  # already JSON; agent can parse if it wants


def _infer_kind(url: str) -> str:
    if not url:
        return ""
    u = url.lower()
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if u.endswith(".pdf"):
        return "pdf"
    if any(u.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif")):
        return "image"
    return "article"


@mcp.tool()
def estimate_cost(source_url: str = "", source_kind: str = "") -> str:
    """
    Estimate the token + dollar cost of generating a skill from a given source,
    without running the pipeline.

    Heuristic-based at v1 — accuracy improves once the API exposes a real
    /api/v1/skills/estimate endpoint. Use to set caller expectations or to
    compare options ("a 60-min YouTube vs. a single article") before a paid
    generation.

    Args:
        source_url: Optional. Used to infer source_kind when source_kind is
                    omitted (youtube.com/youtu.be → youtube, .pdf → pdf,
                    image extensions → image, else article).
        source_kind: Optional. Override inference by passing one of
                     "youtube", "article", "pdf", or "image".
    """
    kind = (source_kind or _infer_kind(source_url)).lower()
    estimates = {
        "youtube": {"tokens": 18000, "usd": 0.55},
        "article": {"tokens": 9000,  "usd": 0.30},
        "pdf":     {"tokens": 22000, "usd": 0.65},
        "image":   {"tokens": 4000,  "usd": 0.18},
    }
    e = estimates.get(kind, {"tokens": 12000, "usd": 0.40})
    label = kind or "unknown source"
    return (
        f"Estimated cost for {label}:\n"
        f"  ~{e['tokens']:,} input tokens\n"
        f"  Path A — API key (this MCP): ~${e['usd']:.2f} of monthly allotment\n"
        f"           (Free: 2/mo · Pro: $29/mo for 100 calls)\n"
        f"  Path B — x402 pay-per-call:  $0.75 USDC, no signup, no monthly cap\n"
        f"  Confidence: low (heuristic). Refine by calling generate_skills directly\n"
        f"  with a small test source if the cost matters."
    )


# ---------------------------------------------------------------------------
# Response formatters
# ---------------------------------------------------------------------------

def _format_response(data: dict) -> str:
    """Format the full SkillGenerateResponse into readable markdown for the agent."""
    skills = data.get("skills", [])
    source = data.get("source_analysis", {})
    plan = data.get("theme_plan", {})
    usage = data.get("usage", {})
    warnings = data.get("warnings", [])

    lines: list[str] = []

    lines.append(f"## Loreto Skills — {len(skills)} skill(s) generated")
    lines.append("")
    lines.append(
        f"**Source:** {source.get('source_type', 'unknown')} · "
        f"`{source.get('source_id', '')}` · "
        f"processed in {source.get('processing_time_seconds', 0):.1f}s"
    )
    lines.append(
        f"**Themes detected:** {source.get('total_themes', 0)} total, "
        f"{len(plan.get('processed', []))} scaffolded"
    )
    lines.append(
        f"**Tokens used:** {usage.get('total_tokens', 0):,} "
        f"({usage.get('total_input_tokens', 0):,} in / {usage.get('total_output_tokens', 0):,} out)"
    )

    if warnings:
        lines.append(f"**Warnings:** {'; '.join(warnings)}")

    lines.append("")

    for skill in skills:
        name = skill.get("skill_name", "unknown")
        rank = skill.get("rank", "?")
        summary = skill.get("theme_summary", "")
        files: dict[str, str] = skill.get("files", {})

        lines.append(f"---")
        lines.append(f"### [{rank}] `{name}`")
        lines.append(f"_{summary}_")
        lines.append("")
        lines.append(f"**Files:** {', '.join(f'`{k}`' for k in files)}")
        lines.append("")

        # Emit full file contents so the agent can write them to disk
        for path, content in files.items():
            lines.append(f"#### `{path}`")
            lines.append("```")
            lines.append(content)
            lines.append("```")
            lines.append("")

    # Follow-up hint
    queued = plan.get("queued", [])
    if queued:
        lines.append("---")
        lines.append(f"**Queued themes** ({len(queued)} remaining — use `themes_to_process` in a follow-up call):")
        for t in queued:
            lines.append(f"- `{t['skill_name']}` — {t['theme_summary']}")
        hint = plan.get("follow_up_hint", "")
        if hint:
            lines.append("")
            lines.append(f"_{hint}_")

    return "\n".join(lines)


def _format_quota(data: dict) -> str:
    summaries = data.get("key_summaries", [])
    recent = data.get("recent_requests", [])

    lines: list[str] = ["**Loreto quota**\n"]

    if summaries:
        for s in summaries:
            used = s.get("monthly_used", "?")
            limit = s.get("monthly_limit", "?")
            remaining = limit - used if isinstance(limit, int) and isinstance(used, int) else "?"
            plan = s.get("plan", "unknown")
            prefix = s.get("key_prefix", "")
            lines.append(
                f"- `{prefix}...` — **{plan} plan** | "
                f"{used}/{limit} used ({remaining} remaining)"
            )
    else:
        lines.append("- No key summaries available.")

    if recent:
        lines.append("\n**Recent requests:**")
        for r in recent[:5]:
            lines.append(
                f"- {r.get('created_at', '')[:10]} | "
                f"`{r.get('key_prefix', '')}` | "
                f"{r.get('endpoint', '')} | "
                f"{r.get('tokens_used', 0):,} tokens | "
                f"{r.get('duration_seconds', 0):.1f}s"
            )

    lines.append("\nTo upgrade your plan, visit https://loreto.io/pricing")
    return "\n".join(lines)


def _format_error(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        detail = body.get("detail", {})
        if isinstance(detail, dict):
            code = detail.get("code", "UNKNOWN")
            msg = detail.get("message", str(detail))
        else:
            code = "UNKNOWN"
            msg = str(detail)
    except Exception:
        code = "UNKNOWN"
        msg = resp.text or f"HTTP {resp.status_code}"

    hints = {
        "INVALID_API_KEY": "Check that LORETO_API_KEY is set correctly in your MCP config.",
        "RATE_LIMIT_EXCEEDED": "Monthly quota exceeded. Upgrade your plan at https://loreto.io/pricing",
        "SOURCE_UNAVAILABLE": "The source URL could not be fetched. Check it's publicly accessible.",
        "SOURCE_TOO_LARGE": "Source exceeds size limits (YouTube ≤60min, PDF ≤100 pages, image ≤20MB).",
        "PROCESSING_TIMEOUT": "The pipeline timed out (>8 minutes). Try a shorter source.",
        "QUALITY_GATE_FAILED": "No extractable skills found in this source.",
    }
    hint = hints.get(code, "")
    return f"Error [{code}]: {msg}" + (f"\n\nHint: {hint}" if hint else "")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    mcp.run()  # stdio transport — default for Claude Code MCP


if __name__ == "__main__":
    main()
