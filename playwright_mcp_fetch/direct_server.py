#!/usr/bin/env python3
"""Direct MCP server implementation using low-level API."""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, List

import anyio
from mcp.server.lowlevel.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

from playwright_mcp_fetch.types import RequestPayload
from playwright_mcp_fetch.fetcher import Fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Check if fetch_html tool is enabled
fetch_html_env = os.environ.get("fetch_html", "Disable")
is_fetch_html_enabled = fetch_html_env.lower() == "enable"

# Create server instance with low-level API
server = Server(
    name="mcp-fetch",
    version="0.1.5",
)

# Register tool handlers
@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools."""
    tools = []
    
    # Add fetch_html tool if enabled
    if is_fetch_html_enabled:
        tools.append(
            types.Tool(
                name="fetch_html",
                description="Fetch and return the raw HTML content from a website.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL to fetch HTML from"},
                        "headers": {"type": "object", "description": "Optional HTTP headers"}
                    },
                    "required": ["url"]
                }
            )
        )
    
    # Add other tools
    tools.append(
        types.Tool(
            name="fetch_markdown",
            description="Fetch content from a website and convert it to Markdown format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch content from"},
                    "headers": {"type": "object", "description": "Optional HTTP headers"}
                },
                "required": ["url"]
            }
        )
    )
    
    tools.append(
        types.Tool(
            name="fetch_txt",
            description="Fetch and return plain text content from a website (HTML tags removed).",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch text from"},
                    "headers": {"type": "object", "description": "Optional HTTP headers"}
                },
                "required": ["url"]
            }
        )
    )
    
    tools.append(
        types.Tool(
            name="fetch_json",
            description="Fetch and return JSON content from a URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch JSON from"},
                    "headers": {"type": "object", "description": "Optional HTTP headers"}
                },
                "required": ["url"]
            }
        )
    )
    
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Call a tool."""
    url = arguments.get("url")
    headers = arguments.get("headers")
    
    if not url:
        raise ValueError("URL is required")
    
    payload = RequestPayload(url=url, headers=headers)
    
    if name == "fetch_html":
        if not is_fetch_html_enabled:
            raise ValueError("The fetch_html tool is disabled. Please set the environment variable fetch_html=Enable to enable this tool.")
        result = await Fetcher.html(payload)
    elif name == "fetch_markdown":
        result = await Fetcher.markdown(payload)
    elif name == "fetch_txt":
        result = await Fetcher.txt(payload)
    elif name == "fetch_json":
        result = await Fetcher.json(payload)
    else:
        raise ValueError(f"Unknown tool: {name}")
    
    return [types.TextContent(type="text", text=result.get("content", ""))]

async def main_async():
    """Async main function."""
    # Log environment variable settings
    logger.info("Environment variables settings:")
    logger.info(f"- fetch_html: {os.environ.get('fetch_html', 'Disable')} (default: Disable)")
    
    try:
        # Run the server using stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point for the script."""
    try:
        # Run the async main function
        anyio.run(main_async)
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 