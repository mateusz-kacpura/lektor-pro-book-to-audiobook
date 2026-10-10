"""
lektor.domain.normalizers.go_translators.statements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Translator for allocation instructions (make, new, append), functions, variables, control flow, and Go idioms.
Strict typing without Any.
"""

from __future__ import annotations

import re
from typing import Optional

from .types import (
    polish_args,
    polish_number,
    polish_return_types,
    polish_type,
    polish_type_base,
)


def explain_allocation(stmt: str) -> Optional[str]:
    """Translates memory allocation statements: make, new, append."""
    # make for slice with len and cap
    m = re.match(
        r"^(?:var\s+)?(\w+)\s*(?::=|=)\s*make\(\s*\[\]([a-zA-Z0-9_.*]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$",
        stmt,
    )
    if m:
        var_name, t, length, cap_val = m.group(1), m.group(2), polish_number(m.group(3)), polish_number(m.group(4))
        unit = "bajtĂłw" if t == "byte" else "elementĂłw"
        return (
            f"Alokacja wycinka {polish_type_base(t)} o nazwie {var_name} funkcjÄ… make, "
            f"o dĹ‚ugoĹ›ci poczÄ…tkowej {length} oraz pojemnoĹ›ci {cap_val} {unit}."
        )

    # make for slice with len only
    m = re.match(r"^(?:var\s+)?(\w+)\s*(?::=|=)\s*make\(\s*\[\]([a-zA-Z0-9_.*]+)\s*,\s*(\d+)\s*\)$", stmt)
    if m:
        var_name, t, length = m.group(1), m.group(2), polish_number(m.group(3))
        unit = "bajtĂłw" if t == "byte" else "elementĂłw"
        return f"Alokacja wycinka {polish_type_base(t)} o nazwie {var_name} funkcjÄ… make o dĹ‚ugoĹ›ci {length} {unit}."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^(?:var\s+)?(\w+)\s*(?::=|=)\s*make\(\s*chan\s+([a-zA-Z0-9_.*]+)\s*,\s*(\d+)\s*\)$", stmt)
    if m:
        var_name, t, cap_val = m.group(1), m.group(2), polish_number(m.group(3))
        return (
            f"Utworzenie buforowanego kanaĹ‚u {var_name} dla typu {polish_type_base(t)} "
            f"o pojemnoĹ›ci bufora {cap_val} elementĂłw."
        )

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^(?:var\s+)?(\w+)\s*(?::=|=)\s*make\(\s*chan\s+([a-zA-Z0-9_.*]+)\s*\)$", stmt)
    if m:
        var_name, t = m.group(1), m.group(2)
        return (
            f"Utworzenie niebuforowanego kanaĹ‚u {var_name} dla typu {polish_type_base(t)}. "
            f"KanaĹ‚ wymaga jednoczesnej gotowoĹ›ci nadawcy i odbiorcy."
        )

    # make for map
    m = re.match(r"^(?:var\s+)?(\w+)\s*(?::=|=)\s*make\(\s*map\[([^\]]+)\]([a-zA-Z0-9_.*]+)\s*\)$", stmt)
    if m:
        var_name, k, v = m.group(1), m.group(2), m.group(3)
        return f"Alokacja mapy {var_name} za pomocÄ… make, o kluczach {polish_type(k)} i wartoĹ›ciach {polish_type(v)}."

    # append
    m = re.match(r"^(\w+)\s*=\s*append\(\1,\s*(.+)\)$", stmt)
    if m:
        s_name, elem = m.group(1), m.group(2)
        return f"DoĹ‚Ä…czenie elementu {elem} na koniec wycinka {s_name} za pomocÄ… funkcji append."

    # new
    m = re.match(r"^(?:var\s+)?(\w+)\s*(?::=|=)\s*new\(([a-zA-Z0-9_.*]+)\)$", stmt)
    if m:
        var_name, t = m.group(1), m.group(2)
        return f"Alokacja zerowej wartoĹ›ci typu {polish_type_base(t)} za pomocÄ… new i przypisanie wskaĹşnika do zmiennej {var_name}."

    return None


