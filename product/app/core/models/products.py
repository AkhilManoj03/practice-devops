"""
Product-related models for the Combined Origami Service.

This module contains Pydantic models related to products.
"""

from pydantic import BaseModel, ConfigDict

class Product(BaseModel):
    """Product model with votes included."""
    id: int
    name: str
    description: str
    image_url: str
    votes: int = 0

    model_config = ConfigDict(from_attributes=True)
