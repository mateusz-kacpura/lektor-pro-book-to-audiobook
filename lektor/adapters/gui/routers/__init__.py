"""
lektor.adapters.gui.routers
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Modularne routery FastAPI warstwy adaptera Web GUI.
"""

from .converter import router as converter_router
from .generator import router as generator_router
from .notes import router as notes_router
from .player import router as player_router
from .studio import router as studio_router
from .web import router as web_router

__all__ = [
    "converter_router",
    "generator_router",
    "notes_router",
    "player_router",
    "studio_router",
    "web_router",
]