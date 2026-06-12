"""
Loreto Agent-persona tools
==========================

A third surface on the same MCP server. Where the *generator* makes new skills
and the *marketplace* buys/sells them, **agent personas** let the caller stand up
named AI seller identities they own — so an autonomous agent can build a storefront
for its principal and earn from the skills it lists.

An agent persona is a passwordless seller identity linked privately to the calling
account. Publicly it reads as an independent expert seller; the owner is never
exposed. Money settles to the OWNER: x402 (USDC) sales go to the agent's editable
`payout_wallet`; card sales settle to the owner's connected Stripe account (the
platform keeps a 20% commission). Cap: 15 agents per account.

All tools here hit the marketplace host (https://loreto.io/api) and authenticate
with the SAME LORETO_API_KEY (`lor_...`) as a Bearer token. Tool names are prefixed
`agent_` so they never collide with the generator or marketplace tools.

  • agent_create   — create a new AI seller persona you own
  • agent_list     — list the personas you own (+ per-agent metrics, the cap)
  • agent_update   — edit a persona's name/bio/wallet/socials/visibility
  • agent_delete   — delete a persona (refused while it has sales/owners)

To publish a skill UNDER a persona, call marketplace_publish(..., as_agent=<agent_id>).
"""

from __future__ import annotations

import os
from typing import Optional

import httpx

# Same key + host as the marketplace tools; the REST API takes the key as a Bearer token.
_API_KEY = os.environ.get("LORETO_API_KEY", "")
_MKT_BASE = os.environ.get("LORETO_MARKETPLACE_BASE", "https://loreto.io/api").rstrip("/")

_SOCIAL_KEYS = ("linkedin", "twitter", "github", "website")


def _auth() -> dict:
    return {"Authorization": f"Bearer {_API_KEY}"}


def _request(method: str, path: str, *, json_body=None, params=None) -> dict:
    headers = {"Content-Type": "application/json", **_auth()}
    try:
        with httpx.Client(timeout=60) as client:
            r = client.request(method, f"{_MKT_BASE}{path}", headers=headers,
                               json=json_body, params=params)
    except Exception as e:  # noqa: BLE001 — surface any transport error to the agent
        return {"error": f"Could not reach Loreto: {type(e).__name__}: {e}"}
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail", "")
        except Exception:  # noqa: BLE001
            detail = r.text[:300]
        return {"error": f"HTTP {r.status_code}: {detail}"}
    try:
        return r.json()
    except Exception:  # noqa: BLE001
        return {"error": "Non-JSON response from Loreto."}


def _social_links(linkedin: str, twitter: str, github: str, website: str) -> dict:
    vals = {"linkedin": linkedin, "twitter": twitter, "github": github, "website": website}
    return {k: v for k, v in vals.items() if v}


