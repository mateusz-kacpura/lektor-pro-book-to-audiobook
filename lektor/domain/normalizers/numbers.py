"""
Comprehensive normalizer for numbers, dates, chapters, versions, and technical notation.
Converts numeric digits into natural, grammatically correct spoken words.
"""
import re

from .spelling import NumberSpellingProtocol

# Implementation note: see the surrounding code for the behavior described here.

ROMAN_TO_INT = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20,
    "XXI": 21, "XXII": 22
}

ROMAN_CENTURY_LOCATIVE = {
    "I": "pierwszym", "II": "drugim", "III": "trzecim", "IV": "czwartym", "V": "piÄ…tym",
    "VI": "szĂłstym", "VII": "siĂłdmym", "VIII": "Ăłsmym", "IX": "dziewiÄ…tym", "X": "dziesiÄ…tym",
    "XI": "jedenastym", "XII": "dwunastym", "XIII": "trzynastym", "XIV": "czternastym", "XV": "piÄ™tnastym",
    "XVI": "szesnastym", "XVII": "siedemnastym", "XVIII": "osiemnastym", "XIX": "dziewiÄ™tnastym", "XX": "dwudziestym",
    "XXI": "dwudziestym pierwszym", "XXII": "dwudziestym drugim"
}

ROMAN_CENTURY_GENITIVE = {
    "I": "pierwszego", "II": "drugiego", "III": "trzeciego", "IV": "czwartego", "V": "piÄ…tego",
    "VI": "szĂłstego", "VII": "siĂłdmego", "VIII": "Ăłsmego", "IX": "dziewiÄ…tego", "X": "dziesiÄ…tego",
    "XI": "jedenastego", "XII": "dwunastego", "XIII": "trzynastego", "XIV": "czternastego", "XV": "piÄ™tnastego",
    "XVI": "szesnastego", "XVII": "siedemnastego", "XVIII": "osiemnastego", "XIX": "dziewiÄ™tnastego", "XX": "dwudziestego",
    "XXI": "dwudziestego pierwszego", "XXII": "dwudziestego drugiego"
}

ROMAN_CENTURY_NOMINATIVE = {
    "I": "pierwszy", "II": "drugi", "III": "trzeci", "IV": "czwarty", "V": "piÄ…ty",
    "VI": "szĂłsty", "VII": "siĂłdmy", "VIII": "Ăłsmy", "IX": "dziewiÄ…ty", "X": "dziesiÄ…ty",
    "XI": "jedenasty", "XII": "dwunasty", "XIII": "trzynasty", "XIV": "czternasty", "XV": "piÄ™tnasty",
    "XVI": "szesnasty", "XVII": "siedemnasty", "XVIII": "osiemnasty", "XIX": "dziewiÄ™tnasty", "XX": "dwudziesty",
    "XXI": "dwudziesty pierwszy", "XXII": "dwudziesty drugi"
}

ROMAN_PART_FEM_NOMINATIVE = {
    "I": "pierwsza", "II": "druga", "III": "trzecia", "IV": "czwarta", "V": "piÄ…ta",
    "VI": "szĂłsta", "VII": "siĂłdma", "VIII": "Ăłsma", "IX": "dziewiÄ…ta", "X": "dziesiÄ…ta"
}

ROMAN_PART_FEM_GEN_LOC = {
    "I": "pierwszej", "II": "drugiej", "III": "trzeciej", "IV": "czwartej", "V": "piÄ…tej",
    "VI": "szĂłstej", "VII": "siĂłdmej", "VIII": "Ăłsmej", "IX": "dziewiÄ…tej", "X": "dziesiÄ…tej"
}

DECADES_LOCATIVE = {
    10: "dziesiÄ…tych", 20: "dwudziestych", 30: "trzydziestych", 40: "czterdziestych",
    50: "piÄ™Ä‡dziesiÄ…tych", 60: "szeĹ›Ä‡dziesiÄ…tych", 70: "siedemdziesiÄ…tych",
    80: "osiemdziesiÄ…tych", 90: "dziewiÄ™Ä‡dziesiÄ…tych",
    2000: "dwutysiÄ™cznych", 2010: "dwa tysiÄ…ce dziesiÄ…tych"
}

