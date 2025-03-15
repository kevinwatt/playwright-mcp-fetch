"""Core fetcher implementation using Playwright."""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Response
from html2text import HTML2Text

from playwright_mcp_fetch.types import RequestPayload

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Fetcher:
    """Fetcher class for retrieving web content using Playwright."""
    
    # Constants
    MAX_RETRIES = 2
    BASE_TIMEOUT = 10000  # milliseconds
    MAX_REDIRECTS = 3
    
    @classmethod
    async def _fetch(cls, payload: RequestPayload) -> Tuple[str, str]:
        """
        Fetch content from the specified URL.
        
        Args:
            payload: The request payload containing URL and headers
            
        Returns:
            Tuple of (content, content_type)
            
        Raises:
            Exception: If fetching fails after max retries
        """
        last_error = None
        
        # Retry logic
        for attempt in range(cls.MAX_RETRIES + 1):
            try:
                logger.info(f"Attempt {attempt + 1} to fetch {payload.url}")
                
                async with async_playwright() as playwright:
                    # Launch browser
                    browser = await playwright.chromium.launch(
                        headless=True,
                        timeout=30000  # Increased timeout for browser launch
                    )
                    
                    try:
                        # Create browser context
                        context = await browser.new_context(
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            extra_http_headers=payload.headers or {}
                        )
                        
                        # Create page
                        page = await context.new_page()
                        
                        # Track redirect count
                        redirect_count = 0
                        
                        # Set up route handler to monitor and limit redirects
                        async def handle_route(route, request):
                            nonlocal redirect_count
                            
                            # Check for redirects
                            redirected_from = request.redirected_from
                            if request.is_navigation_request and redirected_from:
                                redirect_count += 1
                                logger.info(f"Redirect #{redirect_count}: {redirected_from.url} -> {request.url}")
                                
                                # Abort if too many redirects
                                if redirect_count > cls.MAX_REDIRECTS:
                                    logger.error(f"Redirect count exceeded limit ({cls.MAX_REDIRECTS}), aborting request")
                                    await route.abort("failed")
                                    return
                            
                            # Continue request
                            await route.continue_()
                        
                        # Apply route handler
                        await page.route("**/*", handle_route)
                        
                        # Navigate to URL
                        response = await page.goto(
                            str(payload.url),
                            wait_until="commit",  # Only wait for page to start receiving content
                            timeout=cls.BASE_TIMEOUT * (attempt + 1)
                        )
                        
                        if not response:
                            raise ValueError("No response received")
                        
                        if response.status >= 400:
                            raise ValueError(f"HTTP error: {response.status}")
                        
                        # Wait a bit for content to load
                        await page.wait_for_timeout(2000)
                        
                        # Get content type
                        content_type = response.headers.get("content-type", "")
                        
                        # Get page content
                        content = await page.content()
                        
                        return content, content_type
                    
                    finally:
                        # Always close browser
                        await browser.close()
            
            except Exception as e:
                last_error = e
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                
                # If not the last attempt, wait before retrying
                if attempt < cls.MAX_RETRIES:
                    delay = 1000 * (attempt + 1)  # Gradually increase delay
                    logger.info(f"Waiting {delay}ms before retry...")
                    await asyncio.sleep(delay / 1000)  # Convert to seconds
        
        # All retries failed
        raise Exception(f"Failed to fetch {payload.url} after {cls.MAX_RETRIES + 1} attempts: {str(last_error)}")
    
    @classmethod
    def _create_error_response(cls, error: Exception) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "content": [{"type": "text", "text": str(error)}],
            "isError": True
        }
    
    @classmethod
    async def html(cls, payload: RequestPayload) -> Dict[str, Any]:
        """
        Fetch raw HTML content from the URL.
        
        Args:
            payload: The request payload
            
        Returns:
            Response containing HTML content or error
        """
        try:
            content, _ = await cls._fetch(payload)
            return {
                "content": [{"type": "text", "text": content}],
                "isError": False
            }
        except Exception as error:
            return cls._create_error_response(error)
    
    @classmethod
    async def json(cls, payload: RequestPayload) -> Dict[str, Any]:
        """
        Fetch JSON content from the URL.
        
        Args:
            payload: The request payload
            
        Returns:
            Response containing parsed JSON or error
        """
        try:
            content, _ = await cls._fetch(payload)
            
            # Try to extract JSON from HTML
            json_content = content
            
            # Check if HTML wrapped JSON
            if "<pre>" in content and "</pre>" in content:
                import re
                pre_match = re.search(r"<pre>([\s\S]*?)</pre>", content)
                if pre_match and pre_match.group(1):
                    json_content = pre_match.group(1).strip()
            
            # Try to parse JSON
            try:
                import json
                json_obj = json.loads(json_content)
                return {
                    "content": [{"type": "text", "text": json.dumps(json_obj)}],
                    "isError": False
                }
            except json.JSONDecodeError:
                raise ValueError("Response is not valid JSON")
                
        except Exception as error:
            return cls._create_error_response(error)
    
    @classmethod
    async def txt(cls, payload: RequestPayload) -> Dict[str, Any]:
        """
        Fetch content as plain text from the URL (HTML tags removed).
        
        Args:
            payload: The request payload
            
        Returns:
            Response containing plain text or error
        """
        try:
            content, _ = await cls._fetch(payload)
            
            # Use BeautifulSoup to extract text
            soup = BeautifulSoup(content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text and normalize whitespace
            text = soup.get_text()
            normalized_text = " ".join(text.split())
            
            return {
                "content": [{"type": "text", "text": normalized_text}],
                "isError": False
            }
        except Exception as error:
            return cls._create_error_response(error)
    
    @classmethod
    async def markdown(cls, payload: RequestPayload) -> Dict[str, Any]:
        """
        Fetch content and convert it to Markdown format.
        
        Args:
            payload: The request payload
            
        Returns:
            Response containing Markdown or error
        """
        try:
            content, _ = await cls._fetch(payload)
            
            # Use BeautifulSoup to parse HTML and extract main content
            soup = BeautifulSoup(content, "html.parser")
            
            # Remove script and style elements
            for element in soup(["script", "style"]):
                element.extract()
            
            # Try to find main content
            main_content = None
            
            # Try to identify main content by common selectors
            main_selectors = ["main", "article", "#content", ".content", "#main", ".main"]
            for selector in main_selectors:
                main = soup.select_one(selector)
                if main:
                    main_content = main
                    break
            
            # If no main content identified, use body
            if not main_content:
                main_content = soup.body
            
            # Extract title
            title = soup.title.string if soup.title else ""
            
            # Convert to HTML string
            html_content = str(main_content) if main_content else content
            
            # Custom HTML to Markdown conversion using markdown module
            # First, extract text and basic structure
            clean_html = cls._clean_html_for_markdown(html_content)
            
            # Convert to Markdown using a custom approach
            markdown_content = cls._html_to_markdown(clean_html)
            
            # Add title as h1 if found
            if title:
                markdown_content = f"# {title}\n\n{markdown_content}"
            
            return {
                "content": [{"type": "text", "text": markdown_content}],
                "isError": False
            }
        except Exception as error:
            return cls._create_error_response(error)
    
    @staticmethod
    def _clean_html_for_markdown(html: str) -> str:
        """Clean HTML to prepare for markdown conversion."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Replace common elements with markdown equivalents
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(tag.name[1])
            prefix = '#' * level + ' '
            tag.string = prefix + tag.get_text().strip()
            tag.unwrap()
        
        # Handle emphasis (strong/bold)
        for tag in soup.find_all(['strong', 'b']):
            text = tag.get_text().strip()
            tag.replace_with(f"**{text}**")
        
        # Handle emphasis (em/italic)
        for tag in soup.find_all(['em', 'i']):
            text = tag.get_text().strip()
            tag.replace_with(f"*{text}*")
        
        # Handle links
        for a in soup.find_all('a'):
            href = a.get('href', '')
            text = a.get_text().strip()
            if href and text:
                a.replace_with(f"[{text}]({href})")
        
        # Handle images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                img.replace_with(f"![{alt}]({src})")
        
        # Handle lists
        for ul in soup.find_all('ul'):
            for li in ul.find_all('li'):
                li.string = "* " + li.get_text().strip()
                li.unwrap()
            ul.unwrap()
        
        for ol in soup.find_all('ol'):
            for i, li in enumerate(ol.find_all('li')):
                li.string = f"{i+1}. " + li.get_text().strip()
                li.unwrap()
            ol.unwrap()
        
        # Handle paragraphs
        for p in soup.find_all('p'):
            p.append("\n\n")
            p.unwrap()
        
        return str(soup)
    
    @staticmethod
    def _html_to_markdown(html: str) -> str:
        """Convert HTML to Markdown using custom rules."""
        # Use BeautifulSoup to extract text with our custom formatting
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()
        
        # Clean up extra whitespace
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        
        return text 