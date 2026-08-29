"""Deployment entrypoint.

Managed hosts (Prefect Horizon, and anything else driving `fastmcp run`) load a
server by file path rather than by importing the installed distribution. When
the host installs only the dependencies from ``pyproject.toml`` and not the
project itself, ``google_rss_mcp`` is not importable, so put ``src/`` on the
path before importing.

Point the host's entrypoint at ``main.py:mcp``.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from google_rss_mcp.server import main, mcp  # noqa: E402

__all__ = ["main", "mcp"]


if __name__ == "__main__":
    main()
