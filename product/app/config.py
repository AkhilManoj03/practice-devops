"""
Configuration management for the Combined Origami Service.

This module handles all application settings and environment variable loading.
"""

import logging
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

    # Authentication settings
    auth_service_url: str = "http://authentication:8080"
    product_key_id: str = "product-service-key-1"

    # File paths
    base_dir: Path = Path(__file__).resolve().parent
    products_file: str = "data/products.json"
    templates_dir: str = "templates"
    static_dir: str = "static"

    # Database configuration (required)
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int = 5432

    # Redis configuration (optional for caching)
    redis_host: Optional[str] = None
    redis_port: int = 6379

    # Configure Pydantic to ignore extra fields and load from .env file
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

    def debug_log(self) -> None:
        """Log all settings at debug level if debugging is enabled."""
        logging.debug("Settings configuration:")
        for field_name, value in self.model_dump().items():
            # Don't log sensitive database password
            if field_name == "db_password":
                logging.debug(f"{field_name}: ***")
            else:
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

settings = Settings()