def explain_functions_and_methods(stmt: str) -> Optional[str]:
    """Translates function and method definitions with receivers, parameters, and return types."""
    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(
        r"^func\s*\(\s*(\w+)\s+(\*?[a-zA-Z0-9_.]+)\s*\)\s*([a-zA-Z0-9_]+)(?:\[.*?\])?\s*\((.*?)\)\s*(.*?)\s*\{?$",
        stmt,
    )
    if m:
        rec_var, rec_type, m_name, args, ret = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        if rec_type.startswith("*"):
            rec_desc = f"wskaĹşnikowym odbiorcÄ… {rec_var} typu {rec_type[1:]}"
        else:
            rec_desc = f"wartoĹ›ciowym odbiorcÄ… {rec_var} typu {rec_type}"

        args_desc = polish_args(args)
        ret_desc = polish_return_types(ret)
        return f"Definicja metody {m_name} ze {rec_desc}, {args_desc}{ret_desc}."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^func\s+([a-zA-Z0-9_]+)(?:\[(.*?)\])?\s*\((.*?)\)\s*(.*?)\s*\{?$", stmt)
    if m:
        fn_name, type_params, args, ret = m.group(1), m.group(2), m.group(3), m.group(4)
        gen_desc = f" generyczna z parametrami typu {type_params}," if type_params else ""
        args_desc = polish_args(args)
        ret_desc = polish_return_types(ret)
        return f"Definicja funkcji {fn_name}{gen_desc} {args_desc}{ret_desc}."

    return None


def explain_variables_and_constants(stmt: str) -> Optional[str]:
    """Translates variable declarations, constants, and literal initializations."""
    # Rune
    m = re.match(r"^(?:var\s+)?(\w+)(?:\s+rune)?\s*(?::=|=)\s*'([^']+)'$", stmt)
    if m:
        return f"Zmienna {m.group(1)} typu rune, reprezentujÄ…ca znak Unicode o wartoĹ›ci {m.group(2)}."

    # String
    m = re.match(r'^(?:var\s+)?(\w+)(?:\s+string)?\s*(?::=|=)\s*"([^"]*)"$', stmt)
    if m:
        return f'Zmienna {m.group(1)} typu string o wartoĹ›ci tekstowej: "{m.group(2)}".'

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^(\w+)\s*,\s*(err|error)\s*:=\s*(.+)$", stmt)
    if m:
        res_var, err_var, expr = m.group(1), m.group(2), m.group(3)
        return f"ZwiÄ™zĹ‚a deklaracja zmiennej wynikowej {res_var} oraz zmiennej bĹ‚Ä™du {err_var} z wywoĹ‚ania: {expr}."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^(\w+)\s*:=\s*\[\]([a-zA-Z0-9_.*]+)\s*\{([^}]*)\}$", stmt)
    if m:
        items = m.group(3).strip() or "pusty"
        return f"Zmienna {m.group(1)} zainicjalizowana wycinkiem {polish_type_base(m.group(2))} z elementami: {items}."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^(\w+)\s*:=\s*(-?\d+(?:\.\d+)?)$", stmt)
    if m:
        return f"KrĂłtka deklaracja zmiennej {m.group(1)} z przypisaniem wartoĹ›ci liczbowej {polish_number(m.group(2))}."

    # var with zero type: var x int
    m = re.match(r"^var\s+(\w+)\s+([a-zA-Z0-9_.*\[\]]+)$", stmt)
    if m:
        return f"Deklaracja zmiennej {m.group(1)} {polish_type(m.group(2))}, zainicjalizowanej wartoĹ›ciÄ… zerowÄ…."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^const\s+(\w+)(?:\s+[a-zA-Z0-9_.*]+)?\s*=\s*(.+)$", stmt)
    if m:
        return f"Definicja staĹ‚ej {m.group(1)} rĂłwnej {m.group(2)}."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^(?:var\s+)?(\w+)\s*(?::=|=)\s*(&?[A-Z]\w*)\s*\{([^}]*)\}$", stmt)
    if m:
        v_name, s_name, fields = m.group(1), m.group(2), m.group(3).strip()
        prefix = "wskaĹşnika do nowej instancji struktury" if s_name.startswith("&") else "instancji struktury"
        clean_s_name = s_name.lstrip("&")
        if not fields:
            return f"Zainicjalizowanie pustego {prefix} {clean_s_name} z przypisaniem do zmiennej {v_name}."
        return f"Utworzenie {prefix} {clean_s_name} dla zmiennej {v_name} z polami: {fields}."

    return None


