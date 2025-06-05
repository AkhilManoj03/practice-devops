# models.py
"""
Pydantic models for the Voting Service.

This module contains all data models used for API request/response validation
and internal data structures.
"""

from pydantic import BaseModel, ConfigDict

class Origami(BaseModel):
    """Base origami model."""
    name: str
    description: str
    image_url: str

class OrigamiResponse(Origami):
    """Origami response model with votes."""
    id: int
    votes: int

    model_config = ConfigDict(from_attributes=True)

class VoteResponse(BaseModel):
    """Vote operation response."""
    origami_id: int
    new_vote_count: int
    message: str

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
