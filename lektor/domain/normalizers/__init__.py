"""
Text and source code normalization rules package for TTS synthesis.
Domain Layer.
"""

from .code_cleaner import clean_inline_code, process_code_block
from .dictionary import apply_pronunciation_rules
from .language import detect_language
from .markdown import clean_markdown_document, clean_markdown_structure
from .numbers import normalize_numbers_and_symbols
from .symbols import normalize_special_characters

__all__ = [
    "clean_inline_code",
    "process_code_block",
    "apply_pronunciation_rules",
    "detect_language",
    "clean_markdown_document",
    "clean_markdown_structure",
    "normalize_numbers_and_symbols",
    "normalize_special_characters",
]
