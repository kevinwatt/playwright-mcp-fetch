"""Tests for the Fetcher module."""

import os
import pytest
from unittest.mock import patch, AsyncMock

from playwright_mcp_fetch.types import RequestPayload
from playwright_mcp_fetch.fetcher import Fetcher


@pytest.mark.asyncio
async def test_fetch_html_success():
    """Test successful HTML fetching."""
    # Mock Fetcher._fetch to return a sample HTML content
    sample_html = "<html><body><h1>Test Page</h1></body></html>"
    with patch.object(Fetcher, '_fetch', AsyncMock(return_value=(sample_html, "text/html"))):
        # Create a test payload
        payload = RequestPayload(url="https://example.com")
        
        # Call the html method
        result = await Fetcher.html(payload)
        
        # Verify the result
        assert result["isError"] is False
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == sample_html


@pytest.mark.asyncio
async def test_fetch_html_error():
    """Test HTML fetching with error."""
    # Mock Fetcher._fetch to raise an exception
    error_message = "Failed to fetch"
    with patch.object(Fetcher, '_fetch', AsyncMock(side_effect=Exception(error_message))):
        # Create a test payload
        payload = RequestPayload(url="https://example.com")
        
        # Call the html method
        result = await Fetcher.html(payload)
        
        # Verify the result
        assert result["isError"] is True
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == error_message


@pytest.mark.asyncio
async def test_fetch_txt_success():
    """Test successful text fetching."""
    # Mock Fetcher._fetch to return a sample HTML content
    sample_html = """
    <html>
        <head><title>Test Title</title></head>
        <body>
            <h1>Test Page</h1>
            <p>This is a test paragraph.</p>
            <script>console.log("This should be removed");</script>
            <style>.hidden { display: none; }</style>
        </body>
    </html>
    """
    with patch.object(Fetcher, '_fetch', AsyncMock(return_value=(sample_html, "text/html"))):
        # Create a test payload
        payload = RequestPayload(url="https://example.com")
        
        # Call the txt method
        result = await Fetcher.txt(payload)
        
        # Verify the result
        assert result["isError"] is False
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "Test Page" in result["content"][0]["text"]
        assert "This is a test paragraph" in result["content"][0]["text"]
        assert "This should be removed" not in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_fetch_markdown_success():
    """Test successful markdown fetching."""
    # Mock Fetcher._fetch to return a sample HTML content
    sample_html = """
    <html>
        <head><title>Test Title</title></head>
        <body>
            <h1>Test Page</h1>
            <p>This is a <strong>test</strong> paragraph.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </body>
    </html>
    """
    with patch.object(Fetcher, '_fetch', AsyncMock(return_value=(sample_html, "text/html"))):
        # Create a test payload
        payload = RequestPayload(url="https://example.com")
        
        # Call the markdown method
        result = await Fetcher.markdown(payload)
        
        # Verify the result
        assert result["isError"] is False
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "# Test Title" in result["content"][0]["text"]
        assert "Test Page" in result["content"][0]["text"]
        assert "**test**" in result["content"][0]["text"] or "*test*" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_fetch_json_success():
    """Test successful JSON fetching."""
    # Mock Fetcher._fetch to return a sample JSON content
    sample_json = '{"key": "value", "nested": {"inner": 123}}'
    with patch.object(Fetcher, '_fetch', AsyncMock(return_value=(sample_json, "application/json"))):
        # Create a test payload
        payload = RequestPayload(url="https://example.com")
        
        # Call the json method
        result = await Fetcher.json(payload)
        
        # Verify the result
        assert result["isError"] is False
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert '"key": "value"' in result["content"][0]["text"]
        assert '"inner": 123' in result["content"][0]["text"] 