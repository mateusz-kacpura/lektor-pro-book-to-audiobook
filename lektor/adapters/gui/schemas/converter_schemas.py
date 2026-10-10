"""
lektor.adapters.gui.schemas.converter_schemas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pydantic request and response schemas for book and PDF conversion router.
Strict typing without Any.
"""

from typing import Optional

from pydantic import BaseModel, Field


class SwitchBookRequest(BaseModel):
    slug: str = Field(..., description="Znormalizowany slug docelowej książki")


class BookPdfInfoResponse(BaseModel):
    book_slug: str
    title: str
    pdf_path: Optional[str] = None
    pdf_exists: bool = False
    pages_count: int = 0
    scans_count: int = 0
    total_pages: int = 0
    language: str = "pl"


class StartConversionRequest(BaseModel):
    pdf_path: str = Field(..., description="Ścieżka do źródłowego pliku PDF na dysku")
    book_slug: str = Field(..., description="Unikalny identyfikator książki (slug)")
    dpi: int = Field(default=300, description="Rozdzielczość renderowania skanów")
    target_language: str = Field(default="pl", description="Język docelowy Markdown (np. pl, en, de, fr, es, uk, ja, itd.)")
    source_language: Optional[str] = Field(default=None, description="Opcjonalny język źródłowy w pliku PDF (np. en, de)")
    custom_prompt: Optional[str] = Field(default=None, description="Opcjonalny prompt dla modelu AI")
    start_page: Optional[int] = Field(default=None, description="Pierwsza strona do konwersji")
    end_page: Optional[int] = Field(default=None, description="Ostatnia strona do konwersji")
    skip_existing: bool = Field(default=True, description="Pomiń strony posiadające już plik Markdown")
    model_name: Optional[str] = Field(default=None, description="Opcjonalny identyfikator modelu wizyjnego AI")


class StartConversionResponse(BaseModel):
    task_id: str
    status: str
    message: str


class RenderScansRequest(BaseModel):
    book_slug: str = Field(..., description="Znormalizowany slug docelowej książki")
    dpi: int = Field(default=300, description="Rozdzielczość renderowania skanów")
    start_page: Optional[int] = Field(default=None, description="Pierwsza strona do renderowania")
    end_page: Optional[int] = Field(default=None, description="Ostatnia strona do renderowania")


class RenderScansResponse(BaseModel):
    book_slug: str
    scans_created: int
    scans_dir: str
    total_scans: int
    message: str