"""
Database layer for data persistence.

This module contains PostgreSQL storage implementation.
"""

from .postgres_manager import PostgresManager

__all__ = ["PostgresManager"]
