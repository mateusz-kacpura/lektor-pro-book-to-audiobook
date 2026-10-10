"""
lektor.domain.normalizers.go_translators.concurrency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Translator for Go concurrency mechanisms (channels, goroutines, select) and sync primitives.
Strict typing without Any.
"""

from __future__ import annotations

import re
from typing import Optional

from .types import polish_number


def explain_concurrency(stmt: str) -> Optional[str]:
    """Translates channel operations, select blocks, and goroutines."""
    # Timeout case with time.After
    m = re.match(r"^case\s*<-\s*time\.After\((.*?)\)\s*:$", stmt)
    if m:
        dur = m.group(1).replace("*", " pomnoĹĽone przez ").strip()
        return f"Przypadek case: przekroczenie limitu czasu timeout po upĹ‚ywie {dur} za pomocÄ… time.After."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^case\s+(\w+)\s*(?::=|=)\s*<-\s*(\w+)\s*:$", stmt)
    if m:
        val, ch = m.group(1), m.group(2)
        return f"Przypadek case: asynchroniczny odbiĂłr danych z kanaĹ‚u {ch} do zmiennej {val}."

    # Empty receive case
    m = re.match(r"^case\s*<-\s*(\w+)\s*:$", stmt)
    if m:
        return f"Przypadek case: synchronizacja przez odebranie sygnaĹ‚u z kanaĹ‚u {m.group(1)}."

    # Default in select
    if stmt.startswith("default:"):
        return "Przypadek domyĹ›lny default: wykonanie nieblokujÄ…ce, gdy ĹĽaden kanaĹ‚ nie jest gotowy."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^(\w+)\s*<-\s*(.+)$", stmt)
    if m:
        ch, val = m.group(1), m.group(2).strip()
        return f"WysĹ‚anie wartoĹ›ci {val} do kanaĹ‚u {ch}. JeĹ›li kanaĹ‚ jest niebuforowany, operacja blokuje gorutynÄ™ do czasu odebrania."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^(\w+)\s*,\s*(\w+)\s*(?::=|=)\s*<-\s*(\w+)$", stmt)
    if m:
        val, ok, ch = m.group(1), m.group(2), m.group(3)
        return f"Odebranie z kanaĹ‚u {ch} do zmiennej {val} wraz ze sprawdzeniem otwarcia kanaĹ‚u we fladze logicznej {ok}."

    # Receive into variable
    m = re.match(r"^(\w+)\s*(?::=|=)\s*<-\s*(\w+)$", stmt)
    if m:
        val, ch = m.group(1), m.group(2)
        return f"Odebranie wartoĹ›ci z kanaĹ‚u {ch} i przypisanie jej do zmiennej {val}."

    # Receive with discard
    m = re.match(r"^<-\s*(\w+)$", stmt)
    if m:
        return f"Pobranie i odrzucenie wartoĹ›ci z kanaĹ‚u {m.group(1)} w celu synchronizacji."

    # Implementation note: see the surrounding code for the behavior described here.
    m = re.match(r"^close\((\w+)\)$", stmt)
    if m:
        return f"ZamkniÄ™cie kanaĹ‚u {m.group(1)} wywoĹ‚aniem funkcji close, sygnalizujÄ…ce brak dalszych transmisji."

    # Anonymous goroutine
    if stmt.startswith("go func"):
        return "Uruchomienie nowej wspĂłĹ‚bieĹĽnej gorutyny realizujÄ…cej anonimowy literaĹ‚ funkcyjny."

    # Named goroutine
    m = re.match(r"^go\s+([a-zA-Z0-9_.]+)\((.*)\)$", stmt)
    if m:
        fn, args = m.group(1), m.group(2)
        arg_desc = f" z argumentami {args}" if args else " bez argumentĂłw"
        return f"Uruchomienie wspĂłĹ‚bieĹĽnej gorutyny wykonujÄ…cej funkcjÄ™ {fn}{arg_desc}."

    return None


def explain_sync_primitives(stmt: str) -> Optional[str]:
    """Translates synchronization primitives: Mutex, WaitGroup, etc."""
    # Mutex Lock / Unlock
    if stmt.endswith(".Lock()"):
        mu = stmt[:-7].strip()
        return f"Zablokowanie muteksa {mu} metodÄ… Lock w celu zabezpieczenia sekcji krytycznej."

    if stmt.startswith("defer ") and stmt.endswith(".Unlock()"):
        mu = stmt[6:-9].strip()
        return f"Odroczone wywoĹ‚anie defer odblokowania muteksa {mu} Unlock przy wyjĹ›ciu z bieĹĽÄ…cej funkcji."

    if stmt.endswith(".Unlock()"):
        mu = stmt[:-9].strip()
        return f"Zwolnienie blokady muteksa {mu} metodÄ… Unlock."

    if stmt.endswith(".RLock()"):
        mu = stmt[:-8].strip()
        return f"ZaĹ‚oĹĽenie blokady odczytu RLock na muteksie {mu}."

    if stmt.endswith(".RUnlock()"):
        mu = stmt[:-10].strip()
        return f"Zwolnienie blokady odczytu RUnlock na muteksie {mu}."

    # WaitGroup
    m_wg_add = re.match(r"^(\w+)\.Add\((.*?)\)$", stmt)
    if m_wg_add:
        wg, delta = m_wg_add.group(1), polish_number(m_wg_add.group(2))
        return f"ZwiÄ™kszenie licznika grupy oczekiwania {wg} o {delta} za pomocÄ… metody Add."

    if stmt.endswith(".Done()"):
        wg = stmt[:-7].strip()
        return f"Zasygnalizowanie ukoĹ„czenia zadania w grupie oczekiwania {wg} za pomocÄ… metody Done."

    if stmt.endswith(".Wait()"):
        wg = stmt[:-7].strip()
        return f"Zablokowanie wykonywania metodÄ… Wait do czasu ukoĹ„czenia wszystkich zadaĹ„ w grupie {wg}."

    return None
