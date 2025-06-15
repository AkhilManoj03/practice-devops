"""
Vote service for the Combined Origami Service.

This module contains business logic for voting-related operations.
"""

import logging
from typing import Dict, Any

from core.models.votes import VoteResponse
from core.exceptions import ProductNotFoundError, DataValidationError, DataPersistenceError

class VoteService:
    """Service class for voting business logic."""

    def __init__(self, data_access):
        """Initialize the vote service.

        Args:
            data_access: The data access layer instance.
        """
        self.data_access = data_access

    async def get_votes_for_product(self, product_id: int) -> Dict[str, Any]:
        """Get votes for a specific product.

        Args:
            product_id (int): The ID of the product to get votes for.

        Returns:
            Dict[str, Any]: Dictionary containing product_id and votes.

        Raises:
            DataPersistenceError: If data access fails.
            ProductNotFoundError: If no product exists with the given ID.
        """
        try:
            votes = self.data_access.get_votes_for_product(product_id)
            return {"origami_id": product_id, "votes": votes}
        except DataPersistenceError:
            logging.error(f"Infrastructure error in get_votes_for_product({product_id})")
            raise
        except ProductNotFoundError:
            logging.error(f"Product not found for votes in get_votes_for_product({product_id})")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in get_votes_for_product({product_id}): {e}")
            raise Exception("An unexpected error occurred")

    async def add_vote(self, product_id: int) -> VoteResponse:
        """Vote for a specific product.

        Args:
            product_id (int): The ID of the product to vote for.

        Returns:
            VoteResponse: Response containing vote details.

        Raises:
            DataPersistenceError: If data access fails.
            ProductNotFoundError: If no product exists with the given ID.
        """
        try:
            vote_data = self.data_access.add_vote(product_id)
            return VoteResponse(**vote_data)
        except DataPersistenceError:
            logging.error(f"Infrastructure error in add_vote({product_id})")
            raise
        except ProductNotFoundError:
            logging.error(f"Product not found for vote in add_vote({product_id})")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in add_vote({product_id}): {e}")
            raise Exception("An unexpected error occurred") 
