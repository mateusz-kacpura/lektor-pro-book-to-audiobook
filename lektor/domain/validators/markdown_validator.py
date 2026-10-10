"""
lektor.domain.validators.markdown_validator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Domain service for validating Markdown pages and Mermaid diagrams (Business Rule 14).
Pure business logic — no framework dependencies.
"""

import re
from typing import Sequence

MERMAID_VALID_KEYWORDS: Sequence[str] = (
    "flowchart",
    "graph",
    "sequencediagram",
    "classdiagram",
    "statediagram",
    "erdiagram",
    "gantt",
    "pie",
    "gitgraph",
    "architecture-beta",
)


class MarkdownPageValidationService:
    """Service for verifying correctness and integrity of Markdown pages and Mermaid diagrams."""

    def validate_content_not_empty(self, content: str) -> bool:
        """Checks whether page content is non-empty after stripping whitespace."""
        return bool(content and content.strip())

    def validate_code_blocks(self, content: str) -> bool:
        """Checks whether code block markers (```) are balanced (even count)."""
        backtick_blocks = re.findall(r"```", content)
        return len(backtick_blocks) % 2 == 0

    def validate_mermaid_syntax(self, diagram_code: str) -> bool:
        """
        Verifies whether a Mermaid block starts with an allowed keyword
        and contains valid relationship syntax (->, -->, ---).
        """
        stripped = diagram_code.strip()
        if not stripped:
            return False

        first_line = stripped.splitlines()[0].strip().lower()
        starts_with_keyword = any(first_line.startswith(kw) for kw in MERMAID_VALID_KEYWORDS)
        if not starts_with_keyword:
            return False

        # Implementation note: see the surrounding code for the behavior described here.
        open_brackets = stripped.count("[") + stripped.count("(") + stripped.count("{")
        close_brackets = stripped.count("]") + stripped.count(")") + stripped.count("}")
        return open_brackets == close_brackets

    def validate_page_integrity(self, content: str) -> bool:
        """Verifies complete integrity of a Markdown page."""
        if not self.validate_content_not_empty(content):
            return False
        if not self.validate_code_blocks(content):
            return False

        # Implementation note: see the surrounding code for the behavior described here.
        mermaid_blocks = re.findall(r"```mermaid\n(.*?)```", content, re.DOTALL | re.IGNORECASE)
        for block in mermaid_blocks:
            if not self.validate_mermaid_syntax(block):
                return False

        return True
