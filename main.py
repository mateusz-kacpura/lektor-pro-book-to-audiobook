"""
Main entry point for the Lektor CLI.
Starts the command-line interface through the Interface Adapters layer with the IoC container injected.
"""
import sys

from lektor.adapters.cli.main import main
from lektor.infrastructure.container import default_container

if __name__ == "__main__":
    sys.exit(main(container=default_container))