DECADES_NOMINATIVE = {
    10: "dziesiÄ…te", 20: "dwudzieste", 30: "trzydzieste", 40: "czterdzieste",
    50: "piÄ™Ä‡dziesiÄ…te", 60: "szeĹ›Ä‡dziesiÄ…te", 70: "siedemdziesiÄ…te",
    80: "osiemdziesiÄ…te", 90: "dziewiÄ™Ä‡dziesiÄ…te",
    2000: "dwutysiÄ™czne", 2010: "dwa tysiÄ…ce dziesiÄ…te"
}


# Implementation note: see the surrounding code for the behavior described here.

class _PureDomainNumberSpeller(NumberSpellingProtocol):
    """Pure domain Python implementation for verbalizing numbers."""

    _UNITS = ("zero", "jeden", "dwa", "trzy", "cztery", "piÄ™Ä‡", "szeĹ›Ä‡", "siedem", "osiem", "dziewiÄ™Ä‡")
    _TEENS = (
        "dziesiÄ™Ä‡", "jedenaĹ›cie", "dwanaĹ›cie", "trzynaĹ›cie", "czternaĹ›cie",
        "piÄ™tnaĹ›cie", "szesnaĹ›cie", "siedemnaĹ›cie", "osiemnaĹ›cie", "dziewiÄ™tnaĹ›cie"
    )
    _TENS = (
        "", "", "dwadzieĹ›cia", "trzydzieĹ›ci", "czterdzieĹ›ci",
        "piÄ™Ä‡dziesiÄ…t", "szeĹ›Ä‡dziesiÄ…t", "siedemdziesiÄ…t", "osiemdziesiÄ…t", "dziewiÄ™Ä‡dziesiÄ…t"
    )
    _HUNDREDS = (
        "", "sto", "dwieĹ›cie", "trzysta", "czterysta",
        "piÄ™Ä‡set", "szeĹ›Ä‡set", "siedemset", "osiemset", "dziewiÄ™Ä‡set"
    )

    def int_to_polish_words(self, num: int) -> str:
        if num == 0:
            return "zero"
        if num < 0:
            return f"minus {self.int_to_polish_words(abs(num))}"
        if num >= 1000000:
            return str(num)
        
        parts: list[str] = []
        thousands = num // 1000
        remainder = num % 1000

        if thousands > 0:
            if thousands == 1:
                parts.append("tysiÄ…c")
            elif 2 <= (thousands % 10) <= 4 and (thousands % 100 < 10 or thousands % 100 >= 20):
                parts.append(f"{self._spell_under_thousand(thousands)} tysiÄ…ce")
            else:
                parts.append(f"{self._spell_under_thousand(thousands)} tysiÄ™cy")

        if remainder > 0 or not parts:
            spelled_rem = self._spell_under_thousand(remainder)
            if spelled_rem:
                parts.append(spelled_rem)

        return " ".join(parts).strip()

    def _spell_under_thousand(self, num: int) -> str:
        if num == 0:
            return ""
        parts: list[str] = []
        h = num // 100
        rem = num % 100
        if h > 0:
            parts.append(self._HUNDREDS[h])
        if 10 <= rem < 20:
            parts.append(self._TEENS[rem - 10])
        else:
            t = rem // 10
            u = rem % 10
            if t > 0:
                parts.append(self._TENS[t])
            if u > 0:
                parts.append(self._UNITS[u])
        return " ".join(parts).strip()

    def int_to_ordinal_masc_nom(self, num: int) -> str:
        ordinals_units = (
            "zerowy", "pierwszy", "drugi", "trzeci", "czwarty",
            "piÄ…ty", "szĂłsty", "siĂłdmy", "Ăłsmy", "dziewiÄ…ty"
        )
        if 0 <= num < 10:
            return ordinals_units[num]
        return f"{self.int_to_polish_words(num)}"

    def int_to_ordinal_masc_loc(self, num: int) -> str:
        card = self.int_to_ordinal_masc_nom(num)
        words = card.split()
        if not words:
            return str(num)
        last = words[-1]
        if last.endswith("y"):
            words[-1] = last[:-1] + "ym"
        elif last.endswith("i"):
            words[-1] = last[:-1] + "im"
        return " ".join(words)

    def int_to_ordinal_masc_gen(self, num: int) -> str:
        card = self.int_to_ordinal_masc_nom(num)
        words = card.split()
        if not words:
            return str(num)
        last = words[-1]
        if last.endswith("y") or last.endswith("i"):
            words[-1] = last[:-1] + "ego"
        return " ".join(words)

    def int_to_ordinal_fem_nom(self, num: int) -> str:
        card = self.int_to_ordinal_masc_nom(num)
        words = card.split()
        if not words:
            return str(num)
        last = words[-1]
        if last.endswith("y"):
            words[-1] = last[:-1] + "a"
        elif last.endswith("i"):
            words[-1] = last[:-1] + "a"
        return " ".join(words)

    def int_to_ordinal_fem_loc(self, num: int) -> str:
        card = self.int_to_ordinal_masc_nom(num)
        words = card.split()
        if not words:
            return str(num)
        last = words[-1]
        if last.endswith("y") or last.endswith("i"):
            words[-1] = last[:-1] + "ej"
        return " ".join(words)


