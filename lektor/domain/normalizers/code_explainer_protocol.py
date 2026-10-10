"""
Protocol defining the interface for verbalizing source code blocks (OCP / DIP).
Strict typing without Any.
"""

from typing import Protocol


class CodeGrammarExplainerProtocol(Protocol):
    """Interface for code syntax translation and phonetic verbalization strategies."""

    def explain_inline(self, code: str) -> str:
        """Converts short inline code fragment into phonetic spoken text."""
        ...

    def explain_block(self, code: str, lang: str = "", mode: str = "spoken") -> str:
        """Converts full code block into descriptive text for speech synthesizer."""
        ...
