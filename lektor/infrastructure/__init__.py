"""
Frameworks & Drivers Layer.
Contains environment configuration, device detection, and IoC container.
"""

from .config import InfrastructureSettings, resolve_device, settings

__all__ = ["InfrastructureSettings", "resolve_device", "settings"]
