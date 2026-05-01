"""
Basic integration tests for loreto-mcp server tools.

Run with:
    LORETO_API_KEY=lor_... python tests/test_server.py
"""

import os
import sys

# Verify API key is set before importing server (it reads env at module load)
if not os.environ.get("LORETO_API_KEY"):
    print("ERROR: Set LORETO_API_KEY before running tests.")
    sys.exit(1)

# Import after env is confirmed set. The .tool() decorator wraps each function
# in a FunctionTool object; tests can either go through the wrapper or call
# the underlying .fn — we hit the wrapped form for parity with how MCP clients
# invoke them, falling back to .fn when a wrapper isn't applied to plain helpers.
from loreto_mcp.server import (
    get_quota,
    generate_skills,
    list_skills,
    get_skill,
    verify_artifacts,
    estimate_cost,
    _infer_kind,
)


def _call(tool, **kwargs):
    """FastMCP wraps decorated tools; some versions expose .fn for the raw
    callable. Try direct call first, fall back to .fn."""
    if callable(tool):
        try:
            return tool(**kwargs) if kwargs else tool()
        except TypeError:
            pass
    fn = getattr(tool, "fn", None)
    if fn is not None:
        return fn(**kwargs) if kwargs else fn()
    raise RuntimeError(f"Cannot invoke tool {tool!r}")


def test_get_quota():
    print("\n── test_get_quota ───────────────────────────────────")
    result = _call(get_quota)
    print(result)
    assert "plan" in result.lower(), "Expected plan info in quota response"
    assert "Error" not in result, f"Unexpected error: {result}"
    print("PASS")


def test_generate_skills():
    print("\n── test_generate_skills ─────────────────────────────")
    result = _call(
        generate_skills,
        source="https://www.youtube.com/watch?v=JYcidOS9ozU",
        source_type="youtube",
        test_language="python",
        include_visuals=False,
    )
    print(result[:800], "..." if len(result) > 800 else "")

    # Connection/auth errors = hard failure (MCP transport broken)
    hard_errors = ["Could not reach", "INVALID_API_KEY", "timed out"]
    for err in hard_errors:
        assert err not in result, f"Hard transport error: {result[:200]}"

    # Quality gate / content failures are acceptable — API responded correctly
    if "QUALITY_GATE_FAILED" in result or "Loreto Skills" in result:
        print("PASS (API reachable — content quality gate or skills returned)")
    else:
        assert "skill" in result.lower(), f"Unexpected response: {result[:200]}"
        print("PASS")


def test_list_skills():
    print("\n── test_list_skills ─────────────────────────────────")
    result = _call(list_skills)
    print(result[:400], "..." if len(result) > 400 else "")
    assert "Loreto catalog" in result, f"Expected catalog header: {result[:200]}"
    assert "diagnosing-rag-failure-modes" in result, "Expected at least one known skill id"
    assert "Error" not in result, f"Unexpected error: {result[:200]}"
    print("PASS")


def test_get_skill_known():
    print("\n── test_get_skill_known ─────────────────────────────")
    result = _call(get_skill, skill_id="diagnosing-rag-failure-modes")
    print(result[:300], "..." if len(result) > 300 else "")
    # Should be JSON with structural fields, not the heavy rendered HTML
    assert '"artifacts"' in result, "Expected artifacts in record"
    assert '"mermaidDiagrams"' in result or '"mermaid_diagrams"' in result, \
        "Expected mermaidDiagrams field"
    assert "<html" not in result.lower(), "Heavy HTML should be stripped"
    print("PASS")


def test_get_skill_unknown():
    print("\n── test_get_skill_unknown ───────────────────────────")
    result = _call(get_skill, skill_id="does-not-exist-xyz")
    print(result[:200])
    assert "not in catalog" in result, f"Expected 'not in catalog' message: {result[:200]}"
    print("PASS")


def test_verify_artifacts_404():
    print("\n── test_verify_artifacts_404 ────────────────────────")
    result = _call(verify_artifacts, generation_id="00000000-0000-0000-0000-000000000000")
    print(result[:200])
    assert ("No manifest" in result) or ("Error" in result), \
        f"Expected 404 message or error: {result[:200]}"
    print("PASS")


def test_estimate_cost_youtube():
    print("\n── test_estimate_cost_youtube ───────────────────────")
    result = _call(estimate_cost, source_url="https://youtu.be/EXAMPLE")
    print(result)
    assert "youtube" in result.lower(), "Expected kind inference"
    assert "$" in result, "Expected dollar estimate"
    assert "tokens" in result.lower(), "Expected token estimate"
    print("PASS")


def test_estimate_cost_kind_override():
    print("\n── test_estimate_cost_kind_override ─────────────────")
    result = _call(estimate_cost, source_kind="pdf")
    print(result)
    assert "pdf" in result.lower(), "Expected pdf kind"
    print("PASS")


def test_infer_kind():
    print("\n── test_infer_kind ──────────────────────────────────")
    cases = [
        ("https://www.youtube.com/watch?v=abc", "youtube"),
        ("https://youtu.be/EXAMPLE", "youtube"),
        ("https://example.com/whitepaper.pdf", "pdf"),
        ("https://example.com/photo.PNG", "image"),
        ("https://nytimes.com/article", "article"),
        ("", ""),
    ]
    for url, want in cases:
        got = _infer_kind(url)
        assert got == want, f"_infer_kind({url!r}) = {got!r}, want {want!r}"
        print(f"  ✓ {url or '(empty)'} → {want!r}")
    print("PASS")


if __name__ == "__main__":
    tests = [
        test_get_quota,
        test_generate_skills,
        test_list_skills,
        test_get_skill_known,
        test_get_skill_unknown,
        test_verify_artifacts_404,
        test_estimate_cost_youtube,
        test_estimate_cost_kind_override,
        test_infer_kind,
    ]
    passed = 0
    failed = 0

    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {e}")
            failed += 1

    print(f"\n{'─'*50}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
