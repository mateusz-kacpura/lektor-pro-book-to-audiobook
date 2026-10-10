"""Composition Root for the web application."""

from fastapi import FastAPI

from ..adapters.gui.app import create_app
from .container import default_container


def build_default_app() -> FastAPI:
    """Creates the GUI application with infrastructure dependencies."""
    return create_app(
        container=default_container,
        gui_paths=default_container.get_gui_paths(),
    )


app: FastAPI = build_default_app()
