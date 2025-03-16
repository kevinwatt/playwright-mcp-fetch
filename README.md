# playwright-mcp-fetch

**Current version: 0.1.5**

This tool provides a Model Context Protocol (MCP) server for fetching content from websites and converting it to different formats using Playwright.

## Requirements

- Python 3.10 or higher

## Features

- `fetch_html`: Fetch the raw HTML content from a website
- `fetch_markdown`: Fetch content from a website and convert it to Markdown format
- `fetch_txt`: Fetch and return plain text content from a website (HTML tags removed)
- `fetch_json`: Fetch and parse JSON content

## Installation

### From Source

```bash
git clone https://github.com/kevinwatt/playwright-mcp-fetch.git
cd playwright-mcp-fetch
pip install -e .
```

### Install Dependencies

```bash
pip install -r requirements.txt
# Install Playwright browsers
playwright install
```

## Usage

### Run as MCP Server (SSE Transport)

```bash
# Run the MCP server with SSE transport
playwright-mcp-fetch-sse
```

### Environment Variables

- `fetch_html`: Set to "Enable" to enable the fetch_html tool (default: "Disable")
- `PORT`: Set the HTTP port for the SSE server (default: 3000)

### MCP Client Configuration

To use this server with an MCP client, configure the client to connect to the SSE endpoint:

```json
{
  "mcpServers": {
    "fetch-tools": {
      "enabled": true,
      "transport": "sse",
      "url": "http://localhost:3000/sse",
      "postUrl": "http://localhost:3000/messages"
    }
  }
}
```

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
docker build -t playwright-mcp-fetch .
docker run -p 3000:3000 -e TRANSPORT_TYPE=sse playwright-mcp-fetch
```

Or use Docker Compose:

```bash
docker-compose up -d
```

## License

MIT