_DEFAULT_SPELLER: NumberSpellingProtocol = _PureDomainNumberSpeller()


def get_default_speller() -> NumberSpellingProtocol:
    """Returns active number spelling strategy."""
    return _DEFAULT_SPELLER


def set_default_speller(speller: NumberSpellingProtocol) -> None:
    """Sets global number spelling strategy (Dependency Injection)."""
    global _DEFAULT_SPELLER
    _DEFAULT_SPELLER = speller


# Implementation note: see the surrounding code for the behavior described here.

def int_to_polish_words(num: int) -> str:
    """Returns cardinal number in masculine nominative (e.g. 15 -> 'piętnaście')."""
    return _DEFAULT_SPELLER.int_to_polish_words(num)


def int_to_ordinal_masc_nom(num: int) -> str:
    """Returns ordinal number in masculine nominative (e.g. 1 -> 'pierwszy')."""
    return _DEFAULT_SPELLER.int_to_ordinal_masc_nom(num)


def int_to_ordinal_masc_loc(num: int) -> str:
    """Returns ordinal number in masculine locative (e.g. 1976 -> 'tysiąc dziewięćset siedemdziesiątym szóstym')."""
    return _DEFAULT_SPELLER.int_to_ordinal_masc_loc(num)


def int_to_ordinal_masc_gen(num: int) -> str:
    """Returns ordinal number in masculine genitive (e.g. 2024 -> 'dwa tysiące dwudziestego czwartego')."""
    return _DEFAULT_SPELLER.int_to_ordinal_masc_gen(num)


def int_to_ordinal_fem_nom(num: int) -> str:
    """Returns ordinal number in feminine nominative (e.g. 20 -> 'dwudziesta')."""
    return _DEFAULT_SPELLER.int_to_ordinal_fem_nom(num)


def int_to_ordinal_fem_loc(num: int) -> str:
    """Returns ordinal number in feminine locative (e.g. 9 -> 'dziewiątej')."""
    return _DEFAULT_SPELLER.int_to_ordinal_fem_loc(num)


# Implementation note: see the surrounding code for the behavior described here.

