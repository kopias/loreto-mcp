"""
Offline tests for loreto-mcp: the install rules, and the read -> buy -> install
flow against a stand-in for loreto.io. No network, no API key.

Run with:  python -m pytest tests  (or python tests/test_server.py)
"""
import io
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

os.environ["LORETO_STATE"] = os.path.join(tempfile.mkdtemp(), "mcp.json")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loreto_mcp import server  # noqa: E402

fn = lambda t: getattr(t, "fn", t)  # FastMCP wraps tools; call the function underneath
server.WAIT.update({"read": 1, "write": 1, "poll": 0})


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for k, v in files.items():
            z.writestr(k, v)
    return buf.getvalue()


def test_repo_url():
    assert server._repo_url("github.com/acme/w") == "https://github.com/acme/w"
    assert server._repo_url("acme/w.git") == "https://github.com/acme/w"
    assert server._repo_url("https://github.com/acme/w/tree/main") == "https://github.com/acme/w"
    assert server._repo_url("not a repo") is None


def test_install_keeps_your_root_file_and_never_escapes():
    root = Path(tempfile.mkdtemp())
    (root / "CLAUDE.md").write_text("# ours\nKeep this.\n")
    (root / "README.md").write_text("our readme\n")
    data = make_zip({"CLAUDE.md": "rules v1\n", "README.md": "loreto readme", "evidence.json": "{}",
                     ".claude/skills/w-conventions/SKILL.md": "skill", "../escape.md": "no"})
    out = server.install_zip(data, "claude-code", "acme/w", root)
    text = (root / "CLAUDE.md").read_text()
    assert text.startswith("# ours") and "Keep this." in text and "rules v1" in text
    assert (root / "README.md").read_text() == "our readme\n"                     # never clobbered
    assert (root / ".loreto/w-conventions/README.md").read_text() == "loreto readme"
    assert (root / ".claude/skills/w-conventions/SKILL.md").read_text() == "skill"
    assert not (root.parent / "escape.md").exists()
    assert any("kept yours" in o for o in out)
    # installing again replaces only the Loreto section
    server.install_zip(make_zip({"CLAUDE.md": "rules v2\n"}), "claude-code", "acme/w", root)
    text = (root / "CLAUDE.md").read_text()
    assert "rules v2" in text and "rules v1" not in text and text.count(server.START) == 1


def test_hermes_skills_go_to_hermes_home():
    root, home = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
    os.environ["HERMES_HOME"] = str(home)
    server.install_zip(make_zip({"skills/w-conventions/SKILL.md": "h", "AGENTS.md": "a"}), "hermes", "acme/w", root)
    assert (home / "skills/w-conventions/SKILL.md").read_text() == "h"
    assert "a" in (root / "AGENTS.md").read_text()


class R:
    def __init__(self, code, body=None, content=b""):
        self.status_code, self._b, self.content = code, body, content
        self.text = json.dumps(body) if body is not None else ""

    def json(self):
        return self._b


def test_read_buy_install_flow(monkeypatch=None):
    paid = {"done": False}
    zipdata = make_zip({"CLAUDE.md": "rules\n", ".claude/skills/w-conventions/SKILL.md": "s"})

    def post(url, json=None, headers=None, timeout=None):
        if url.endswith("/explore/pass"):
            return R(200, {"pass": "gp"})
        if url.endswith("/timeline/explore"):
            assert headers.get("X-Guest-Pass") == "gp"
            return R(200, {"id": "x1", "status": "running"})
        if url.endswith("/grain/preview"):
            return R(200, {"commits_read": 400, "bundle_cents": 500, "file_cents": 200, "chats_per_purchase": 25,
                           "insights": [{"title": "What moves together", "line": "a and b changed together 17 times."}],
                           "items": [{"key": "root", "path": "CLAUDE.md", "what": "the root file"}]})
        if url.endswith("/grain/checkout"):
            assert json == {"harness": "claude-code", "items": []}
            return R(200, {"url": "https://checkout.stripe.com/x", "cents": 500, "session_id": "cs_1"})
        if url.endswith("/grain/claim"):
            if not paid["done"]:
                return R(402, {"detail": "not paid"})
            return R(200, {"id": "g1", "xid": "x1", "key": "k1", "full_name": "acme/w"})
        raise AssertionError(url)

    def get(url, headers=None, timeout=None):
        if url.endswith("/explore/x1"):
            return R(200, {"id": "x1", "status": "done"})
        if url.endswith("/grain/g1"):
            assert headers.get("X-Grain-Key") == "k1"
            return R(200, {"status": "done", "xid": "x1", "harness": "claude-code", "harness_name": "Claude Code",
                           "full_name": "acme/w", "download": "/api/timeline/explore/x1/grain/g1/download", "complete_cents": 0})
        if url.endswith("/download"):
            return R(200, content=zipdata)
        raise AssertionError(url)

    server.httpx.post, server.httpx.get = post, get
    out = fn(server.read_repo)("github.com/acme/w")
    assert "read_id: x1" in out and "17 times" in out and "$5" in out
    out = fn(server.buy_harness)()
    assert "https://checkout.stripe.com/x" in out
    repo = Path(tempfile.mkdtemp())
    assert "Not paid yet" in fn(server.get_harness)(str(repo))
    paid["done"] = True
    out = fn(server.get_harness)(str(repo))
    assert "Armed Claude Code" in out, out
    assert (repo / ".claude/skills/w-conventions/SKILL.md").read_text() == "s"
    # the purchase is remembered: installing again needs no new checkout
    assert "Armed" in fn(server.get_harness)(str(Path(tempfile.mkdtemp())))


if __name__ == "__main__":
    for name, f in list(globals().items()):
        if name.startswith("test_"):
            f()
            print("ok", name)
