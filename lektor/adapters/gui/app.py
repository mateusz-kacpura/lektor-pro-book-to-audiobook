"""
lektor.adapters.gui.app
~~~~~~~~~~~~~~~~~~~~~~~
Main FastAPI application adapter for the Web GUI.
"""

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers.converter import wait_for_conversion_tasks
from ...application.ports.container_ports import ApplicationContainerProtocol
from .paths import GuiPaths
from .routers import (
    converter_router,
    generator_router,
    notes_router,
    player_router,
    studio_router,
    web_router,
)


def create_app(
    container: ApplicationContainerProtocol,
    gui_paths: GuiPaths,
) -> FastAPI:
    """FastAPI application factory injecting the IoC container into application state."""
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            wait_for_conversion_tasks()
            container.shutdown()

    app_instance = FastAPI(title="Lektor Pro â€” Cloud Native in Go Audiobook",
        lifespan=lifespan,
    )

    # Implementation note: see the surrounding code for the behavior described here.
    app_instance.state.container = container
    app_instance.state.gui_paths = gui_paths

    # CORS configuration
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Implementation note: see the surrounding code for the behavior described here.
    app_instance.mount("/static", StaticFiles(directory=gui_paths.static_dir), name="static")

    if gui_paths.images_dir.exists():
        app_instance.mount("/images", StaticFiles(directory=gui_paths.images_dir), name="images")

    if gui_paths.pdf_pages_dir.exists():
        app_instance.mount("/pdf_pages_jpg", StaticFiles(directory=gui_paths.pdf_pages_dir), name="pdf_pages_jpg")

    # Implementation note: see the surrounding code for the behavior described here.
    app_instance.include_router(web_router)
    app_instance.include_router(player_router)
    app_instance.include_router(converter_router)
    app_instance.include_router(generator_router)
    app_instance.include_router(notes_router)
    app_instance.include_router(studio_router)

    return app_instance



__all__ = ["create_app"]
