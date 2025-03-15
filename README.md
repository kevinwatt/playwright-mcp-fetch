# MCP Fetch Tool

**Current version: 0.1.0**

This tool provides a Model Context Protocol (MCP) server for fetching content from websites and converting it to different formats using Playwright.

## Features

- `fetch_html`: Fetch the raw HTML content from a website
- `fetch_markdown`: Fetch content from a website and convert it to Markdown format
- `fetch_txt`: Fetch and return plain text content from a website (HTML tags removed)
- `fetch_json`: Fetch and parse JSON content

## Installation

### From Source

```bash
git clone https://github.com/yourusername/mcp-fetch.git
cd mcp-fetch
pip install -e .
```

### Install Dependencies

```bash
pip install -r requirements.txt
# Install Playwright browsers
playwright install
```

## Usage

### Run as stdio MCP Server

```bash
mcp-fetch
```

### Run as SSE MCP Server

```bash
# Run with the SSE transport
mcp-fetch-sse
```

This will start an HTTP server providing the following endpoints:

- `GET /`: Server status page
- `GET /sse`: SSE connection endpoint
- `POST /api/list-tools`: List available tools
- `POST /api/call-tool`: Call a tool

### Environment Variables

- `PORT`: HTTP server port (default: 3000)
- `TRANSPORT_TYPE`: Transport type, either `stdio` or `sse` (default: `stdio`)
- `fetch_html`: Whether to enable the `fetch_html` tool, either `Enable` or `Disable` (default: `Disable`)

## MCP Client Configuration

To use this server in an MCP client, use the following configuration:

```json
{
  "mcpServers": {
    "fetch-tools": {
      "enabled": true,
      "transport": "sse",
      "url": "http://localhost:3000/sse"
    }
  }
}
```

You can replace `fetch-tools` with any name you prefer, and adjust the URL according to your deployment environment.

## API Examples

### List Tools

```bash
curl -X POST http://localhost:3000/api/list-tools
```

### Call a Tool

```bash
curl -X POST http://localhost:3000/api/call-tool \
  -H "Content-Type: application/json" \
  -d '{"name": "fetch_markdown", "arguments": {"url": "https://example.com"}}'
```

## SSE Client Example

```python
import json
import aiohttp
import asyncio

async def sse_client():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:3000/sse") as response:
            async for line in response.content:
                if line.startswith(b"data: "):
                    data = json.loads(line[6:].decode("utf-8"))
                    print(f"Received event: {data}")

asyncio.run(sse_client())
```

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest
```

## Docker Support

Build and run with Docker:

```bash
docker build -t mcp-fetch .
docker run -p 3000:3000 -e TRANSPORT_TYPE=sse mcp-fetch
```

Or use Docker Compose:

```bash
docker-compose up -d
```

## Acknowledgments

This project is inspired by and ported from [@kevinwatt/biggo-eclimit-fetch-mcp](https://www.npmjs.com/package/@kevinwatt/biggo-eclimit-fetch-mcp).

## License

MIT # playwright-mcp-fetch
