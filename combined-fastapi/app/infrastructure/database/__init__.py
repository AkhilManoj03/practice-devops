"""
Database layer for data persistence.

This module contains both PostgreSQL and JSON file storage implementations.
"""

from .postgres_manager import PostgresManager
from .json_manager import JSONDataManager

__all__ = ["PostgresManager", "JSONDataManager"]
