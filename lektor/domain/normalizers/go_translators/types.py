"""
lektor.domain.normalizers.go_translators.types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Translator for Go data types, argument signatures, return values, structs, and interfaces.
Strict typing without Any.
"""

from __future__ import annotations

import re
from typing import Optional

from ..numbers import int_to_polish_words
from .keywords import GO_PRIMITIVE_TYPES


def polish_number(n_str: str) -> str:
    """Converts integers to spoken words via the numbers module."""
    n_str = n_str.strip()
    try:
        n = int(n_str)
        return int_to_polish_words(n)
    except ValueError:
        return n_str.replace(".", " przecinek ")


def polish_type_base(t: str) -> str:
    """Translates Go type into grammatical Polish case, supporting composite types."""
    t = t.strip()
    if not t:
        return ""

    # Base types
    if t in GO_PRIMITIVE_TYPES:
        return GO_PRIMITIVE_TYPES[t]

    # Implementation note: see the surrounding code for the behavior described here.
    if t.startswith("**"):
        return f"podwĂłjny wskaĹşnik na {polish_type_base(t[2:])}"
    if t.startswith("*"):
        return f"wskaĹşnik na {polish_type_base(t[1:])}"

    # Slices and arrays
    if t.startswith("[]"):
        inner = t[2:]
        if inner == "byte":
            return "wycinek bajtĂłw slice of bytes"
        return f"wycinek elementĂłw typu {polish_type_base(inner)}"

    m_arr = re.match(r"^\[(\d+)\](.+)$", t)
    if m_arr:
        count = polish_number(m_arr.group(1))
        elem_t = polish_type_base(m_arr.group(2))
        return f"tablica o staĹ‚ym rozmiarze {count} elementĂłw typu {elem_t}"

    # Implementation note: see the surrounding code for the behavior described here.
    if t.startswith("chan "):
        return f"dwukierunkowy kanaĹ‚ przesyĹ‚ajÄ…cy {polish_type_base(t[5:])}"
    if t.startswith("<-chan "):
        return f"jednokierunkowy kanaĹ‚ odbiorczy dla typu {polish_type_base(t[7:])}"
    if t.startswith("chan<- "):
        return f"jednokierunkowy kanaĹ‚ nadawczy dla typu {polish_type_base(t[7:])}"

    # Maps
    m_map = re.match(r"^map\[([^\]]+)\](.+)$", t)
    if m_map:
        k_type = polish_type_base(m_map.group(1))
        v_type = polish_type_base(m_map.group(2))
        return f"mapa z kluczami typu {k_type} oraz wartoĹ›ciami typu {v_type}"

    # Generic types e.g. List[T]
    m_gen = re.match(r"^([a-zA-Z0-9_.]+)\[([^\]]+)\]$", t)
    if m_gen:
        base_name = m_gen.group(1)
        args = [polish_type_base(a.strip()) for a in m_gen.group(2).split(",")]
        return f"typ sparametryzowany {base_name} z parametrami: {', '.join(args)}"

    return t


def polish_type(t: str) -> str:
    """Returns full grammatical phrase 'of type X'."""
    return f"typu {polish_type_base(t)}"


def polish_args(args_str: str) -> str:
    """Translates function parameter lists, including variadic parameters."""
    args_str = args_str.strip()
    if not args_str:
        return "nieprzyjmujÄ…ca ĹĽadnych argumentĂłw"

    raw_items = [a.strip() for a in args_str.split(",") if a.strip()]
    formatted = []

    for item in raw_items:
        # Implementation note: see the surrounding code for the behavior described here.
        if "..." in item:
            parts = item.split("...")
            param_name = parts[0].strip()
            param_t = polish_type_base(parts[1].strip())
            formatted.append(f"zmienna liczba argumentĂłw {param_name} typu {param_t}")
            continue

        parts = item.split()
        if len(parts) >= 2:
            name = parts[0]
            t = " ".join(parts[1:])
            formatted.append(f"argument {name} {polish_type(t)}")
        else:
            formatted.append(f"argument anonimowy {polish_type(item)}")

    return "przyjmujÄ…ca: " + ", ".join(formatted)


def polish_return_types(ret_str: str) -> str:
    """Translates return type signatures (single or tuples)."""
    ret_str = ret_str.strip()
    if not ret_str:
        return ""

    if ret_str.startswith("(") and ret_str.endswith(")"):
        ret_str = ret_str[1:-1].strip()

    rets = [r.strip() for r in ret_str.split(",") if r.strip()]
    if not rets:
        return ""

    if len(rets) == 1:
        return f", zwracajÄ…ca wartoĹ›Ä‡ {polish_type(rets[0])}"

    desc = []
    for r in rets:
        parts = r.split()
        if len(parts) >= 2:
            desc.append(f"nazwanÄ… wartoĹ›Ä‡ {parts[0]} {polish_type(' '.join(parts[1:]))}")
        else:
            desc.append(f"wartoĹ›Ä‡ {polish_type(r)}")

    return f", zwracajÄ…ca krotkÄ™ wartoĹ›ci: {', '.join(desc)}"


def explain_types_and_fields(stmt: str) -> Optional[str]:
    """Translates struct, interface, alias, and field declarations."""
    m_st_head = re.match(r"^type\s+(\w+)(?:\[.*?\])?\s+struct\s*\{?$", stmt)
    if m_st_head:
        return f"Deklaracja struktury {m_st_head.group(1)}:"

    m_if_head = re.match(r"^type\s+(\w+)(?:\[.*?\])?\s+interface\s*\{?$", stmt)
    if m_if_head:
        return f"Deklaracja interfejsu {m_if_head.group(1)} definiujÄ…cego kontrakt:"

    m_type_alias = re.match(r"^type\s+(\w+)\s*=\s*(.+)$", stmt)
    if m_type_alias:
        return f"Definicja aliasu typu {m_type_alias.group(1)} dla {polish_type_base(m_type_alias.group(2))}."

    m_type_def = re.match(r"^type\s+(\w+)\s+([a-zA-Z0-9_.*\[\]]+)$", stmt)
    if m_type_def:
        return f"Definicja nowego silnego typu {m_type_def.group(1)} bazujÄ…cego na {polish_type_base(m_type_def.group(2))}."

    m_field = re.match(r"^([A-Z]\w*)\s+([a-zA-Z0-9_.*\[\]]+)(?:\s+`([^`]+)`)?$", stmt)
    if m_field:
        tag_info = f" z tagiem {m_field.group(3)}" if m_field.group(3) else ""
        return f"pole {m_field.group(1)} {polish_type(m_field.group(2))}{tag_info}."

    return None
