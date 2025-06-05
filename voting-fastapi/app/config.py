# config.py
"""
Configuration management for the Voting Service.

This module handles all application settings and environment variable loading.
"""

import logging
from pathlib import Path

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Service URLs
    catalogue_service_url: str = Field(
        default="http://catalogue:8000",
        description="URL of the catalogue service"
    )
    
    # File paths
    votes_file_path: str = Field(
        default="votes.json",
        description="Path to the votes JSON file"
    )
    templates_dir: str = Field(
        default="templates",
        description="Directory containing Jinja2 templates"
    )
    
    # Application settings
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    version: str = Field(
        default="1.0.1",
        description="API version"
    )
    
    # Network settings
    request_timeout: float = Field(
        default=10.0,
        description="HTTP request timeout in seconds"
    )
    
    # Server settings
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind the server to"
    )
    port: int = Field(
        default=8080,
        description="Port to bind the server to"
    )

    model_config = ConfigDict(env_file="app/.env")

    def debug_log(self) -> None:
        """Log all settings at debug level."""
        logging.debug("Settings configuration:")
        for field_name, field in self.model_fields.items():
            value = getattr(self, field_name)
            description = field.description or field_name
            suffix = "s" if field_name == "request_timeout" else ""
            logging.debug(f"{description}: {value}{suffix}")

    def get_templates_path(self) -> Path:
        """Get the full path to templates directory."""
        base_dir = Path(__file__).parent
        return base_dir / self.templates_dir

    def get_votes_file_path(self) -> Path:
        """Get the full path to votes file."""
        return Path(self.votes_file_path)


# Global settings instance
settings = Settings()