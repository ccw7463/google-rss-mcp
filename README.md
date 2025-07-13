# google-rss-mcp

A Model Context Protocol (MCP) server that leverages Google News RSS feeds. Built on FastMCP framework

<img width="400" height="400" alt="google_rss_mcp" src="https://github.com/user-attachments/assets/ea23e670-388d-44ac-b287-e74ef8fc309a" />

https://smithery.ai/server/@ccw7463/google-rss-mcp

## Overview

https://github.com/user-attachments/assets/584c38c0-c5dc-4219-b54e-bc8187f1b675

This project is an MCP server that collects and provides news data using Google News RSS feeds. It's built using the FastMCP framework and includes workflow testing through LangGraph.

Key Features:
- News collection from Google News RSS feeds
- Topic-based news search (top, world, business, technology, etc.)
- Keyword-based news search
- AI workflow integration through LangGraph

## Project Structure

```
google-rss-mcp/
├── src/
│   ├── server.py      # FastMCP server main file
│   ├── rss.py         # Google RSS tools class
│   └── client.py      # MCP client implementation
├── langgraph_test.py  # LangGraph workflow test
├── client_test.py     # Basic client test
└── pyproject.toml     # Project configuration and dependencies
```

## Getting Started

### 1. Install uv

First, you need to install the uv package manager:

```bash
# macOS/Linux
curl -Ls https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Project Setup

```bash
# Clone the project
git clone https://github.com/ccw7463/google-rss-mcp.git
cd google-rss-mcp

# Create virtual environment and install dependencies
uv sync
```

### 3. Environment Variables

Create a `.env` file and set your OpenAI API key:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Run Tests

To run the LangGraph workflow test:

```bash
uv run python langgraph_test.py
```

This command connects to the Google RSS MCP server and runs an AI news search workflow through LangGraph.

