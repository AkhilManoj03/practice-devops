"""
Pydantic models for the Combined Origami Service.

This module contains all data models used for API request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class Product(BaseModel):
    """Product model with votes included."""
    id: int
    name: str
    description: str
    image_url: str
    votes: int = 0

    model_config = ConfigDict(from_attributes=True)


class VoteResponse(BaseModel):
    """Vote operation response."""
    origami_id: int
    new_vote_count: int
    message: str


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