def _normalize_big_o_and_multipliers(text: str) -> str:
    """1. Big-O computational complexity and multipliers."""
    text = re.sub(r"\bO\(\s*1\s*\)", "zĹ‚oĹĽonoĹ›Ä‡ rzÄ™du jeden", text)
    text = re.sub(r"\bO\(\s*n\s*\)", "zĹ‚oĹĽonoĹ›Ä‡ rzÄ™du en", text)
    text = re.sub(r"\bO\(\s*log\s*n\s*\)", "zĹ‚oĹĽonoĹ›Ä‡ rzÄ™du logarytm en", text, flags=re.IGNORECASE)
    text = re.sub(r"\bO\(\s*n\s*log\s*n\s*\)", "zĹ‚oĹĽonoĹ›Ä‡ rzÄ™du en logarytm en", text, flags=re.IGNORECASE)
    text = re.sub(r"\bO\(\s*n\^2\s*\)", "zĹ‚oĹĽonoĹ›Ä‡ rzÄ™du en do kwadratu", text)

    text = re.sub(r"\b10-krotne(go|mu|m)?\b", r"dziesiÄ™ciokrotne\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b100-krotne(go|mu|m)?\b", r"stukrotne\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b1000-krotne(go|mu|m)?\b", r"tysiÄ…ckrotne\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b10x\b", "dziesiÄ™ciokrotnie", text, flags=re.IGNORECASE)
    text = re.sub(r"\b100x\b", "stukrotnie", text, flags=re.IGNORECASE)
    return text


def _normalize_footnotes(text: str) -> str:
    """2. Markdown footnotes and bibliographic references."""
    text = re.sub(r"^\s*\[\^\d+\]:?.*$", "", text, flags=re.MULTILINE)
    return re.sub(r"\[\^\d+\]", "", text)


def _normalize_decades_and_centuries(text: str) -> str:
    """3-5. Centuries, decades, and book sections in Roman numerals."""
    def replace_decade_century(m: re.Match[str]) -> str:
        prefix = m.group(1)
        decade_num = int(m.group(2))
        roman = m.group(3).upper()
        decade_word = DECADES_LOCATIVE.get(decade_num, int_to_polish_words(decade_num))
        century_word = ROMAN_CENTURY_GENITIVE.get(roman, f"{roman} wieku")
        return f"{prefix} {decade_word} {century_word} wieku"

    text = re.sub(
        r"\b(w\s+latach|latach|pod\s+koniec\s+lat|lat)\s+(\d+)(?:\.|\-tych)?\s+([IVXLCDM]+)\s+wieku\b",
        replace_decade_century,
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bw\s+([IVXLCDM]+)\s+(?:wieku|w\.)\b",
        lambda m: f"w {ROMAN_CENTURY_LOCATIVE.get(m.group(1).upper(), m.group(1))} wieku",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b([IVXLCDM]+)\s+(?:wieku|w\.)\b",
        lambda m: f"{ROMAN_CENTURY_GENITIVE.get(m.group(1).upper(), m.group(1))} wieku",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b([IVXLCDM]+)\s+wiek\b",
        lambda m: f"{ROMAN_CENTURY_NOMINATIVE.get(m.group(1).upper(), m.group(1))} wiek",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bCzÄ™Ĺ›Ä‡\s+([IVXLCDM]+)\b",
        lambda m: f"CzÄ™Ĺ›Ä‡ {ROMAN_PART_FEM_NOMINATIVE.get(m.group(1).upper(), m.group(1))}",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\bCzÄ™Ĺ›ci\s+([IVXLCDM]+)\b",
        lambda m: f"CzÄ™Ĺ›ci {ROMAN_PART_FEM_GEN_LOC.get(m.group(1).upper(), m.group(1))}",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\b(w\s+latach|latach)\s+(\d+)(?:\.|\-tych)?(?=\s|[,\.\?!]|$|\))",
        lambda m: f"{m.group(1)} {DECADES_LOCATIVE.get(int(m.group(2)), int_to_polish_words(int(m.group(2))))}",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b(pod\s+koniec\s+lat|lat)\s+(\d+)(?:\.|\-tych)?(?=\s|[,\.\?!]|$|\))",
        lambda m: f"{m.group(1)} {DECADES_LOCATIVE.get(int(m.group(2)), int_to_polish_words(int(m.group(2))))}",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\blata\s+(\d+)(?:\.|\-tych)?(?=\s|[,\.\?!]|$|\))",
        lambda m: f"lata {DECADES_NOMINATIVE.get(int(m.group(1)), int_to_polish_words(int(m.group(1))))}",
        text,
        flags=re.IGNORECASE
    )
    return text


