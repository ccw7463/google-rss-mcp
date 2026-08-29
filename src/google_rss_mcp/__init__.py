"""Google News RSS MCP server."""

# Kept in sync with pyproject.toml; used when the package is not pip-installed
# (managed hosts often install only dependencies and load the file directly).
__version__ = "0.2.0"

from google_rss_mcp.config import Settings
from google_rss_mcp.rss import Article, GoogleNewsClient, GoogleNewsError, NewsItem

__all__ = [
    "__version__",
    "Article",
    "GoogleNewsClient",
    "GoogleNewsError",
    "NewsItem",
    "Settings",
]
