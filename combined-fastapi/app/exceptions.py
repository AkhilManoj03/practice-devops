"""
Custom exceptions for the Combined Origami Service.

This module defines business-specific exceptions for better error handling.
"""


class DataAccessError(Exception):
    """Base exception for data access errors."""
    pass


class ProductNotFoundError(DataAccessError):
    """Raised when a product is not found."""
    pass


class DataValidationError(DataAccessError):
    """Raised when data validation fails."""
    pass


class DataPersistenceError(DataAccessError):
    """Raised when data cannot be saved or loaded."""
    pass 