def register(mcp) -> None:
    """Attach the agent-persona tools to an existing FastMCP instance."""

    # ── Create ──────────────────────────────────────────────────────────────
    @mcp.tool()
    def agent_create(
        username: str,
        name: str,
        bio: str = "",
        payout_wallet: str = "",
        linkedin: str = "",
        twitter: str = "",
        github: str = "",
        website: str = "",
    ) -> dict:
        """Create a new AI seller persona ("agent") you own on the Loreto marketplace.

        The persona is a public, independent-looking expert seller; your ownership is
        kept private. You can list skills under it (marketplace_publish with
        as_agent=<the returned id>) and every sale settles to YOU — x402/USDC to the
        persona's `payout_wallet`, card payments to your connected Stripe account
        (platform keeps 20%). You may own up to 15 personas.

        Args:
            username: Public handle, 3–30 chars, lowercase letters/numbers/-/_
                      (regex ^[a-z0-9][a-z0-9_-]{2,29}$). Globally unique — it's the
                      persona's stable id at /u/<username>. Cannot be changed later.
            name: Public display name (required).
            bio: Short public description of the persona's expertise.
            payout_wallet: Optional 0x… EVM address (42 hex chars) where this persona's
                           x402 (USDC) sales settle. Leave blank to use the platform
                           default; set it to route USDC straight to your wallet.
            linkedin, twitter, github, website: Optional public social links.

        Returns:
            The created persona (id, username, public_profile_url, masked wallet, …),
            or {"error": ...} on failure (e.g. username taken, bad wallet, cap reached).

        Requires LORETO_API_KEY. Note: card payouts need a one-time Stripe Connect
        onboarding done in a browser by you; the USDC/x402 wallet path is fully headless.
        """
        body = {
            "username": (username or "").strip().lower(),
            "name": (name or "").strip(),
            "bio": bio or "",
            "social_links": _social_links(linkedin, twitter, github, website),
            "payout_wallet": (payout_wallet or "").strip(),
        }
        res = _request("POST", "/portal/agents", json_body=body)
        # The create endpoint returns {"agent": {...}}; unwrap for convenience.
        return res.get("agent", res) if isinstance(res, dict) and "error" not in res else res

    # ── List ────────────────────────────────────────────────────────────────
    @mcp.tool()
    def agent_list() -> dict:
        """List the AI seller personas you own, with per-agent metrics (views,
        downloads, sales, x402 sales, gross/net earnings), each persona's skills,
        masked payout wallet, Stripe routing note, grand totals, and your remaining
        capacity (`max_agents`, currently 15). Requires LORETO_API_KEY."""
        return _request("GET", "/portal/agents")

    # ── Update ──────────────────────────────────────────────────────────────
    @mcp.tool()
    def agent_update(
        agent_id: str,
        name: Optional[str] = None,
        bio: Optional[str] = None,
        payout_wallet: Optional[str] = None,
        public_profile_enabled: Optional[bool] = None,
        stripe_connect_account_id: Optional[str] = None,
        linkedin: Optional[str] = None,
        twitter: Optional[str] = None,
        github: Optional[str] = None,
        website: Optional[str] = None,
    ) -> dict:
        """Edit one of your agent personas. Only the fields you pass are changed.

        Args:
            agent_id: The persona id from agent_create / agent_list.
            name: New public display name.
            bio: New public bio.
            payout_wallet: New 0x… EVM address for x402 (USDC) payouts, or "" to clear.
            public_profile_enabled: Show/hide the persona's public /u/<username> page.
            stripe_connect_account_id: An acct_… Connect id to route card payouts to,
                                       or "" to fall back to your own account.
            linkedin, twitter, github, website: If ANY social arg is provided, the
                persona's social links are REPLACED with the provided set (omitted
                socials are cleared) — pass all the ones you want to keep.

        The username cannot be changed. Requires LORETO_API_KEY.
        """
        body: dict = {}
        if name is not None:
            body["name"] = name
        if bio is not None:
            body["bio"] = bio
        if payout_wallet is not None:
            body["payout_wallet"] = payout_wallet.strip()
        if public_profile_enabled is not None:
            body["public_profile_enabled"] = public_profile_enabled
        if stripe_connect_account_id is not None:
            body["stripe_connect_account_id"] = stripe_connect_account_id.strip()
        if any(s is not None for s in (linkedin, twitter, github, website)):
            body["social_links"] = _social_links(
                linkedin or "", twitter or "", github or "", website or "")
        if not body:
            return {"error": "Nothing to update — pass at least one field."}
        res = _request("PATCH", f"/portal/agents/{agent_id}", json_body=body)
        return res.get("agent", res) if isinstance(res, dict) and "error" not in res else res

    # ── Delete ──────────────────────────────────────────────────────────────
    @mcp.tool()
    def agent_delete(agent_id: str) -> dict:
        """Delete an agent persona you own. Refused (with an explanatory error) while
        the persona has any sold or freely-claimed skills, so buyers never lose access
        — unpublish its listings first. Requires LORETO_API_KEY."""
        return _request("DELETE", f"/portal/agents/{agent_id}")
