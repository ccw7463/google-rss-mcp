# google-rss-mcp

A Model Context Protocol (MCP) server that leverages Google News RSS feeds. Built on FastMCP framework

<img width="300" height="300" alt="google_rss_mcp" src="https://github.com/user-attachments/assets/ea23e670-388d-44ac-b287-e74ef8fc309a" />

## MCP Server Platform

[![Smithery](https://img.shields.io/badge/Smithery-Add%20to%20your%20AI%20tools-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDkuNzRMMTIgMTZMMTAuOTEgOS43NEw0IDlMMTAuOTEgOC4yNkwxMiAyWiIgZmlsbD0iY3VycmVudENvbG9yIi8+Cjwvc3ZnPgo=)](https://smithery.ai/server/@ccw7463/google-rss-mcp)

**Direct Link:** https://smithery.ai/server/@ccw7463/google-rss-mcp

## Overview

https://github.com/user-attachments/assets/15f66d05-9d9c-4c2c-b801-b9b6182dfada

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

### Installing via Smithery

To install Google News RSS Feed Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@ccw7463/google-rss-mcp):

```bash
npx -y @smithery/cli install @ccw7463/google-rss-mcp --client claude
```

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
