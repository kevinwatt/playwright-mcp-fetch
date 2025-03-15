"""Type definitions for the MCP Fetch server."""

from typing import Dict, Optional
from pydantic import BaseModel, HttpUrl


class RequestPayload(BaseModel):
    """Model for request payload validation."""
    
    url: HttpUrl
    headers: Optional[Dict[str, str]] = None 