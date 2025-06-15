"""
Vote-related models for the Combined Origami Service.

This module contains Pydantic models related to voting operations.
"""

from pydantic import BaseModel

class VoteResponse(BaseModel):
    """Vote operation response."""
    origami_id: int
    new_vote_count: int
    message: str
