---
search:
  exclude: true
---

# MCP Server API Reference

The **WhisperCrawler MCP Server** provides six powerful tools for web scraping through the Model Context Protocol (MCP). This server integrates WhisperCrawler's capabilities directly into AI chatbots and agents, allowing conversational web scraping with advanced anti-bot bypass features.

You can start the MCP server by running:

```bash
whispercrawler mcp
```

Or import the server class directly:

```python
from whispercrawler.core.ai import WhisperCrawlerMCPServer

server = WhisperCrawlerMCPServer()
server.serve(http=False, host="0.0.0.0", port=8000)
```

## Response Model

The standardized response structure that's returned by all MCP server tools:

## ::: whispercrawler.core.ai.ResponseModel
    handler: python
    :docstring:

## MCP Server Class

The main MCP server class that provides all web scraping tools:

## ::: whispercrawler.core.ai.WhisperCrawlerMCPServer
    handler: python
    :docstring:
