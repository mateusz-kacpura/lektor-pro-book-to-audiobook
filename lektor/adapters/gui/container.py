"""
lektor.adapters.gui.container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
GUI dependency container providing access to application adapters.
"""

from ...application.ports.container_ports import ApplicationContainerProtocol

# Implementation note: see the surrounding code for the behavior described here.
ApplicationContainer = ApplicationContainerProtocol

__all__ = ["ApplicationContainerProtocol", "ApplicationContainer"]
