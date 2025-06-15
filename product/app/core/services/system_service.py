"""
System service for the Combined Origami Service.

This module contains business logic for system-related operations.
"""

import os
import socket
from datetime import datetime

from core.models.system import SystemInfo, HealthCheck

class SystemService:
    """Service class for system-related business logic."""

    def __init__(self, data_access, settings):
        """Initialize the system service.

        Args:
            data_access: The data access layer instance.
            settings: Application settings.
        """
        self.data_access = data_access
        self.settings = settings

    async def get_system_info(self) -> SystemInfo:
        """Get system information.

        Returns:
            SystemInfo: System information including hostname, IP, and environment details.
        """
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
        except socket.error:
            hostname = "unknown"
            ip_address = "unknown"

        is_container = os.path.exists("/.dockerenv")
        is_kubernetes = os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount")

        return SystemInfo(
            hostname=hostname,
            ip_address=ip_address,
            is_container=is_container,
            is_kubernetes=is_kubernetes,
        )

    async def health_check(self) -> HealthCheck:
        """Perform health check.

        Returns:
            HealthCheck: Health check result with status, timestamp, and version.
        """
        is_healthy = self.data_access.health_check()

        return HealthCheck(
            status="healthy" if is_healthy else "unhealthy",
            timestamp=datetime.now(),
            version=self.settings.app_version,
        )
