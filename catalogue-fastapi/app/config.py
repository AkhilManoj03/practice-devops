# config.py
"""
Configuration management for the Catalogue Service.

This module handles all application settings and environment variable loading.
"""

import logging
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application settings
    app_title: str = "Catalogue Service"
    app_version: str = "1.0.0"
    app_description: str = "Product catalogue management service"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    # Data source configuration
    data_source: str = "json"
    products_file: str = "app/products.json"
    
    # Database settings
    db_host: Optional[str] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_port: int = 5432
    
    # Static files and templates
    static_dir: str = "app/static"
    templates_dir: str = "app/templates"

    model_config = ConfigDict(env_file=".env")

    def debug_log(self) -> None:
        """Log all settings at debug level if debugging is enabled."""
        logging.debug("Settings configuration:")
        for field_name, value in self.model_dump().items():
            logging.debug(f"{field_name}: {value}")

# Global settings instance
settings = Settings()
