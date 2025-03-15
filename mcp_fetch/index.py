#!/usr/bin/env python3
"""Main entry point for the MCP Fetch server using stdio transport."""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, List

from mcp.server.fastmcp import FastMCP
from mcp import StdioServerParameters
from mcp.types import ListToolsRequest, CallToolRequest

from mcp_fetch.types import RequestPayload
from mcp_fetch.fetcher import Fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


async def setup_server() -> FastMCP:
    """Set up and configure the MCP server."""
    # Create server instance with FastMCP
    server = FastMCP(
        name="mcp-fetch",
        version="0.1.0",
    )
    
    # Set up request handlers
    server.set_request_handler(ListToolsRequest, list_tools_handler)
    server.set_request_handler(CallToolRequest, call_tool_handler)
    
    return server


async def list_tools_handler(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle list_tools requests."""
    # Check if fetch_html tool is enabled
    fetch_html_env = os.environ.get("fetch_html", "Disable")
    is_fetch_html_enabled = fetch_html_env.lower() == "enable"
    
    # Prepare tool list
    tools: List[Dict[str, Any]] = []
    
    # Add fetch_html tool if enabled
    if is_fetch_html_enabled:
        tools.append({
            "name": "fetch_html",
            "description": "Fetch and return the raw HTML content from a website",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the website to fetch",
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional request headers",
                    },
                },
                "required": ["url"],
            },
        })
    
    # Add other tools (always enabled)
    tools.extend([
        {
            "name": "fetch_markdown",
            "description": "Fetch content from a website and convert it to Markdown format",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the website to fetch",
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional request headers",
                    },
                },
                "required": ["url"],
            },
        },
        {
            "name": "fetch_txt",
            "description": "Fetch and return plain text content from a website (HTML tags removed)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the website to fetch",
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional request headers",
                    },
                },
                "required": ["url"],
            },
        },
        {
            "name": "fetch_json",
            "description": "Fetch and return JSON content from a URL",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the JSON resource to fetch",
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional request headers",
                    },
                },
                "required": ["url"],
            },
        }
    ])
    
    return {"tools": tools}


async def call_tool_handler(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle call_tool requests."""
    # Extract tool name and arguments
    name = request["params"]["name"]
    args = request["params"]["arguments"]
    
    # Check if fetch_html tool is enabled
    if name == "fetch_html":
        fetch_html_env = os.environ.get("fetch_html", "Disable")
        is_fetch_html_enabled = fetch_html_env.lower() == "enable"
        
        if not is_fetch_html_enabled:
            raise ValueError("The fetch_html tool is disabled. Please set the environment variable fetch_html=Enable to enable this tool.")
    
    # Define tool handlers mapping
    tool_handlers = {
        "fetch_html": Fetcher.html,
        "fetch_json": Fetcher.json,
        "fetch_txt": Fetcher.txt,
        "fetch_markdown": Fetcher.markdown,
    }
    
    # Validate and convert arguments to RequestPayload
    try:
        payload = RequestPayload(url=args["url"], headers=args.get("headers"))
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Invalid arguments: {str(e)}"}],
            "isError": True
        }
    
    # Get handler for the requested tool
    handler = tool_handlers.get(name)
    if not handler:
        return {
            "content": [{"type": "text", "text": f"Tool not found: {name}"}],
            "isError": True
        }
    
    # Call the handler
    try:
        return await handler(payload)
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


async def main_async():
    """Async main function."""
    # Log environment variable settings
    logger.info("Environment variables settings:")
    logger.info(f"- fetch_html: {os.environ.get('fetch_html', 'Disable')} (default: Disable)")
    
    # Set up server
    server = await setup_server()
    
    # Create stdio parameters
    stdio_params = StdioServerParameters()
    
    # Connect server to transport
    await server.connect(stdio_params)


def main():
    """Main entry point for the script."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 