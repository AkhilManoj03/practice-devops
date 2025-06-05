# models.py
"""
Pydantic models for the Catalogue Service.

This module contains all data models used for API request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Product(BaseModel):
    """Product model with validation."""
    id: int
    name: str
    description: str
    image_url: str

    model_config = ConfigDict(from_attributes=True)


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
