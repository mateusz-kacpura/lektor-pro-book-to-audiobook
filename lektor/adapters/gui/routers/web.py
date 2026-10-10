"""
lektor.adapters.gui.routers.web
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Router handling HTML views and static assets for the Web GUI application.
Uses Jinja2Templates for modular template rendering.
Strict typing without Any.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from ..dependencies import get_gui_paths
from ..paths import GuiPaths

router = APIRouter(tags=["Web Views"])


@router.get("/static/{file_path:path}")
def serve_static_fallback(
    file_path: str,
    paths: GuiPaths = Depends(get_gui_paths),
) -> FileResponse:
    """Fallback endpoint serving static CSS/JS files."""
    target = paths.static_dir / file_path
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Static file not found")
    media_type = "text/css" if file_path.endswith(".css") else ("application/javascript" if file_path.endswith(".js") else None)
    return FileResponse(path=target, media_type=media_type)


@router.get("/", response_class=HTMLResponse)
def index_page(
    request: Request,
    paths: GuiPaths = Depends(get_gui_paths),
) -> HTMLResponse:
    """Serves main HTML template with Jinja2 modular components."""
    template_path = paths.templates_dir / "index.html"
    if not template_path.exists():
        return HTMLResponse(content="<h1>Szablon GUI nie został jeszcze utworzony.</h1>")

    templates = Jinja2Templates(directory=str(paths.templates_dir))
    return templates.TemplateResponse(request=request, name="index.html")