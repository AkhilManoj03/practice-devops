"""
System-related models for the Combined Origami Service.

This module contains Pydantic models related to system information and health checks.
"""

from datetime import datetime
from pydantic import BaseModel

class SystemInfo(BaseModel):
    """System information model."""
    hostname: str
    ip_address: str
    is_container: bool
    is_kubernetes: bool

class HealthCheck(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
