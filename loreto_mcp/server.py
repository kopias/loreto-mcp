"""
Loreto MCP Server

Exposes Loreto skill generation as MCP tools so AI coding agents
(Claude Code, Codex, OpenCode) can call generate_skills directly.

Required environment variable:
    LORETO_API_KEY  —  your Loreto API key (lor_...)

Optional:
    LORETO_BASE_URL —  override the API base URL (default: https://api.loreto.io)

Usage (stdio transport, for Claude Code):
    uvx loreto-mcp
    # or: python -m loreto_mcp.server
"""

from __future__ import annotations

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

        Use generate_skills to extract reusable knowledge from YouTube videos,
        articles, PDFs, or images. The returned skill files can be saved to
        .claude/skills/ so Claude Code can apply them on future tasks.

        Use get_quota to check how many API calls remain before running
        long or repeated extractions.
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

    Returns the number of calls used, the monthly limit, and the plan name.
    Use this before running large or repeated extractions to avoid hitting limits.
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
        "RATE_LIMITED": "Monthly quota exceeded. Upgrade your plan at https://loreto.io/pricing",
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
