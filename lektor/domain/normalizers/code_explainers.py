"""
Concrete implementations of code verbalization strategies for Go and general code.
Interface Adapters & Domain Layer.
"""

import re

from .code_explainer_protocol import CodeGrammarExplainerProtocol
from .go_code_reader import GoCodeReader, clean_inline_go_code
from .go_translators.keywords import GO_KEYWORDS_REGEX_PATTERNS
from .symbols import normalize_special_characters


class GenericCodeGrammarExplainer(CodeGrammarExplainerProtocol):
    """Generic phonetic code explainer for languages such as Python, YAML, Shell, JSON."""

    def explain_inline(self, code: str) -> str:
        cleaned = code.strip()
        if not cleaned:
            return ""
        cleaned = normalize_special_characters(cleaned)
        cleaned = cleaned.replace("{", "").replace("}", "").replace(";", "")
        return re.sub(r"\s+", " ", cleaned).strip()

    def explain_block(self, code: str, lang: str = "", mode: str = "spoken") -> str:
        if mode == "skip":
            return "PominiÄ™to listing kodu."

        lines = [line.strip() for line in code.strip().split("\n") if line.strip()]
        if not lines:
            return ""

        if mode == "summary":
            return f"Listing kodu w jÄ™zyku {lang or 'tekstowym'}, zawierajÄ…cy {len(lines)} linii kodu."

        spoken_lines: list[str] = []
        for line in lines:
            if line in ["{", "}", "()", "};"]:
                continue

            comment_part = ""
            if "//" in line:
                parts = line.split("//", 1)
                line = parts[0].strip()
                comment_part = parts[1].strip()
            elif "#" in line:
                parts = line.split("#", 1)
                line = parts[0].strip()
                comment_part = parts[1].strip()

            line_spoken = self.explain_inline(line) if line else ""
            if comment_part:
                if line_spoken:
                    spoken_lines.append(f"{line_spoken}. Komentarz: {comment_part}.")
                else:
                    spoken_lines.append(f"Komentarz: {comment_part}.")
            elif line_spoken:
                spoken_lines.append(f"{line_spoken}.")

        intro = f"PoczÄ…tek fragmentu kodu {lang if lang else ''}: "
        outro = " Koniec fragmentu kodu."
        return intro + " ".join(spoken_lines) + outro


class GoCodeGrammarExplainer(CodeGrammarExplainerProtocol):
    """Dedicated semantic code explainer for Go language using GoCodeReader."""

    def explain_inline(self, code: str) -> str:
        cleaned = code.strip()
        if not cleaned:
            return ""

        explained = clean_inline_go_code(cleaned)
        if explained != cleaned:
            return explained

        for pattern, rep in GO_KEYWORDS_REGEX_PATTERNS.items():
            cleaned = re.sub(pattern, rep, cleaned)

        cleaned = normalize_special_characters(cleaned)
        cleaned = cleaned.replace("{", "").replace("}", "").replace(";", "")
        return re.sub(r"\s+", " ", cleaned).strip()

    def explain_block(self, code: str, lang: str = "go", mode: str = "spoken") -> str:
        if mode == "skip":
            return "PominiÄ™to listing kodu."

        lines = [line.strip() for line in code.strip().split("\n") if line.strip()]
        if not lines:
            return ""

        if mode == "summary":
            return f"Listing kodu w jÄ™zyku {lang or 'Go'}, zawierajÄ…cy {len(lines)} linii kodu."

        lang_clean = (lang or "go").strip().lower()
        if lang_clean in ("go", "golang", ""):
            return GoCodeReader.explain_code_block(code, lang="go")

        # Implementation note: see the surrounding code for the behavior described here.
        generic = GenericCodeGrammarExplainer()
        return generic.explain_block(code, lang=lang, mode=mode)