def _normalize_dates_and_years(text: str) -> str:
    """6. Years and calendar dates."""
    text = re.sub(
        r"\b(w)\s+(\d{4})\s*(?:roku|r\.)\b",
        lambda m: f"{m.group(1)} {int_to_ordinal_masc_loc(int(m.group(2)))} roku",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b(od|do|z|od\s+roku|do\s+roku)\s+(\d{4})\s*(?:roku|r\.)\b",
        lambda m: f"{m.group(1)} {int_to_ordinal_masc_gen(int(m.group(2)))} roku",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\broku\s+(\d{4})\b",
        lambda m: f"roku {int_to_ordinal_masc_gen(int(m.group(1)))}",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\brok\s+(\d{4})\b",
        lambda m: f"rok {int_to_polish_words(int(m.group(1)))}",
        text,
        flags=re.IGNORECASE
    )
    months_pat = r"\b(styczeĹ„|luty|marzec|kwiecieĹ„|maj|czerwiec|lipiec|sierpieĹ„|wrzesieĹ„|paĹşdziernik|listopad|grudzieĹ„|stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|wrzeĹ›nia|paĹşdziernika|listopada|grudnia)\s+(\d{4})\s*(?:roku|r\.)?"
    return re.sub(
        months_pat,
        lambda m: f"{m.group(1)} {int_to_ordinal_masc_gen(int(m.group(2)))} roku",
        text,
        flags=re.IGNORECASE
    )


def _normalize_figures_and_chapters(text: str) -> str:
    """7-8. Figures, tables, listings, chapters, and page numbers."""
    def replace_figure(m: re.Match[str]) -> str:
        prefix = m.group(1)
        if prefix.lower().startswith("fig"):
            prefix = "Rysunek"
        n1 = int_to_polish_words(int(m.group(2)))
        n2 = int_to_polish_words(int(m.group(3)))
        return f"{prefix} {n1} {n2}"

    text = re.sub(
        r"\b(Rysunek|Rysunku|Rysunkiem|Figure|figure)\s+(\d+)[-\.](\d+)\b",
        replace_figure,
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b(Tabela|Tabeli|Table|table)\s+(\d+)[-\.](\d+)\b",
        lambda m: f"Tabela {int_to_polish_words(int(m.group(2)))} {int_to_polish_words(int(m.group(3)))}",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b(Listing|Listingu)\s+(\d+)[-\.](\d+)\b",
        lambda m: f"{m.group(1)} {int_to_polish_words(int(m.group(2)))} {int_to_polish_words(int(m.group(3)))}",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b(Sekcja|Sekcji)\s+(\d+)[-\.](\d+)\b",
        lambda m: f"{m.group(1)} {int_to_polish_words(int(m.group(2)))} {int_to_polish_words(int(m.group(3)))}",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b(Krok|Punkt)\s+(\d+)\b",
        lambda m: f"{m.group(1)} {int_to_ordinal_masc_nom(int(m.group(2)))}",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\b(rozdziaĹ‚u|rozdziale)\s+(\d+)\b",
        lambda m: f"{m.group(1)} {int_to_ordinal_masc_loc(int(m.group(2)))}",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b(rozdziaĹ‚)\s+(\d+)\b",
        lambda m: f"{m.group(1)} {int_to_ordinal_masc_nom(int(m.group(2)))}",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b(Strona|strona)\s+0*(\d+)\b",
        lambda m: f"{m.group(1)} {int_to_ordinal_fem_nom(int(m.group(2)))}",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\b(na\s+stronie|stronie)\s+0*(\d+)\b",
        lambda m: f"{m.group(1)} {int_to_ordinal_fem_loc(int(m.group(2)))}",
        text,
        flags=re.IGNORECASE
    )
    return re.sub(
        r"\b(?:na\s+)?(?:s\.|str\.)\s*0*(\d+)\b",
        lambda m: f"na stronie {int_to_ordinal_fem_loc(int(m.group(1)))}",
        text,
        flags=re.IGNORECASE
    )


