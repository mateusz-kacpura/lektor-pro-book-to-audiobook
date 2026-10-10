"""Markdown and Go code block cleaning and normalization for speech synthesis."""

from typing import Optional

from .code_explainer_protocol import CodeGrammarExplainerProtocol
from .code_explainers import GoCodeGrammarExplainer
from .go_translators.keywords import GO_KEYWORDS_REGEX_PATTERNS, GO_OPERATORS_MAP

# Implementation note: see the surrounding code for the behavior described here.
OPERATORS_MAP = GO_OPERATORS_MAP
GO_KEYWORDS_SPOKEN = GO_KEYWORDS_REGEX_PATTERNS


def clean_inline_code(code_str: str, explainer: Optional[CodeGrammarExplainerProtocol] = None) -> str:
    """Converts inline code fragments to spoken text using CodeGrammarExplainerProtocol."""
    active = explainer if explainer is not None else GoCodeGrammarExplainer()
    return active.explain_inline(code_str)


def process_code_block(
    code_content: str,
    lang: str = "go",
    mode: str = "spoken",
    explainer: Optional[CodeGrammarExplainerProtocol] = None,
) -> str:
    """Processes full code block into descriptive spoken text using CodeGrammarExplainerProtocol."""
    active = explainer if explainer is not None else GoCodeGrammarExplainer()
    return active.explain_block(code_content, lang=lang, mode=mode)
