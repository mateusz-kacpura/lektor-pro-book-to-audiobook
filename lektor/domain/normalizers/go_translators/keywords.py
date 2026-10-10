"""
lektor.domain.normalizers.go_translators.keywords
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Single Source of Truth (SSOT) dictionaries for Go operators, keywords, primitive types, and idioms.
Strict typing without Any (Python 3.14+).
"""

from typing import Mapping

# Implementation note: see the surrounding code for the behavior described here.
GO_OPERATORS_MAP: Mapping[str, str] = {
    ":=": "deklaracja i przypisanie",
    "!=": "rĂłĹĽne od",
    "==": "rĂłwne",
    "<=": "mniejsze lub rĂłwne",
    ">=": "wiÄ™ksze lub rĂłwne",
    "<-": "odbiĂłr lub wysĹ‚anie do kanaĹ‚u",
    "&&": "oraz",
    "||": "lub",
    "++": "inkrementacja",
    "--": "dekrementacja",
    "+=": "zwiÄ™ksz o",
    "-=": "zmniejsz o",
    "*=": "pomnĂłĹĽ przez",
    "/=": "podziel przez",
    "->": "strzaĹ‚ka w prawo",
    "=>": "strzaĹ‚ka gruba",
    "...": "wielokropek",
    "//": "komentarz:",
    "/*": "poczÄ…tek komentarza",
    "*/": "koniec komentarza",
}

# Implementation note: see the surrounding code for the behavior described here.
GO_INLINE_KEYWORDS: Mapping[str, str] = {
    "struct": "struktura struct",
    "interface": "interfejs interface",
    "goroutine": "wspĂłĹ‚bieĹĽna gorutyna",
    "chan": "kanaĹ‚ komunikacyjny chan",
    "select": "instrukcja wyboru select",
    "defer": "odroczone wykonanie defer",
    "go": "sĹ‚owo kluczowe go do tworzenia gorutyn",
    "nil": "wartoĹ›Ä‡ zerowa nil",
    "make": "funkcja alokujÄ…ca make",
    "new": "funkcja alokujÄ…ca pamiÄ™Ä‡ new",
    "append": "funkcja append",
    "range": "klauzula iteracji range",
    "rune": "typ rune reprezentujÄ…cy punkt kodowy Unicode",
    "byte": "typ bajtowy byte",
    "iota": "generator staĹ‚ych iota",
    "context.Context": "kontekst operacji Context",
    "sync.Mutex": "muteks wzajemnego wykluczania",
    "sync.RWMutex": "muteks czytelnikĂłw i pisarzy RWMutex",
    "sync.WaitGroup": "licznik synchronizacji zadaĹ„ WaitGroup",
}

# Implementation note: see the surrounding code for the behavior described here.
GO_KEYWORDS_REGEX_PATTERNS: Mapping[str, str] = {
    r"\bfunc\b": "funkcja",
    r"\btype\b": "typ",
    r"\bstruct\b": "struktura",
    r"\binterface\b": "interfejs",
    r"\bpackage\b": "pakiet",
    r"\bimport\b": "import",
    r"\breturn\b": "zwrĂłÄ‡",
    r"\bdefer\b": "odroczone wywoĹ‚anie defer",
    r"\bgo\s+func\b": "uruchomienie gorutyny",
    r"\bselect\b": "instrukcja wyboru select",
    r"\bchan\b": "kanaĹ‚",
    r"\bmake\(chan\b": "utwĂłrz kanaĹ‚",
    r"\bmake\(\[\]\b": "utwĂłrz wycinek",
    r"\bmake\(map\b": "utwĂłrz mapÄ™",
    r"\bmap\[": "mapa z kluczem ",
    r"\b\[\]byte\b": "wycinek bajtĂłw",
    r"\b\[\]string\b": "wycinek Ĺ‚aĹ„cuchĂłw znakĂłw",
    r"\b\[\]int\b": "wycinek liczb caĹ‚kowitych",
    r"\berr\s*!=\s*nil\b": "bĹ‚Ä…d jest rĂłĹĽny od nil",
    r"\berr\s*==\s*nil\b": "brak bĹ‚Ä™du, err rĂłwne nil",
    r"\bnil\b": "nil",
    r"\bint64\b": "int szeĹ›Ä‡dziesiÄ…t cztery",
    r"\bint32\b": "int trzydzieĹ›ci dwa",
    r"\bfloat64\b": "float szeĹ›Ä‡dziesiÄ…t cztery",
    r"\bfloat32\b": "float trzydzieĹ›ci dwa",
    r"\bbool\b": "typ logiczny bool",
    r"\bstring\b": "napis string",
    r"\bcontext\.Context\b": "kontekst operacji Context",
    r"\bctx\b": "kontekst",
    r"\bsync\.Mutex\b": "muteks wzajemnego wykluczania",
    r"\bsync\.WaitGroup\b": "licznik synchronizacji zadaĹ„ WaitGroup",
    r"\bhttp\.Handler\b": "handler ha te te pe",
    r"\bhttp\.ResponseWriter\b": "obiekt odpowiedzi ha te te pe",
    r"\b\*http\.Request\b": "wskaĹşnik na ĹĽÄ…danie ha te te pe",
}

# Implementation note: see the surrounding code for the behavior described here.
GO_PRIMITIVE_TYPES: Mapping[str, str] = {
    "string": "string, Ĺ‚aĹ„cuch znakĂłw",
    "int": "int, liczba caĹ‚kowita",
    "int8": "int osiem",
    "int16": "int szesnaĹ›cie",
    "int32": "int trzydzieĹ›ci dwa",
    "int64": "int szeĹ›Ä‡dziesiÄ…t cztery",
    "uint": "bezznakowy int",
    "uint8": "bezznakowy int osiem",
    "uint16": "bezznakowy int szesnaĹ›cie",
    "uint32": "bezznakowy int trzydzieĹ›ci dwa",
    "uint64": "bezznakowy int szeĹ›Ä‡dziesiÄ…t cztery",
    "uintptr": "uintptr, wskaĹşnik liczb caĹ‚kowitych",
    "float32": "float trzydzieĹ›ci dwa",
    "float64": "float szeĹ›Ä‡dziesiÄ…t cztery",
    "complex64": "liczba zespolona complex szeĹ›Ä‡dziesiÄ…t cztery",
    "complex128": "liczba zespolona complex sto dwadzieĹ›cia osiem",
    "bool": "bool, wartoĹ›Ä‡ logiczna",
    "byte": "bajt byte",
    "rune": "runa rune, punkt kodowy Unicode",
    "error": "interfejs bĹ‚Ä™du error",
    "any": "dowolny typ any",
    "interface{}": "pusty interfejs interface{}",
    "context.Context": "kontekst operacji Context",
    "time.Duration": "czas trwania time.Duration",
    "time.Time": "znacznik czasu time.Time",
}
