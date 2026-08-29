"""Unit tests for parsing and extraction helpers (no network required)."""

from datetime import timezone

import pytest
from bs4 import BeautifulSoup

from google_rss_mcp.config import Settings
from google_rss_mcp.rss import (
    GoogleNewsClient,
    _image_from_json_ld,
    _is_plausible_lead_image,
    clean_text,
    parse_date,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("AT&amp;T rose 5% to $120", "AT&T rose 5% to $120"),
        ("C++ / C# developers @ Google", "C++ / C# developers @ Google"),
        ("가격은 1,000원 (약 $0.75)", "가격은 1,000원 (약 $0.75)"),
        ("&quot;great&quot; news", '"great" news'),
        ("日本の経済ニュース", "日本の経済ニュース"),
        ("  spaced   out  ", "spaced out"),
        ("", ""),
    ],
)
def test_clean_text_preserves_meaningful_characters(raw, expected):
    """Figures, symbols and names must survive cleaning."""
    assert clean_text(raw) == expected


def test_clean_text_strips_markup_and_collapses_blank_lines():
    """Tags go away and paragraph breaks collapse to a single blank line."""
    assert clean_text("<p>one</p>\n\n\n\n<p>two</p>") == "one\n\ntwo"


def test_parse_date_returns_aware_utc_datetime():
    """RFC 822 feed dates parse into timezone-aware datetimes."""
    parsed = parse_date("Mon, 25 Aug 2025 09:30:00 GMT")
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.astimezone(timezone.utc).hour == 9


def test_parse_date_handles_garbage():
    """Unparseable input yields None rather than raising."""
    assert parse_date("not a date") is None
    assert parse_date("") is None


def test_image_from_json_ld_walks_nested_shapes():
    """The JSON-LD walker handles str, dict, list and @graph nesting."""
    assert _image_from_json_ld({"image": "https://x/a.jpg"}) == "https://x/a.jpg"
    assert (
        _image_from_json_ld({"image": {"url": "https://x/b.jpg"}}) == "https://x/b.jpg"
    )
    assert _image_from_json_ld({"image": ["https://x/c.jpg"]}) == "https://x/c.jpg"
    assert (
        _image_from_json_ld({"@graph": [{"image": "https://x/d.jpg"}]})
        == "https://x/d.jpg"
    )
    assert _image_from_json_ld({"headline": "no image"}) is None


def test_is_plausible_lead_image_rejects_chrome():
    """Icons, trackers and data URIs are not lead images."""
    tag = BeautifulSoup('<img src="x">', "html.parser").img
    assert not _is_plausible_lead_image(tag, "https://x/logo-header.png")
    assert not _is_plausible_lead_image(tag, "data:image/png;base64,AAAA")
    assert not _is_plausible_lead_image(tag, "https://x/1x1.gif")
    assert _is_plausible_lead_image(tag, "https://cdn.example.com/lead-photo.jpg")


def test_is_plausible_lead_image_rejects_small_declared_sizes():
    """An <img> that declares itself tiny is skipped."""
    small = BeautifulSoup('<img src="a.jpg" width="32" height="32">', "html.parser").img
    big = BeautifulSoup('<img src="a.jpg" width="800" height="600">', "html.parser").img
    assert not _is_plausible_lead_image(small, "https://cdn.example.com/a.jpg")
    assert _is_plausible_lead_image(big, "https://cdn.example.com/a.jpg")


def test_extract_body_drops_boilerplate():
    """Nav, script and footer content never reaches the article text."""
    html = """
        <html><body>
          <nav>MENU HOME SEARCH</nav>
          <script>var tracker = 1;</script>
          <article><p>The council voted 7-2 on Tuesday.</p></article>
          <footer>Copyright notice</footer>
        </body></html>
    """
    body = GoogleNewsClient()._extract_body(BeautifulSoup(html, "html.parser"))
    assert "council voted 7-2" in body
    assert "MENU" not in body
    assert "tracker" not in body
    assert "Copyright" not in body