def explain_control_flow(stmt: str) -> Optional[str]:
    """Translates control flow statements: if, for loops, defer, and return."""
    # Implementation note: see the surrounding code for the behavior described here.
    if stmt.startswith("defer "):
        call = stmt[6:].strip()
        return f"Odroczona instrukcja defer wywoĹ‚ujÄ…ca {call}, wykonywana przy wyjĹ›ciu z ramki stosu funkcji."

    # Implementation note: see the surrounding code for the behavior described here.
    if re.search(r"if\s+err\s*!=\s*nil", stmt):
        return "Sprawdzenie bĹ‚Ä™du: jeĹ›li zmienna err nie jest rĂłwna nil, nastÄ™puje obsĹ‚uga sytuacji wyjÄ…tkowej."

    # Conditional if with assignment: if err := fn(); err != nil
    m_if_assign = re.match(r"^if\s+(.*?);\s*(.*?)\s*\{?$", stmt)
    if m_if_assign:
        init_part, cond_part = m_if_assign.group(1), m_if_assign.group(2)
        return f"Instrukcja warunkowa if z inicjalizacjÄ… lokalnÄ… {init_part} i sprawdzeniem warunku: {cond_part}."

    # Simple if condition
    m_if = re.match(r"^if\s+(.*?)\s*\{?$", stmt)
    if m_if:
        return f"Instrukcja warunkowa if: jeĹ›li {m_if.group(1)}:"

    if stmt in ("else {", "else"):
        return "W przeciwnym wypadku else:"

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^for\s+(\w+)\s*:=\s*range\s+(\w+)\s*\{?$", stmt)
    if m:
        return f"PÄ™tla for range odbierajÄ…ca kolejne wartoĹ›ci z kanaĹ‚u lub kolekcji {m.group(2)} do zmiennej {m.group(1)}."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^for\s+(\w+)\s*,\s*(\w+)\s*:=\s*range\s+(\w+)\s*\{?$", stmt)
    if m:
        return f"PÄ™tla for range iterujÄ…ca po {m.group(3)} z indeksem lub kluczem {m.group(1)} oraz wartoĹ›ciÄ… {m.group(2)}."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^for\s+_\s*,\s*(\w+)\s*:=\s*range\s+(\w+)\s*\{?$", stmt)
    if m:
        return f"PÄ™tla for range iterujÄ…ca po kolekcji {m.group(2)} z pobraniem samych elementĂłw do zmiennej {m.group(1)}."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^for\s+(\w+)\s*:=\s*(\d+);\s*\1\s*<\s*([^;]+);\s*\1\+\+\s*\{?$", stmt)
    if m:
        var_name, start, end = m.group(1), polish_number(m.group(2)), m.group(3)
        return f"Klasyczna pÄ™tla for ze zmiennÄ… {var_name} rosnÄ…cÄ… od {start} dopĂłki jest mniejsza od {end}."

    # Implementation note: see the surrounding code for the behavior described here.
    if stmt in ("for {", "for"):
        return "NieskoĹ„czona pÄ™tla for:"

    # Type switch
    m_tswitch = re.match(r"^switch\s+(?:(\w+)\s*:=\s*)?(\w+)\.\(type\)\s*\{?$", stmt)
    if m_tswitch:
        v_var = m_tswitch.group(1) or m_tswitch.group(2)
        return f"Instrukcja switch badajÄ…ca konkretny dynamiczny typ zmiennej interfejsowej {v_var}."

    # Return nil
    if stmt == "return nil":
        return "ZwrĂłcenie wartoĹ›ci nil oznaczajÄ…ce pomyĹ›lny brak bĹ‚Ä™du."

    # Implementation note: see the surrounding code for the behavior described here.
    if stmt.startswith("return "):
        val = stmt[7:].strip()
        return f"ZwrĂłcenie z funkcji wartoĹ›ci: {val}."

    return None


def explain_idiomatic_patterns(stmt: str) -> Optional[str]:
    """Translates common Go standard library idioms (fmt, time)."""
    # fmt.Print / fmt.Println / fmt.Printf
    m_print = re.match(r"^fmt\.Print(ln|f)?\((.*?)\)$", stmt)
    if m_print:
        args = m_print.group(2).strip()
        return f"Wypisanie do standardowego wyjĹ›cia za pomocÄ… fmt: {args}."

    # time.Sleep
    m_sleep = re.match(r"^time\.Sleep\((.*?)\)$", stmt)
    if m_sleep:
        return f"Wstrzymanie bieĹĽÄ…cej gorutyny za pomocÄ… time.Sleep na czas {m_sleep.group(1)}."

    return None
