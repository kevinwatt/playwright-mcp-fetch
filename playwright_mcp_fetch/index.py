#!/usr/bin/env python3
"""Main entry point for the MCP Fetch server using stdio transport."""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, List

from mcp.server.fastmcp import FastMCP

from playwright_mcp_fetch.types import RequestPayload
from playwright_mcp_fetch.fetcher import Fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create server instance with FastMCP
server = FastMCP(
    name="mcp-fetch",
    version="0.1.5",
)

# Check if fetch_html tool is enabled
fetch_html_env = os.environ.get("fetch_html", "Disable")
is_fetch_html_enabled = fetch_html_env.lower() == "enable"

# 添加 list_tools_handler 函數
async def list_tools_handler() -> Dict[str, List[Dict[str, Any]]]:
    """Handler for listing available tools."""
    # 在函數內部檢查環境變數
    fetch_html_env = os.environ.get("fetch_html", "Disable")
    is_fetch_html_enabled_local = fetch_html_env.lower() == "enable"
    
    tools = []
    
    # 添加 fetch_html 工具（如果啟用）
    if is_fetch_html_enabled_local:
        tools.append({
            "name": "fetch_html",
            "description": "Fetch and return the raw HTML content from a website.",
            "parameters": {
                "url": {"type": "string", "description": "The URL to fetch HTML from"},
                "headers": {"type": "object", "description": "Optional HTTP headers"}
            }
        })
    
    # 添加其他工具
    tools.append({
        "name": "fetch_markdown",
        "description": "Fetch content from a website and convert it to Markdown format.",
        "parameters": {
            "url": {"type": "string", "description": "The URL to fetch content from"},
            "headers": {"type": "object", "description": "Optional HTTP headers"}
        }
    })
    
    tools.append({
        "name": "fetch_txt",
        "description": "Fetch and return plain text content from a website (HTML tags removed).",
        "parameters": {
            "url": {"type": "string", "description": "The URL to fetch text from"},
            "headers": {"type": "object", "description": "Optional HTTP headers"}
        }
    })
    
    tools.append({
        "name": "fetch_json",
        "description": "Fetch and return JSON content from a URL.",
        "parameters": {
            "url": {"type": "string", "description": "The URL to fetch JSON from"},
            "headers": {"type": "object", "description": "Optional HTTP headers"}
        }
    })
    
    # 返回包含 tools 鍵的字典
    return {"tools": tools}

# 正確的裝飾器用法
@server.tool()
async def fetch_html(url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Fetch and return the raw HTML content from a website."""
    if not is_fetch_html_enabled:
        raise ValueError("The fetch_html tool is disabled. Please set the environment variable fetch_html=Enable to enable this tool.")
    
    payload = RequestPayload(url=url, headers=headers)
    return await Fetcher.html(payload)


@server.tool()
async def fetch_markdown(url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Fetch content from a website and convert it to Markdown format."""
    payload = RequestPayload(url=url, headers=headers)
    return await Fetcher.markdown(payload)


@server.tool()
async def fetch_txt(url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Fetch and return plain text content from a website (HTML tags removed)."""
    payload = RequestPayload(url=url, headers=headers)
    return await Fetcher.txt(payload)


@server.tool()
async def fetch_json(url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Fetch and return JSON content from a URL."""
    payload = RequestPayload(url=url, headers=headers)
    return await Fetcher.json(payload)


async def main_async():
    """Async main function."""
    # Log environment variable settings
    logger.info("Environment variables settings:")
    logger.info(f"- fetch_html: {os.environ.get('fetch_html', 'Disable')} (default: Disable)")
    
    try:
        # Run the server
        await server.run()  # 使用 run() 方法
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point for the script."""
    try:
        # Log environment variable settings
        logger.info("Environment variables settings:")
        logger.info(f"- fetch_html: {os.environ.get('fetch_html', 'Disable')} (default: Disable)")
        
        # Run the server using stdio transport
        import anyio
        anyio.run(server.run_stdio_async)
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 