def _normalize_technical_versions(text: str) -> str:
    """9. Technical versioning (v1.2.0, Go 1.22, HTTP/2)."""
    def replace_version(m: re.Match[str]) -> str:
        ver_str = m.group(1)
        digits = ver_str.split(".")
        spoken_digits = [int_to_polish_words(int(d)) for d in digits if d.isdigit()]
        return f"wersja {' '.join(spoken_digits)}"

    text = re.sub(r"\bv(\d+\.\d+(?:\.\d+)?)\b", replace_version, text, flags=re.IGNORECASE)
    text = re.sub(
        r"\bGo\s+(\d+\.\d+)\b",
        lambda m: f"Go {' '.join(int_to_polish_words(int(d)) for d in m.group(1).split('.'))}",
        text,
        flags=re.IGNORECASE
    )
    return re.sub(
        r"\bHTTP/(\d+(?:\.\d+)?)\b",
        lambda m: f"ha te te pe {' '.join(int_to_polish_words(int(d)) for d in m.group(1).split('.'))}",
        text,
        flags=re.IGNORECASE
    )


def _normalize_percentages_and_fractions(text: str) -> str:
    """10-11. Percentages and decimal fractions."""
    text = re.sub(
        r"\b(\d+)[,\.](\d+)\s*%",
        lambda m: f"{int_to_polish_words(int(m.group(1)))} przecinek {int_to_polish_words(int(m.group(2)))} procent",
        text
    )
    text = re.sub(
        r"\b(\d+)\s*%",
        lambda m: f"{int_to_polish_words(int(m.group(1)))} procent",
        text
    )
    return re.sub(
        r"\b(\d+)[,\.](\d+)\b",
        lambda m: f"{int_to_polish_words(int(m.group(1)))} przecinek {int_to_polish_words(int(m.group(2)))}",
        text
    )


def _normalize_units_and_standalone(text: str) -> str:
    """12-14. Time units, network ports, and integers."""
    text = re.sub(r"\b(\d+)\s+lat\b", lambda m: f"{int_to_polish_words(int(m.group(1)))} lat", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(\d+)\s+lata\b", lambda m: f"{int_to_polish_words(int(m.group(1)))} lata", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(\d+)\s+rok\b", lambda m: f"{int_to_polish_words(int(m.group(1)))} rok", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(\d+)\s*ms\b", lambda m: f"{int_to_polish_words(int(m.group(1)))} milisekund", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(\d+)\s*s\b", lambda m: f"{int_to_polish_words(int(m.group(1)))} sekund", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(\d+)\s*min\b", lambda m: f"{int_to_polish_words(int(m.group(1)))} minut", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(\d+)\s+sekund(?:y)?\b", lambda m: f"{int_to_polish_words(int(m.group(1)))} sekund", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(\d+)\s+minut(?:y)?\b", lambda m: f"{int_to_polish_words(int(m.group(1)))} minut", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(\d+)\s+godzin(?:y)?\b", lambda m: f"{int_to_polish_words(int(m.group(1)))} godzin", text, flags=re.IGNORECASE)

    text = re.sub(
        r"\bport\s+(\d{2,5})\b",
        lambda m: f"port {int_to_polish_words(int(m.group(1)))}",
        text,
        flags=re.IGNORECASE
    )

    # Implementation note: see the surrounding code for the behavior described here.
    return re.sub(r"\b\d+\b", lambda m: int_to_polish_words(int(m.group(0))), text)


def normalize_numbers_and_symbols(text: str) -> str:
    """Normalizes all numbers, dates, centuries, figures, and fractions into spoken words."""
    if not text:
        return ""

    text = _normalize_big_o_and_multipliers(text)
    text = _normalize_footnotes(text)
    text = _normalize_decades_and_centuries(text)
    text = _normalize_dates_and_years(text)
    text = _normalize_figures_and_chapters(text)
    text = _normalize_technical_versions(text)
    text = _normalize_percentages_and_fractions(text)
    return _normalize_units_and_standalone(text)
