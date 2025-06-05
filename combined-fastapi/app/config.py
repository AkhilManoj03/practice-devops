"""
Configuration management for the Combined Origami Service.

This module handles all application settings and environment variable loading.
"""

import logging
from pathlib import Path
from typing import Optional

from pydantic import Field, ConfigDict
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
    products_file: str = "app/products.json"
    
    # Database settings (for future use)
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

    def get_templates_path(self) -> Path:
        """Get the full path to templates directory."""
        base_dir = Path(__file__).parent
        return base_dir / self.templates_dir

    def get_products_file_path(self) -> Path:
        """Get the full path to products file."""
        return Path(self.products_file)


# Global settings instance
settings = Settings() 