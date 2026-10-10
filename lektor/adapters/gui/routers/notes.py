"""
lektor.adapters.gui.routers.notes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Router handling reading and writing user Markdown notes.
Dependency Inversion (DIP) with NotesRepositoryProtocol injected via FastAPI Depends.
Strict typing without Any.
"""

import re

from fastapi import APIRouter, Depends

from ....application.ports.storage_ports import NotesRepositoryProtocol
from ..dependencies import get_notes_repository
from ..schemas import NoteSaveRequest

router = APIRouter(tags=["Notes"])


@router.get("/api/notes/{note_id}")
def get_note(
    note_id: str,
    notes_repo: NotesRepositoryProtocol = Depends(get_notes_repository),
) -> dict[str, object]:
    """Retrieves note content from notes repository."""
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "", note_id) or "global"
    content = notes_repo.get_note(safe_id)
    return {"note_id": safe_id, "content": content}


@router.post("/api/notes")
def save_note(
    req: NoteSaveRequest,
    notes_repo: NotesRepositoryProtocol = Depends(get_notes_repository),
) -> dict[str, object]:
    """Saves note content to notes repository."""
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "", req.note_id) or "global"
    saved_path = notes_repo.save_note(safe_id, req.content)
    return {
        "status": "saved",
        "note_id": safe_id,
        "path": str(saved_path.resolve()),
        "length": len(req.content),
    }
