"""Tests for the HTTP/SSE server."""

import os
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from playwright_mcp_fetch.server import app
from playwright_mcp_fetch.fetcher import Fetcher


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_index_page(client):
    """Test the index page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "MCP Fetch Server" in response.text
    assert "Server Status" in response.text
    assert "Environment Settings" in response.text


def test_list_tools_endpoint(client):
    """Test the list-tools endpoint."""
    # Set environment variable for testing
    os.environ["fetch_html"] = "Disable"
    
    response = client.post("/api/list-tools")
    assert response.status_code == 200
    
    # Check response content
    data = response.json()
    assert "tools" in data
    
    # Check that fetch_html is not in the tools list (since it's disabled)
    tool_names = [tool["name"] for tool in data["tools"]]
    assert "fetch_html" not in tool_names
    
    # Check that other tools are in the list
    assert "fetch_markdown" in tool_names
    assert "fetch_txt" in tool_names
    assert "fetch_json" in tool_names
    
    # Test with fetch_html enabled
    os.environ["fetch_html"] = "Enable"
    response = client.post("/api/list-tools")
    assert response.status_code == 200
    
    # Check response content
    data = response.json()
    tool_names = [tool["name"] for tool in data["tools"]]
    assert "fetch_html" in tool_names


@patch.object(Fetcher, "markdown")
def test_call_tool_endpoint(mock_markdown, client):
    """Test the call-tool endpoint."""
    # Mock the Fetcher.markdown method
    mock_result = {
        "content": [{"type": "text", "text": "# Test Markdown\n\nThis is a test."}],
        "isError": False
    }
    mock_markdown.return_value = mock_result
    
    # Call the endpoint
    response = client.post(
        "/api/call-tool",
        json={
            "name": "fetch_markdown",
            "arguments": {
                "url": "https://example.com"
            }
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "result" in data
    assert data["result"]["content"][0]["text"] == "# Test Markdown\n\nThis is a test."


def test_call_tool_with_disabled_tool(client):
    """Test calling a disabled tool."""
    # Ensure fetch_html is disabled
    os.environ["fetch_html"] = "Disable"
    
    # Call the endpoint with fetch_html
    response = client.post(
        "/api/call-tool",
        json={
            "name": "fetch_html",
            "arguments": {
                "url": "https://example.com"
            }
        }
    )
    
    # Check response (should be an error)
    assert response.status_code == 403  # Forbidden
    assert "disabled" in response.json()["detail"].lower()


def test_call_tool_with_invalid_tool(client):
    """Test calling an invalid tool."""
    # Call the endpoint with a non-existent tool
    response = client.post(
        "/api/call-tool",
        json={
            "name": "non_existent_tool",
            "arguments": {
                "url": "https://example.com"
            }
        }
    )
    
    # Check response (should be an error)
    assert response.status_code == 404  # Not Found
    assert "not found" in response.json()["detail"].lower() 