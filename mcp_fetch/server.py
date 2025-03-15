#!/usr/bin/env python3
"""HTTP/SSE server implementation for MCP Fetch."""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from mcp_fetch.types import RequestPayload
from mcp_fetch.fetcher import Fetcher
from mcp_fetch.index import list_tools_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP Fetch Server",
    description="A MCP server with Playwright fetch tools",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SSE connections
sse_connections = set()


class ToolCallRequest(BaseModel):
    """Model for tool call requests."""
    
    name: str
    arguments: Dict[str, Any]


@app.get("/", response_class=HTMLResponse)
async def index():
    """Root endpoint with server status."""
    fetch_html_env = os.environ.get("fetch_html", "Disable")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Fetch Server</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                color: #333;
            }}
            .status {{
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .status h2 {{
                margin-top: 0;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            .tool {{
                margin-bottom: 20px;
                border-left: 4px solid #007bff;
                padding-left: 15px;
            }}
        </style>
    </head>
    <body>
        <h1>MCP Fetch Server</h1>
        
        <div class="status">
            <h2>Server Status</h2>
            <p>The server is running and ready to accept requests.</p>
            <h3>Environment Settings:</h3>
            <ul>
                <li><code>fetch_html</code>: {fetch_html_env} (default: Disable)</li>
            </ul>
        </div>
        
        <h2>Available Tools</h2>
        
        <div class="tool">
            <h3>fetch_html</h3>
            <p>Fetches raw HTML content from a URL.</p>
            <pre>{{
  "name": "fetch_html",
  "arguments": {{
    "url": "https://example.com"
  }}
}}</pre>
        </div>
        
        <div class="tool">
            <h3>fetch_txt</h3>
            <p>Fetches content as plain text (HTML tags removed).</p>
            <pre>{{
  "name": "fetch_txt",
  "arguments": {{
    "url": "https://example.com"
  }}
}}</pre>
        </div>
        
        <div class="tool">
            <h3>fetch_markdown</h3>
            <p>Fetches content and converts it to Markdown format.</p>
            <pre>{{
  "name": "fetch_markdown",
  "arguments": {{
    "url": "https://example.com"
  }}
}}</pre>
        </div>
        
        <div class="tool">
            <h3>fetch_json</h3>
            <p>Fetches JSON content from a URL.</p>
            <pre>{{
  "name": "fetch_json",
  "arguments": {{
    "url": "https://example.com/api.json"
  }}
}}</pre>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP clients."""
    async def event_generator():
        sse_id = id(request)
        sse_connections.add(sse_id)
        
        try:
            # Send initial connection event
            yield {
                "event": "connection",
                "data": json.dumps({
                    "status": "connected",
                    "message": "Connected to MCP Fetch Server"
                })
            }
            
            # Keep connection alive
            while True:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": str(asyncio.get_event_loop().time())})
                }
        except asyncio.CancelledError:
            logger.info(f"SSE connection {sse_id} closed")
        finally:
            if sse_id in sse_connections:
                sse_connections.remove(sse_id)
    
    return EventSourceResponse(event_generator())


@app.post("/api/list-tools")
async def list_tools():
    """List available tools."""
    try:
        tools_response = await list_tools_handler({})
        return tools_response
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/call-tool")
async def call_tool(request: ToolCallRequest):
    """Call a tool."""
    try:
        # Check if tool is enabled
        if request.name == "fetch_html":
            fetch_html_env = os.environ.get("fetch_html", "Disable")
            is_fetch_html_enabled = fetch_html_env.lower() == "enable"
            
            if not is_fetch_html_enabled:
                raise ValueError("The fetch_html tool is disabled. Please set the environment variable fetch_html=Enable to enable this tool.")
        
        # Map tool names to handlers
        tool_handlers = {
            "fetch_html": Fetcher.html,
            "fetch_json": Fetcher.json,
            "fetch_txt": Fetcher.txt,
            "fetch_markdown": Fetcher.markdown,
        }
        
        # Get handler for the requested tool
        handler = tool_handlers.get(request.name)
        if not handler:
            raise ValueError(f"Tool not found: {request.name}")
        
        # Create request payload
        payload = RequestPayload(
            url=request.arguments.get("url"),
            headers=request.arguments.get("headers")
        )
        
        # Call handler
        result = await handler(payload)
        
        # Send result via SSE to all connections
        for conn_id in list(sse_connections):
            # This would be handled by the SSE middleware
            pass
        
        return {"status": "ok", "result": result}
    
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error calling tool: {error_message}")
        
        # Return error with appropriate status code
        if "not found" in error_message.lower():
            raise HTTPException(status_code=404, detail=error_message)
        elif "disabled" in error_message.lower():
            raise HTTPException(status_code=403, detail=error_message)
        elif "invalid" in error_message.lower():
            raise HTTPException(status_code=400, detail=error_message)
        else:
            raise HTTPException(status_code=500, detail=error_message)


def start_server(host: str = "0.0.0.0", port: int = 3000):
    """Start the FastAPI server."""
    logger.info("Starting MCP Fetch Server...")
    logger.info(f"Environment settings:")
    logger.info(f"- fetch_html: {os.environ.get('fetch_html', 'Disable')} (default: Disable)")
    
    uvicorn.run(app, host=host, port=port)


def main():
    """Main entry point for the HTTP/SSE server."""
    try:
        # Get port from environment
        port = int(os.environ.get("PORT", 3000))
        
        # Log environment variable settings
        logger.info("Environment variables settings:")
        logger.info(f"- fetch_html: {os.environ.get('fetch_html', 'Disable')} (default: Disable)")
        logger.info(f"- PORT: {port} (default: 3000)")
        
        # Start server
        start_server(port=port)
    
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 