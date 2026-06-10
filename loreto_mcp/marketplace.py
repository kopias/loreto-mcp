"""
Loreto Marketplace tools
========================

A second, distinct product surface exposed through the same MCP server as the
Skills *Generator*. Where the generator turns a URL/PDF into brand-new skills,
the **marketplace** lets an agent publish, discover, and buy skill packages that
people have already listed at loreto.io.

The two products talk to two different hosts:

  • Generator  → https://api.loreto.io      (LORETO_BASE_URL)
  • Marketplace → https://loreto.io/api      (LORETO_MARKETPLACE_BASE)

Both authenticate with the *same* Loreto API key (LORETO_API_KEY, `lor_...`).
The marketplace REST API accepts it as a Bearer token.

Tools registered here (all prefixed `marketplace_` so they never collide with the
generator's catalog `list_skills` / `get_skill`):

  • marketplace_publish      — publish (or draft) a skill package for sale
  • marketplace_search       — browse / search every listed skill (public)
  • marketplace_get_listing  — full detail for one skill by slug
  • marketplace_my_metrics   — your seller metrics (sales, downloads, earnings)
  • marketplace_my_listings  — your own listings (published + drafts)
  • marketplace_library      — skills you own (free + purchased)
  • marketplace_purchase     — acquire a free skill, or get the Stripe / x402
                               payment options for a paid one
"""

from __future__ import annotations

import os
from typing import Optional

import httpx

# Same key as the generator; the marketplace REST API takes it as a Bearer token.
_API_KEY = os.environ.get("LORETO_API_KEY", "")
_MKT_BASE = os.environ.get("LORETO_MARKETPLACE_BASE", "https://loreto.io/api").rstrip("/")


def _auth() -> dict:
    return {"Authorization": f"Bearer {_API_KEY}"}


def _request(method: str, path: str, *, auth: bool = False, json_body=None, params=None) -> dict:
    headers = {"Content-Type": "application/json"}
    if auth:
        headers.update(_auth())
    try:
        with httpx.Client(timeout=140) as client:
            r = client.request(method, f"{_MKT_BASE}{path}", headers=headers,
                               json=json_body, params=params)
    except Exception as e:  # noqa: BLE001 — surface any transport error to the agent
        return {"error": f"Could not reach the Loreto marketplace: {type(e).__name__}: {e}"}
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail", "")
        except Exception:  # noqa: BLE001
            detail = r.text[:300]
        return {"error": f"HTTP {r.status_code}: {detail}"}
    try:
        return r.json()
    except Exception:  # noqa: BLE001
        return {"error": "Non-JSON response from the Loreto marketplace."}


