"""Markdown formatter adapter adding page metadata and formatting code."""

import json
import re
from typing import Optional

from ...application.ports.ocr_ports import BookMarkdownFormatterProtocol
from ...domain.conversion_models import PageNumber


class DefaultBookMarkdownFormatter(BookMarkdownFormatterProtocol):
    """Formatter generating standardized Markdown documents."""

    def __init__(self, default_book_title: Optional[str] = None) -> None:
        self.default_book_title = default_book_title

    def format_markdown(
        self,
        raw_md: str,
        page_num: PageNumber,
        img_name: str,
        book_dir_name: str = "scans",
    ) -> str:
        """Formats markdown content with YAML frontmatter header."""
        page_int = int(page_num)
        non_empty_lines = [line.strip() for line in raw_md.splitlines() if line.strip()]

        title = f"Strona {page_int:03d}"
        body_lines = list(non_empty_lines)

        if non_empty_lines:
            first_line = non_empty_lines[0]
            clean_first = re.sub(r"^[#\s\*\-]+", "", first_line).strip()
            if clean_first and len(clean_first) < 120 and not clean_first.lower().startswith("strona"):
                title = clean_first
                body_lines = non_empty_lines[1:]

        content_body = "\n\n".join(body_lines).strip()

        book_name = self.default_book_title or book_dir_name.replace("_", " ").title()
        metadata_dict = {
            "title": f"{book_name} - Strona {page_int}",
            "page_number": page_int,
            "original_file": f"{book_dir_name}/{img_name}",
            "scan_file": f"/{book_dir_name}/{img_name}",
        }
        metadata_json = json.dumps(metadata_dict, indent=2, ensure_ascii=False)
        metadata_block = f"<!--\n{metadata_json}\n-->"

        scan_footer = f"\n---\n*Oryginalny skan strony:*\n![Skan strony {page_int}](/{book_dir_name}/{img_name})\n"

        return f"{metadata_block}\n\n# Strona {page_int:03d} — {title}\n\n{content_body}\n{scan_footer}"
