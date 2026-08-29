# google-rss-mcp

An MCP server for Google News. Search headlines in **any language**, then read the
full text of the articles that matter.

<img width="300" height="300" alt="google_rss_mcp" src="https://github.com/user-attachments/assets/ea23e670-388d-44ac-b287-e74ef8fc309a" />

## Tools

| Tool | What it does |
| --- | --- |
| `search_news` | Search Google News for a keyword. Returns headlines with publisher URLs, sources, and timestamps. |
| `get_top_headlines` | Current headlines for a topic section: `top`, `world`, `nation`, `business`, `technology`, `entertainment`, `sports`, `science`, `health`. |
| `read_article` | Download one article and return its readable text, title, and lead image. Accepts a publisher URL or a `news.google.com` link. |

Search and headline calls return **headlines only**. The agent picks what is worth
reading and calls `read_article` on those, which keeps a typical news lookup to a
few hundred tokens instead of tens of thousands.

When served over HTTP the server also answers `GET /health` with a small JSON
status document, for platform health checks.

Google News wraps every link in an encrypted `news.google.com/rss/articles/...`
redirect. This server resolves those to the real publisher URL by default, so
answers can cite a source the user can actually open. Pass `resolve_urls: false`
to skip resolution when you want raw speed.

## Language and region

Locale resolves in three tiers, most specific first:

1. the `language` / `region` arguments on an individual tool call
2. the `GOOGLE_RSS_LANGUAGE` / `GOOGLE_RSS_REGION` environment variables
3. the built-in defaults, `en` / `US`

Set the environment once if you always want the same locale. Korean only:

```bash
GOOGLE_RSS_LANGUAGE=ko
GOOGLE_RSS_REGION=KR
```

A shared deployment can leave the defaults alone and let each caller pass
`language: "ja", region: "JP"` per request.

### All settings

| Variable | Default | Purpose |
| --- | --- | --- |
| `GOOGLE_RSS_LANGUAGE` | `en` | Google News `hl` code (`en`, `ko`, `ja`, `de`, …) |
| `GOOGLE_RSS_REGION` | `US` | Google News `gl` code (`US`, `KR`, `JP`, `DE`, …) |
| `GOOGLE_RSS_TIMEOUT` | `10` | Per-request timeout in seconds (1–120) |
| `GOOGLE_RSS_MAX_CONCURRENCY` | `5` | Max simultaneous outbound requests (1–32) |
| `GOOGLE_RSS_MAX_LENGTH` | `5000` | Default `read_article` truncation length |
| `MCP_TRANSPORT` | `stdio` | Set to `http` to serve Streamable HTTP |
| `MCP_STATELESS` | `true` | HTTP only. Keep on for autoscaled hosts; off enables SSE resumability |
| `PORT` | `8081` | HTTP listen port |
| `LOG_LEVEL` | `INFO` | Python log level |

## Install

### Claude Desktop / Claude Code / Cursor

```json
{
  "mcpServers": {
    "google-rss": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/ccw7463/google-rss-mcp", "google-rss-mcp"],
      "env": {
        "GOOGLE_RSS_LANGUAGE": "ko",
        "GOOGLE_RSS_REGION": "KR"
      }
    }
  }
}
```

Drop the `env` block to get the `en` / `US` default.

### From source

```bash
git clone https://github.com/ccw7463/google-rss-mcp.git
cd google-rss-mcp
uv sync
uv run google-rss-mcp
```

## Hosting over HTTP

Remote MCP clients — and Smithery's URL publishing flow — need a Streamable HTTP
endpoint rather than stdio.

Whichever host you pick, leave `GOOGLE_RSS_LANGUAGE` unset on a shared instance:
the server then answers in `en` / `US` and every caller can ask for their own
locale per request. Pinning it would hand everyone else your language. Pin the
locale in your own client config instead — see [Install](#install).

### Public: Google Cloud Run (recommended)

Cloud Run scales to zero, so an idle server costs nothing, and its always-free
allowance (2M requests, 180k vCPU-seconds, 360k GiB-seconds per month) is far
more than this workload uses.

```bash
GCP_PROJECT=your-project-id ./deploy/cloudrun.sh
```

The script builds the `Dockerfile`, deploys with `--allow-unauthenticated`, caps
`--max-instances` so a spike cannot run up a bill, and prints the endpoint. You
can do the same from the Cloud Run console with "Deploy from repository"; set the
container port to `8080`, the health check path to `/health`, and the environment
to `MCP_TRANSPORT=http` and `MCP_STATELESS=true`.

The resulting `https://<service>-<hash>-<region>.a.run.app/mcp` is what Smithery's
URL publishing flow accepts. The container idles at roughly 70 MB.

**Why stateless.** MCP session state lives in one process's memory. On any
autoscaled host, a follow-up request routed to a second instance would fail to
find its session. These tools need no session state, so `MCP_STATELESS=true`
(the default for HTTP) removes the problem rather than pinning the service to a
single instance.

### Private: Prefect Horizon

[Horizon](https://horizon.prefect.io) is built by the FastMCP team. Its free
Personal tier is a good way to get a private remote server for yourself, but it
admits only members of your own organization — anonymous access, which a public
registry listing requires, is on the paid Developer plan. Use it for a personal
instance (where pinning `GOOGLE_RSS_LANGUAGE` does make sense), not a public one.

- **Entrypoint**: `main.py:mcp`

Dependencies are detected from `pyproject.toml`, and pushes to `main` redeploy
automatically. Verify locally what Horizon will see:

```bash
uv run fastmcp inspect main.py:mcp
```

`main.py` exists so the server loads whether or not the host pip-installs the
project itself; it puts `src/` on the path and re-exports `mcp`.

### Self-hosted: Docker

```bash
docker build -t google-rss-mcp .
docker run -p 8081:8081 -e GOOGLE_RSS_LANGUAGE=ko -e GOOGLE_RSS_REGION=KR google-rss-mcp
```

The endpoint is then `http://localhost:8081/mcp`. The image reads `$PORT`, so it
deploys as-is to Railway, Fly.io, or Cloud Run. Without Docker:

```bash
MCP_TRANSPORT=http PORT=8081 uv run google-rss-mcp
```

## Development

```bash
uv sync --extra dev
uv run pytest
```

The example LangGraph agent needs its own extras and an `OPENAI_API_KEY`:

```bash
uv sync --extra examples
uv run python examples/langgraph_test.py
```

## Notes

- Some publishers (NYT, WSJ, and other hard paywalls) return HTTP 403 to any
  automated request. `read_article` reports that explicitly so the agent can move
  on to another result rather than silently returning nothing.
- Google's URL-resolution endpoint rate-limits under load. Requests are
  concurrency-capped and retried with exponential backoff; lower
  `GOOGLE_RSS_MAX_CONCURRENCY` if you still see throttling.

## License

MIT
