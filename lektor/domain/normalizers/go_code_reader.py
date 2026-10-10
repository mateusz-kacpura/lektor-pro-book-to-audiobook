"""Syntactic translator verbalizing Go source code constructs into spoken language."""

from __future__ import annotations

import re
from typing import Callable, Optional

from .go_translators import (
    explain_allocation,
    explain_concurrency,
    explain_control_flow,
    explain_functions_and_methods,
    explain_idiomatic_patterns,
    explain_sync_primitives,
    explain_types_and_fields,
    explain_variables_and_constants,
    polish_args,
    polish_number,
    polish_return_types,
    polish_type,
    polish_type_base,
)

# Implementation note: see the surrounding code for the behavior described here.
__all__ = [
    "GoCodeReader",
    "clean_inline_go_code",
    "polish_args",
    "polish_number",
    "polish_return_types",
    "polish_type",
    "polish_type_base",
]


class GoCodeReader:
    """Translator reading Go syntax constructs phonetically for the listener."""

    # Implementation note: see the surrounding code for the behavior described here.
    _TRANSLATOR_HANDLERS: list[Callable[[str], Optional[str]]] = [
        explain_concurrency,
        explain_sync_primitives,
        explain_allocation,
        explain_functions_and_methods,
        explain_variables_and_constants,
        explain_control_flow,
        explain_types_and_fields,
        explain_idiomatic_patterns,
    ]

    @classmethod
    def explain_code_block(cls, code_content: str, lang: str = "go") -> str:
        """Tlumaczy kompletny blok kodu Go na polski tekst narracyjny."""
        _ = lang
        code = code_content.strip()
        if not code:
            return ""

        interface_description = cls._explain_interface_block(code)
        if interface_description is not None:
            return interface_description

        struct_description = cls._explain_struct_block(code)
        if struct_description is not None:
            return struct_description

        return cls._explain_sequential_block(code)

    @staticmethod
    def _explain_interface_block(code: str) -> Optional[str]:
        interface_match = re.search(
            r"^type\s+(\w+)(?:\[.*?\])?\s+interface\s*\{([^}]*)\}",
            code,
            re.MULTILINE | re.DOTALL,
        )
        if interface_match is None:
            return None

        name = interface_match.group(1)
        body = interface_match.group(2).strip()
        lines = [
            line_item.strip()
            for line_item in body.splitlines()
            if line_item.strip() and not line_item.strip().startswith("//")
        ]
        description = (
            f"Pocz\u0105tek fragmentu kodu. Deklaracja interfejsu {name}. "
            f"W j\u0119zyku Go interfejsy stanowi\u0105 podstaw\u0119 polimorfizmu "
            f"opartego na strukturalnym dopasowaniu kontraktu. "
        )
        if lines:
            description += f"Interfejs definiuje nast\u0119puj\u0105ce metody: {'; '.join(lines)}. "
        else:
            description += "Interfejs jest pusty i akceptuje dowolne typy danych. "
        return description + "Koniec fragmentu kodu."

    @staticmethod
    def _explain_struct_block(code: str) -> Optional[str]:
        struct_match = re.search(
            r"^type\s+(\w+)(?:\[.*?\])?\s+struct\s*\{([^}]*)\}",
            code,
            re.MULTILINE | re.DOTALL,
        )
        if struct_match is None:
            return None

        name = struct_match.group(1)
        body = struct_match.group(2).strip()
        lines = [
            line_item.strip()
            for line_item in body.splitlines()
            if line_item.strip() and not line_item.strip().startswith("//")
        ]
        embedded: list[str] = []
        named_fields: list[str] = []

        for line in lines:
            clean_line = line.split("//")[0].strip()
            tag_match = re.search(r"\x60([^\x60]+)\x60", clean_line)
            tag_description = ""
            if tag_match:
                clean_line = clean_line[: tag_match.start()].strip()
                tag_description = f" z metadanymi tagu {tag_match.group(1)}"

            parts = clean_line.split()
            if len(parts) == 1:
                embedded.append(parts[0])
            elif len(parts) >= 2:
                named_fields.append(f"pole {parts[0]} {polish_type(' '.join(parts[1:]))}{tag_description}")

        description = f"Pocz\u0105tek fragmentu kodu. Definicja struktury {name}. "
        if embedded and not named_fields:
            description += (
                f"Wykorzystuje kompozycj\u0119 i anonimowe osadzenie typ\u00f3w: {', '.join(embedded)}. "
                "Pola i metody osadzonych struktur s\u0105 automatycznie promowane."
            )
        elif embedded and named_fields:
            description += (
                f"Zawiera osadzone typy: {', '.join(embedded)} oraz bezpo\u015brednie definicje: "
                f"{', '.join(named_fields)}."
            )
        elif named_fields:
            description += f"Struktura posiada pola: {', '.join(named_fields)}."
        else:
            description += (
                "Jest to pusta struktura struct, cz\u0119sto wykorzystywana jako znacznik "
                "sygnalizacyjny bez alokacji pami\u0119ci."
            )
        return description + " Koniec fragmentu kodu."

    @classmethod
    def _explain_sequential_block(cls, code: str) -> str:
        lines = [line.strip() for line in code.splitlines() if line.strip()]
        spoken_parts: list[str] = []
        in_select = False
        in_switch = False

        for line in lines:
            if line in ("{", "}", "};", "}()", "});"):
                if in_select and line == "}":
                    in_select = False
                if in_switch and line == "}":
                    in_switch = False
                continue

            comment_part = ""
            if "//" in line:
                parts = line.split("//", 1)
                line = parts[0].strip()
                comment_part = parts[1].strip()

            if not line:
                if comment_part:
                    spoken_parts.append(f"Komentarz w kodzie: {comment_part}.")
                continue

            if line.startswith("select") and "{" in line:
                in_select = True
                spoken_parts.append(
                    "Instrukcja wyboru select, multiplexuj\u0105ca asynchroniczne operacje na kana\u0142ach:"
                )
                continue

            if line.startswith("switch") and "{" in line:
                in_switch = True
                spoken_parts.append("Instrukcja warunkowa switch:")
                continue

            explanation = cls.explain_statement(line)
            if comment_part:
                explanation = f"{explanation} Komentarz: {comment_part}."
            spoken_parts.append(explanation)

        body_text = " ".join(spoken_parts)
        return f"Pocz\u0105tek fragmentu kodu w j\u0119zyku Go: {body_text} Koniec fragmentu kodu."

    @classmethod
    def explain_statement(cls, stmt: str) -> str:
        """Translates a single Go statement using a chain of translators."""
        stmt = stmt.strip()
        if not stmt:
            return ""

        for handler in cls._TRANSLATOR_HANDLERS:
            res = handler(stmt)
            if res is not None:
                return res

        fallback = stmt.replace(":=", " deklaracja i przypisanie ")
        fallback = fallback.replace("!=", " rĂłĹĽne od ").replace("==", " rĂłwne ")
        fallback = fallback.replace("<-", " odbiĂłr lub wysĹ‚anie do kanaĹ‚u ")
        fallback = fallback.replace("&&", " oraz ").replace("||", " lub ")
        return fallback