def test_extract_image_prefers_open_graph_and_absolutizes():
    """og:image wins, and relative paths are made absolute."""
    html = (
        '<html><head><meta property="og:image" content="/img/lead.jpg"></head></html>'
    )
    url = GoogleNewsClient()._extract_image(
        BeautifulSoup(html, "html.parser"), "https://news.example.com/story/1"
    )
    assert url == "https://news.example.com/img/lead.jpg"


def test_locale_params_reflect_constructor():
    """Locale is per-instance, not global."""
    assert "hl=ko" in GoogleNewsClient(language="ko", region="KR")._locale_params()
    assert "ceid=KR:ko" in GoogleNewsClient(language="ko", region="KR")._locale_params()
    assert "hl=ja" in GoogleNewsClient(language="ja", region="JP")._locale_params()


async def test_request_outside_context_manager_is_an_error():
    """Using the client without opening a session fails loudly."""
    with pytest.raises(Exception, match="async context manager"):
        await GoogleNewsClient()._request("GET", "https://example.com")


def test_settings_read_environment(monkeypatch):
    """Environment variables override the neutral defaults."""
    monkeypatch.setenv("GOOGLE_RSS_LANGUAGE", "ko")
    monkeypatch.setenv("GOOGLE_RSS_REGION", "KR")
    settings = Settings.from_env()
    assert (settings.language, settings.region) == ("ko", "KR")


def test_settings_ignore_blank_and_bad_values(monkeypatch):
    """Blank or non-numeric values fall back instead of crashing."""
    monkeypatch.setenv("GOOGLE_RSS_LANGUAGE", "   ")
    monkeypatch.setenv("GOOGLE_RSS_TIMEOUT", "not-a-number")
    settings = Settings.from_env()
    assert settings.language == "en"
    assert settings.timeout == 10.0


def test_settings_clamp_out_of_range(monkeypatch):
    """Absurd numbers are clamped to a usable range."""
    monkeypatch.setenv("GOOGLE_RSS_MAX_CONCURRENCY", "9999")
    assert Settings.from_env().max_concurrency == 32


@pytest.mark.parametrize(
    ("status", "needle"),
    [
        (403, "paywall or bot protection"),
        (404, "may have expired"),
        (500, "HTTP 500"),
        (None, "TLS"),
    ],
)
def test_fetch_failure_message_is_actionable(status, needle):
    """Failure messages name the cause so the agent can pick a next step."""
    from google_rss_mcp.rss import _fetch_failure_message

    assert needle in _fetch_failure_message("https://x/a", status)


def test_fallback_version_matches_pyproject():
    """The hardcoded fallback must not drift from the packaged version."""
    import tomllib
    from pathlib import Path

    import google_rss_mcp

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    declared = tomllib.loads(pyproject.read_text())["project"]["version"]
    assert google_rss_mcp.__version__ == declared


def test_deployment_entrypoint_exposes_server():
    """main.py:mcp is what managed hosts load; keep it importable."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "main.py"
    spec = importlib.util.spec_from_file_location("_entrypoint", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.mcp.name == "google-rss-mcp"


async def test_health_route_reports_ok():
    """Platform health checks need a 2xx on /health without any network call."""
    from starlette.testclient import TestClient

    from google_rss_mcp.server import mcp

    with TestClient(mcp.http_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["default_language"] == "en"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", True),
        ("true", True),
        ("ON", True),
        ("0", False),
        ("no", False),
        ("", None),
    ],
)
def test_env_flag_parsing(monkeypatch, value, expected):
    """Boolean env vars accept the usual spellings and fall back when unset."""
    from google_rss_mcp.server import _env_flag

    monkeypatch.setenv("SOME_FLAG", value)
    assert _env_flag("SOME_FLAG", True) is (True if expected is None else expected)
    assert _env_flag("SOME_FLAG", False) is (False if expected is None else expected)
