"""
Infrastructure layer for the Combined Origami Service.
 
This package contains all data access and external service integrations.
""" 

from .data_access import data_access, DataAccessLayer

__all__ = ["data_access", "DataAccessLayer"]