def register(mcp) -> None:
    """Attach the marketplace tools to an existing FastMCP instance."""

    # ── Publish ────────────────────────────────────────────────────────────
    @mcp.tool()
    def marketplace_publish(
        title: str,
        summary: str = "",
        description: str = "",
        files: Optional[dict] = None,
        skill_md: Optional[str] = None,
        readme_md: Optional[str] = None,
        price_usd: float = 0.0,
        category: str = "general",
        tags: Optional[list] = None,
        invocations: Optional[list] = None,
        publish: bool = True,
    ) -> dict:
        """Publish a skill package to the Loreto marketplace (programmatic listing).

        Provide the package either as `files` (a dict of {relative_path: text},
        e.g. {"SKILL.md": "...", "README.md": "..."}) or as `skill_md` (+ optional
        `readme_md`). `description` is the public "About this skill" text shown to
        buyers when the package has no README. `price_usd` of 0 lists it free.
        Set `publish=False` to save a private draft you can finish later.

        Every upload is scanned for malicious content (prompt injection, secrets,
        destructive code) before it goes live; if it fails the scan this returns an
        error explaining why, and nothing is published. Duplicate/near-duplicate
        packages of an existing listing are also rejected.

        Requires LORETO_API_KEY. This is the *marketplace* — to instead generate a
        brand-new skill from a URL/PDF, use generate_skills.
        """
        pkg = dict(files or {})
        if skill_md:
            pkg.setdefault("SKILL.md", skill_md)
        if readme_md:
            pkg.setdefault("README.md", readme_md)
        if not pkg:
            return {"error": "Provide `files` (path→content) or `skill_md`."}
        body = {
            "title": title,
            "summary": summary,
            "description": description,
            "price_usd": float(price_usd or 0),
            "category": category,
            "tags": tags or [],
            "invocations": invocations or [],
            "status": "published" if publish else "draft",
            "source": {"kind": "paste", "files": pkg},
        }
        return _request("POST", "/portal/marketplace/listings", auth=True, json_body=body)

    # ── Browse ─────────────────────────────────────────────────────────────
    @mcp.tool()
    def marketplace_search(query: str = "", category: str = "", price: str = "",
                           sort: str = "downloads", page: int = 1) -> dict:
        """Search the marketplace for skills others have listed.

        `price` can be 'free' or 'paid'; `sort` is one of
        downloads|rating|newest|price. Returns cards (title, summary, price, seller,
        ratings, downloads, slug) — public, no API key or purchase needed to browse.
        Distinct from the generator's catalog list_skills.
        """
        params = {"q": query or None, "category": category or None, "price": price or None,
                  "sort": sort or None, "page": page}
        return _request("GET", "/marketplace/listings",
                        params={k: v for k, v in params.items() if v is not None})

    @mcp.tool()
    def marketplace_get_listing(slug: str) -> dict:
        """Full detail for one marketplace skill by slug: description, README, file
        manifest, price, reviews. The full package contents (SKILL.md, references,
        tests) are included only if you own or have purchased it; otherwise they're
        locked — buy it first with marketplace_purchase.
        """
        return _request("GET", f"/marketplace/listings/{slug}", auth=True)

    # ── Seller insight ─────────────────────────────────────────────────────
    @mcp.tool()
    def marketplace_my_metrics() -> dict:
        """Your seller metrics: total sales, downloads, skills listed, gross/net
        earnings, platform fee, and Stripe payout status. Requires LORETO_API_KEY."""
        return _request("GET", "/portal/marketplace/metrics", auth=True)

    @mcp.tool()
    def marketplace_my_listings() -> dict:
        """Your own marketplace listings (published + drafts) with their counts.
        Requires LORETO_API_KEY."""
        return _request("GET", "/portal/marketplace/my-listings", auth=True)

    @mcp.tool()
    def marketplace_library() -> dict:
        """Skills you own — free ones you've acquired and paid ones you've purchased.
        Use marketplace_get_listing to read the full package of anything in here.
        Requires LORETO_API_KEY."""
        return _request("GET", "/portal/marketplace/library", auth=True)

    # ── Acquire / purchase ─────────────────────────────────────────────────
    def _x402_challenge(listing_id: str) -> Optional[dict]:
        """Fetch the x402 (USDC) payment requirements for a paid listing — the HTTP
        402 challenge a wallet-holding agent would sign and pay against."""
        try:
            with httpx.Client(timeout=30) as client:
                r = client.post(
                    f"{_MKT_BASE}/portal/marketplace/listings/{listing_id}/x402/purchase",
                    headers=_auth(),
                )
            if r.status_code == 402:
                return r.json()
        except Exception:  # noqa: BLE001
            return None
        return None

    @mcp.tool()
    def marketplace_purchase(slug: str) -> dict:
        """Acquire a marketplace skill.

        Free skills are granted instantly (then use marketplace_get_listing to read
        the full package). For paid skills this returns a Stripe Checkout URL to pay
        by card now, plus an `x402` field carrying the agent-native USDC payment
        requirements (the HTTP 402 challenge) for wallet-holding agents — sign those
        requirements and re-POST with an `X-PAYMENT` header to settle on-chain and
        unlock the skill. The challenge's `network`/`asset`/`payTo` fields state the
        exact chain and token to pay. Requires LORETO_API_KEY.
        """
        detail = _request("GET", f"/marketplace/listings/{slug}", auth=True)
        if "error" in detail:
            return detail
        listing_id = detail.get("id")
        if not listing_id:
            return {"error": "Skill not found."}
        if detail.get("owned"):
            return {"owned": True,
                    "message": "You already own this skill — use marketplace_get_listing to read it."}
        res = _request("POST", f"/portal/marketplace/listings/{listing_id}/purchase", auth=True)
        if "error" in res:
            return res
        if res.get("status") in ("free", "paid") and res.get("owned"):
            return {"owned": True, "status": res.get("status"),
                    "message": "Acquired. Use marketplace_get_listing to read the full package."}
        out: dict = {"owned": False}
        if res.get("checkout_url"):
            out["checkout_url"] = res["checkout_url"]
            out["message"] = "Open checkout_url to pay by card, then re-run marketplace_get_listing."
        x402 = _x402_challenge(listing_id)
        if x402:
            out["x402"] = x402
            out["x402_note"] = (
                "Agent-native USDC payment (HTTP 402). Sign these requirements with your "
                "wallet (EIP-3009 transferWithAuthorization) and re-POST to the same "
                "endpoint with an X-PAYMENT header to settle on-chain and unlock the skill; "
                "the network/asset/payTo fields say exactly what to pay. Or use checkout_url "
                "to pay with a card."
            )
        return out
