#!/usr/bin/env python3
"""Check a deployed google-rss-mcp instance and its Smithery listing.

Run after every deploy. A push to main redeploys the public instance, and the
failures worth catching are not crashes — the server comes up fine while
answering in the wrong locale, exposing a tool list that no longer matches what
the registry cached, or blocking the crawler that keeps the listing alive.

    python3 scripts/verify_deploy.py
    python3 scripts/verify_deploy.py --origin https://staging.example.com/mcp
    python3 scripts/verify_deploy.py --skip-smithery

Standard library only, so it runs against a deployment from anywhere without
installing the project. Exits non-zero if any check fails.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

DEFAULT_ORIGIN = "https://google-rss-mcp-production.up.railway.app/mcp"
DEFAULT_NAMESPACE = "ccw7463"
DEFAULT_SERVER = "google-rss-mcp"
REGISTRY_ROOT = "https://registry.smithery.ai/servers"

EXPECTED_TOOLS = {"search_news", "get_top_headlines", "read_article"}
PROTOCOL_VERSION = "2025-06-18"

# Cloudflare fronts the Smithery gateway and rejects the default
# "Python-urllib/3.x" agent with error 1010, which looks exactly like the
# server being down. Anything else is let through.
USER_AGENT = "google-rss-mcp-verify/1.0"


class Checks:
    """Accumulates pass/fail results and prints them as they happen."""

    def __init__(self, color: bool) -> None:
        self.passed = 0
        self.failed = 0
        self._ok = "\033[32m✓\033[0m" if color else "PASS"
        self._no = "\033[31m✗\033[0m" if color else "FAIL"
        self._bold = (lambda s: f"\033[1m{s}\033[0m") if color else (lambda s: s)

    def section(self, title: str) -> None:
        print(f"\n{self._bold(title)}")

    def record(self, label: str, passed: bool, detail: str = "") -> bool:
        """Record one check.

        Args:
            label: What was checked.
            passed: Whether it held.
            detail: Extra context, shown after the label.

        Returns:
            ``passed``, so callers can branch on it.
        """
        mark = self._ok if passed else self._no
        suffix = f"  {detail}" if detail else ""
        print(f"  {mark} {label}{suffix}")
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        return passed


def _get_json(url: str, timeout: float = 30.0) -> Any:
    """GET a URL and decode JSON."""
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def _rpc(
    origin: str,
    method: str,
    params: Optional[Dict[str, Any]] = None,
    user_agent: str = USER_AGENT,
    timeout: float = 45.0,
) -> Tuple[Dict[str, Any], float]:
    """Send one JSON-RPC call over Streamable HTTP.

    Args:
        origin: The server's ``/mcp`` endpoint.
        method: JSON-RPC method name.
        params: Method parameters.
        user_agent: Agent to send, so crawler behavior can be checked.
        timeout: Seconds to wait.

    Returns:
        The decoded envelope and the round trip in milliseconds.
    """
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    ).encode()
    request = urllib.request.Request(
        origin,
        body,
        {
            "Content-Type": "application/json",
            # The server may answer as SSE, so both are accepted and the
            # response is unwrapped below.
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL_VERSION,
            "User-Agent": user_agent,
        },
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode()
    elapsed_ms = (time.perf_counter() - started) * 1000

    for line in raw.splitlines():
        payload = line[6:] if line.startswith("data: ") else line
        if not payload.strip():
            continue
        try:
            envelope = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if "result" in envelope or "error" in envelope:
            return envelope, elapsed_ms
    return {}, elapsed_ms


def _call_tool(
    origin: str, name: str, arguments: Dict[str, Any]
) -> Tuple[Dict[str, Any], float]:
    """Call one tool and decode its JSON result.

    Raises:
        ValueError: If the server returned an error instead of a result.
    """
    envelope, elapsed_ms = _rpc(
        origin, "tools/call", {"name": name, "arguments": arguments}
    )
    if "error" in envelope:
        raise ValueError(envelope["error"].get("message", "unknown error"))
    blocks = envelope.get("result", {}).get("content", [])
    text = blocks[0].get("text", "") if blocks else ""
    return json.loads(text), elapsed_ms


def _unstripped(articles) -> list:
    """Return articles whose title still carries the ' - Publisher' suffix."""
    return [
        a
        for a in articles
        if a.get("source") and a.get("title", "").endswith(f" - {a['source']}")
    ]


def check_origin(checks: Checks, origin: str) -> set:
    """Check the instance the gateway proxies to.

    Returns:
        The tool names the live server exposes.
    """
    checks.section("1. Origin instance")

    health_url = origin.rsplit("/mcp", 1)[0] + "/health"
    try:
        health = _get_json(health_url)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        checks.record("/health responds", False, f"{type(exc).__name__}: {exc}")
        health = {}
    else:
        checks.record("/health responds", health.get("status") == "ok", str(health))

    # A shared instance must stay neutral: pinning a language here would hand
    # every caller in the world that language.
    checks.record(
        "locale is neutral",
        health.get("default_language") == "en" and health.get("default_region") == "US",
        f"{health.get('default_language')}/{health.get('default_region')}",
    )

    envelope, ms = _rpc(
        origin,
        "initialize",
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "verify", "version": "1"},
        },
    )
    checks.record(
        "anonymous initialize (no auth wall)", "result" in envelope, f"{ms:.0f}ms"
    )

    envelope, ms = _rpc(origin, "tools/list")
    live = {t["name"] for t in envelope.get("result", {}).get("tools", [])}
    checks.record(
        "tools/list matches expectations",
        live == EXPECTED_TOOLS,
        f"{sorted(live)} {ms:.0f}ms",
    )

    # Smithery rescans the listing with this agent; blocking it empties the
    # registry's tool list without the server ever looking unhealthy.
    envelope, _ = _rpc(origin, "tools/list", user_agent="SmitheryBot/1.0")
    crawler = {t["name"] for t in envelope.get("result", {}).get("tools", [])}
    checks.record("SmitheryBot is not blocked", crawler == live)

    return live


def check_tools(checks: Checks, origin: str) -> None:
    """Exercise all three tools, including a locale override."""
    checks.section("2. Tools")

    result, ms = _call_tool(
        origin, "search_news", {"query": "AI", "max_results": 3, "resolve_urls": False}
    )
    checks.record(
        "search_news returns results",
        result.get("count", 0) > 0,
        f"{result.get('count')} in {ms:.0f}ms",
    )
    left = _unstripped(result.get("articles", []))
    checks.record(
        "titles carry no publisher suffix",
        not left,
        left[0]["title"][:60] if left else "",
    )

    result, ms = _call_tool(
        origin,
        "get_top_headlines",
        {
            "topic": "technology",
            "max_results": 3,
            "language": "ko",
            "region": "KR",
            "resolve_urls": False,
        },
    )
    checks.record(
        "get_top_headlines honors a locale override",
        result.get("language") == "ko" and result.get("count", 0) > 0,
        f"{result.get('count')} in {ms:.0f}ms",
    )
    left = _unstripped(result.get("articles", []))
    checks.record(
        "non-Latin titles are stripped too",
        not left,
        left[0]["title"][:60] if left else "",
    )

    # The most fragile hop: Google wraps every link in an encrypted redirect,
    # resolved through an undocumented internal endpoint.
    result, _ = _call_tool(
        origin,
        "search_news",
        {"query": "technology", "max_results": 5, "resolve_urls": True},
    )
    url = next(
        (
            a["url"]
            for a in result.get("articles", [])
            if "news.google.com" not in a["url"]
        ),
        None,
    )
    if not checks.record(
        "redirects resolve to publisher URLs", url is not None, (url or "")[:60]
    ):
        return

    result, ms = _call_tool(origin, "read_article", {"url": url, "max_length": 800})
    checks.record(
        "read_article extracts body text",
        len(result.get("content", "")) > 100,
        f"{len(result.get('content', ''))} chars in {ms:.0f}ms",
    )


def check_smithery(
    checks: Checks, namespace: str, server: str, live_tools: set
) -> None:
    """Check the registry listing and that the gateway is reachable."""
    checks.section("3. Smithery listing")

    try:
        listing = _get_json(f"{REGISTRY_ROOT}/@{namespace}/{server}")
    except urllib.error.HTTPError as exc:
        checks.record("listed in the registry", False, f"HTTP {exc.code}")
        return

    checks.record(
        "listed in the registry",
        listing.get("qualifiedName") == f"{namespace}/{server}",
    )

    # The registry caches the tool list from its own crawl. A schema change that
    # is not rescanned leaves clients calling tools that no longer match.
    cached = {t["name"] for t in listing.get("tools", [])}
    checks.record(
        "registry's cached tools match the live server",
        cached == live_tools,
        f"{sorted(cached)}" if cached != live_tools else "",
    )

    gateway = listing.get("deploymentUrl", "")
    checks.record("deploymentUrl is present", bool(gateway), gateway)
    if not gateway:
        return

    # 401 is the healthy answer: the gateway is an OAuth 2.0 protected resource
    # and rejects every anonymous request. A 5xx would mean it cannot reach us.
    try:
        urllib.request.urlopen(
            urllib.request.Request(
                gateway,
                b"{}",
                {"Content-Type": "application/json", "User-Agent": USER_AGENT},
            ),
            timeout=30,
        )
        status = 200
    except urllib.error.HTTPError as exc:
        status = exc.code
    except urllib.error.URLError as exc:
        checks.record("gateway is reachable", False, str(exc))
        return

    checks.record(
        "gateway is up (401 = its access control)", status == 401, f"HTTP {status}"
    )


def main() -> int:
    """Run every check and report."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--origin", default=DEFAULT_ORIGIN, help="Server /mcp endpoint."
    )
    parser.add_argument(
        "--namespace", default=DEFAULT_NAMESPACE, help="Smithery namespace."
    )
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Smithery server id.")
    parser.add_argument(
        "--skip-smithery", action="store_true", help="Check only the instance itself."
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Plain output, for CI logs."
    )
    args = parser.parse_args()

    checks = Checks(color=sys.stdout.isatty() and not args.no_color)
    print(f"Verifying {args.origin}")

    try:
        live_tools = check_origin(checks, args.origin)
        check_tools(checks, args.origin)
        if not args.skip_smithery:
            check_smithery(checks, args.namespace, args.server, live_tools)
    except (urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
        checks.record("verification completed", False, f"{type(exc).__name__}: {exc}")

    print(f"\n{checks.passed} passed, {checks.failed} failed")
    return 1 if checks.failed else 0


if __name__ == "__main__":
    sys.exit(main())
