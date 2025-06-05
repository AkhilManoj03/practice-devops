"""
Configuration management for the Combined Origami Service.

This module handles all application settings and environment variable loading.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application settings
    app_title: str = "Combined Origami Service"
    app_version: str = "1.0.0"
    app_description: str = "Combined product catalogue and voting service"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    # Data source configuration
    data_source: str = "json"  # "json" or "database"
    
    # File paths
    base_dir: Path = Path(__file__).resolve().parent
    products_file: str = "app/products.json"
    templates_dir: str = "app/templates"
    static_dir: str = "app/static"
    
    # Database configuration
    db_host: Optional[str] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_port: int = 5432
    
    # Redis configuration
    redis_host: Optional[str] = None
    redis_port: int = 6379

    # Configure Pydantic to ignore extra fields and load from .env file
    model_config = ConfigDict(
        env_file="app/.env",
        extra="ignore"
    )

    def debug_log(self) -> None:
        """Log all settings at debug level if debugging is enabled."""
        logging.debug("Settings configuration:")
        for field_name, value in self.model_dump().items():
            logging.debug(f"{field_name}: {value}")

    def get_products_file_path(self) -> Path:
        """Get the full path to the products JSON file.
        
        Returns:
            Path: Full path to products.json
        """
        return self.base_dir / self.products_file

    def get_templates_dir(self) -> str:
        """Get the full path to the templates directory.
        
        Returns:
            str: Full path to templates directory
        """
        return str(self.base_dir / self.templates_dir)

    def get_static_dir(self) -> str:
        """Get the full path to the static directory.
        
        Returns:
            str: Full path to static directory
        """
        return str(self.base_dir / self.static_dir)


# Global settings instance
settings = Settings() 