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

# Import after env is confirmed set
from loreto_mcp.server import get_quota, generate_skills


def test_get_quota():
    print("\n── test_get_quota ───────────────────────────────────")
    result = get_quota()
    print(result)
    assert "plan" in result.lower(), "Expected plan info in quota response"
    assert "Error" not in result, f"Unexpected error: {result}"
    print("PASS")


def test_generate_skills():
    print("\n── test_generate_skills ─────────────────────────────")
    result = generate_skills(
        source="https://www.youtube.com/watch?v=HodCjnGv8Ag",
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


if __name__ == "__main__":
    tests = [test_get_quota, test_generate_skills]
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