def clean_inline_go_code(code_str: str) -> str:
    """Translates short Go code fragments embedded inline in markdown text."""
    code_str = code_str.strip()
    if not code_str:
        return ""

    # Implementation note: see the surrounding code for the behavior described here.
    triggers = (
        ":=",
        "<-",
        "make(",
        "var ",
        "func ",
        "type ",
        "err !=",
        "go ",
        "defer ",
        ".Lock()",
        ".Unlock()",
        ".Wait()",
    )
    if any(op in code_str for op in triggers):
        explained = GoCodeReader.explain_statement(code_str)
        if explained != code_str:
            return explained

    # Implementation note: see the surrounding code for the behavior described here.
    if code_str.startswith("*") and len(code_str) > 1:
        return f"wskaĹşnik na {polish_type_base(code_str[1:])}"
    if code_str.startswith("&") and len(code_str) > 1:
        return f"pobranie adresu wskaĹşnikowego zmiennej {code_str[1:]}"

    # Slices and arrays
    if code_str.startswith("[]"):
        return f"wycinek {polish_type_base(code_str[2:])}"

    m_arr = re.match(r"^\[(\d+)\](.+)$", code_str)
    if m_arr:
        return f"tablica o rozmiarze {polish_number(m_arr.group(1))} elementĂłw typu {polish_type_base(m_arr.group(2))}"

    if code_str.startswith("chan "):
        return f"kanaĹ‚ typu {polish_type_base(code_str[5:])}"

    # Implementation note: see the surrounding code for the behavior described here.
    from .go_translators.keywords import GO_INLINE_KEYWORDS

    return GO_INLINE_KEYWORDS.get(code_str, polish_type_base(code_str))
