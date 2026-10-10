"""
Normalizer module for special characters, programming operators, technical units,
math symbols, URLs/emails, and technical notations for TTS synthesis.
Converts symbols into natural spoken forms.
"""
import re

# Implementation note: see the surrounding code for the behavior described here.
TECH_NAMES = [
    (r"\bC\+\+(?=[\s,;:\.!?\)]|$)", "C plus plus"),
    (r"\bC#(?=[\s,;:\.!?\)]|$)", "C sharp"),
    (r"\b\.NET\b", "dot net"),
    (r"\bASP\.NET\b", "ASP dot net"),
    (r"\bNode\.js\b", "Node dĹĽej es"),
    (r"\bVue\.js\b", "Vue dĹĽej es"),
    (r"\bReact\.js\b", "React dĹĽej es"),
    (r"\bNext\.js\b", "Next dĹĽej es"),
]

# 2. Legal, currency, and typographical symbols
LEGAL_AND_TYPO_SYMBOLS = [
    (r"Â©", " prawa autorskie "),
    (r"Â®", " zastrzeĹĽony znak towarowy "),
    (r"â„˘", " znak towarowy "),
    (r"Â§", " paragraf "),
    (r"Â°C\b", " stopni Celsjusza "),
    (r"(?<=\d)Â°(?!\w)", " stopni "),
    (r"â‚¬\s*(\d+)", r"\1 euro"),
    (r"ÂŁ\s*(\d+)", r"\1 funtĂłw"),
    (r"ÂĄ\s*(\d+)", r"\1 jenĂłw"),
]

# 3. Technical, time, and architectural units
def normalize_technical_units(text: str) -> str:
    """Normalizes bit, memory, frequency, and time units."""
    # Implementation note: see the surrounding code for the behavior described here.
    bit_map = {
        "1": "jednobitow",
        "8": "oĹ›miobitow",
        "16": "szesnastobitow",
        "32": "trzydziestodwubitow",
        "64": "szeĹ›Ä‡dziesiÄ™cioczterobitow",
        "128": "stodwudziestoosmiobitow"
    }
    for b_num, b_stem in bit_map.items():
        text = re.sub(rf"\b{b_num}-bitow([a-zÄ…Ä‡Ä™Ĺ‚Ĺ„ĂłĹ›ĹşĹĽ]*)\b", rf"{b_stem}\1", text, flags=re.IGNORECASE)
    
    # Time units (microseconds, nanoseconds)
    text = re.sub(r"(\d+)\s*(?:Âµs|ÎĽs|us)\b", r"\1 mikrosekund", text)
    text = re.sub(r"(\d+)\s*ns\b", r"\1 nanosekund", text)
    
    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"(\d+)\s*(?:kB|KB|kb)\b", r"\1 kilobajtĂłw", text)
    text = re.sub(r"(\d+)\s*(?:MB|mb)\b", r"\1 megabajtĂłw", text)
    text = re.sub(r"(\d+)\s*(?:GB|gb)\b", r"\1 gigabajtĂłw", text)
    text = re.sub(r"(\d+)\s*(?:TB|tb)\b", r"\1 terabajtĂłw", text)
    text = re.sub(r"(\d+)\s*(?:GHz|ghz)\b", r"\1 gigahercĂłw", text)
    text = re.sub(r"(\d+)\s*(?:MHz|mhz)\b", r"\1 megahercĂłw", text)
    text = re.sub(r"(\d+)\s*(?:kHz|khz)\b", r"\1 kilohercĂłw", text)
    
    return text

# Implementation note: see the surrounding code for the behavior described here.
def normalize_urls_and_emails(text: str) -> str:
    """Transforms email addresses, URLs, and filenames into spoken format."""
    # Implementation note: see the surrounding code for the behavior described here.
    def email_repl(m: re.Match[str]) -> str:
        user = m.group(1)
        domain = m.group(2).replace(".", " kropka ")
        return f"{user} maĹ‚pa {domain}"
    text = re.sub(r"\b([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b", email_repl, text)

    # Implementation note: see the surrounding code for the behavior described here.
    def url_repl(m: re.Match[str]) -> str:
        full = m.group(0).rstrip(".,;!?:")
        cleaned = re.sub(r"^https?://(?:www\.)?", "", full)
        parts = cleaned.split("/")
        domain = parts[0].replace(".", " kropka ")
        path_str = (" ukoĹ›nik " + " ukoĹ›nik ".join(parts[1:])) if len(parts) > 1 and parts[1] else ""
        return f"adres {domain}{path_str}"
    text = re.sub(r"https?://[^\s\)\"\'<>]+", url_repl, text)

    # Key Go configuration files and extensions
    text = re.sub(r"\bgo\.mod\b", "go kropka mod", text, flags=re.IGNORECASE)
    text = re.sub(r"\bgo\.sum\b", "go kropka sum", text, flags=re.IGNORECASE)
    text = re.sub(r"\b([a-zA-Z0-9_-]+)\.go\b", r"\1 kropka go", text)
    text = re.sub(r"\b([a-zA-Z0-9_-]+)\.json\b", r"\1 kropka dĹĽejson", text)
    text = re.sub(r"\b([a-zA-Z0-9_-]+)\.ya?ml\b", r"\1 kropka jaml", text)
    text = re.sub(r"\b([a-zA-Z0-9_-]+)\.md\b", r"\1 kropka em de", text)
    text = re.sub(r"\b([a-zA-Z0-9_-]+)\.sql\b", r"\1 kropka es kju el", text)
    text = re.sub(r"\b([a-zA-Z0-9_-]+)\.sh\b", r"\1 kropka es ha", text)

    return text

# 5. Programming, mathematical, and special operators
def normalize_operators_and_symbols(text: str) -> str:
    """Normalizes Go operators, math signs, and punctuation symbols."""
    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r":=", " deklaracja i przypisanie ", text)
    text = re.sub(r"!=", " rĂłĹĽne od ", text)
    text = re.sub(r"==", " rĂłwne ", text)
    text = re.sub(r"<=", " mniejsze lub rĂłwne ", text)
    text = re.sub(r">=", " wiÄ™ksze lub rĂłwne ", text)
    text = re.sub(r"<-", " strzaĹ‚ka w lewo ", text)
    text = re.sub(r"->", " strzaĹ‚ka w prawo ", text)
    text = re.sub(r"=>", " strzaĹ‚ka gruba ", text)
    text = re.sub(r"&&", " oraz ", text)
    text = re.sub(r"\|\|", " lub ", text)
    text = re.sub(r"\+\+", " plus plus ", text)
    text = re.sub(r"--", " minus minus ", text)
    text = re.sub(r"\+=", " plus rĂłwna siÄ™ ", text)
    text = re.sub(r"-=", " minus rĂłwna siÄ™ ", text)
    text = re.sub(r"\*=", " razy rĂłwna siÄ™ ", text)
    text = re.sub(r"/=", " podzieliÄ‡ rĂłwna siÄ™ ", text)

    # Mathematical symbols
    text = re.sub(r"Â±", " plus minus ", text)
    text = re.sub(r"â‰ ", " rĂłĹĽne od ", text)
    text = re.sub(r"â‰¤", " mniejsze lub rĂłwne ", text)
    text = re.sub(r"â‰Ą", " wiÄ™ksze lub rĂłwne ", text)
    text = re.sub(r"â‰", " w przybliĹĽeniu ", text)
    text = re.sub(r"Ă—", " razy ", text)
    text = re.sub(r"Ă·", " podzieliÄ‡ przez ", text)

    # printf formats (e.g. %s, %d, %v, %w, %t, %f, %q, %T)
    text = re.sub(r"%([sdvwtfqTbBcxXp])\b", r"procent \1", text)

    # Implementation note: see the surrounding code for the behavior described here.
    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"\*([a-zA-Z][a-zA-Z0-9_]*)\b", r"wskaĹşnik na \1", text)
    # e.g. `&a`, `&x`, `&user` -> "ampersand \1"
    text = re.sub(r"&([a-zA-Z][a-zA-Z0-9_]*)\b", r"ampersand \1", text)

    # Standalone ampersand `&`
    text = re.sub(r"\s+&\s+", " i ", text)
    text = re.sub(r"(?<=[a-zA-Z])&(?!=\w)", " and ", text)
    text = re.sub(r"&", " ampersand ", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"(?<=\d)\s*\*\s*(?=\d)", " razy ", text)
    text = re.sub(r"\*", " gwiazdka ", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"\bCI/CD\b", "ciÄ…gĹ‚a integracja i ciÄ…gĹ‚e wdraĹĽanie", text)
    text = re.sub(r"\bTCP/IP\b", "te ce pe przez aj pi", text)
    text = re.sub(r"\bI/O\b", "wejĹ›cie wyjĹ›cie", text)
    text = re.sub(r"\band/or\b", "i lub", text)
    text = re.sub(r"(?<=[a-zA-ZÄ…Ä‡Ä™Ĺ‚Ĺ„ĂłĹ›ĹşĹĽ])/(?=[a-zA-ZÄ…Ä‡Ä™Ĺ‚Ĺ„ĂłĹ›ĹşĹĽ])", " lub ", text)
    text = re.sub(r"(?<=\d)/(?=\d)", " przez ", text)

    # Tilde `~`
    text = re.sub(r"(?:okoĹ‚o\s+)?~(\d+)", r"okoĹ‚o \1", text)
    text = re.sub(r"~/", "katalog domowy ukoĹ›nik ", text)
    text = re.sub(r"~", " tylda ", text)

    # Dollar sign `$`
    text = re.sub(r"\$(\d+)", r"\1 dolarĂłw", text)
    text = re.sub(r"\$([A-Z_]{2,})", r"zmienna Ĺ›rodowiskowa \1", text)
    text = re.sub(r"\$", " dolar ", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"\b_\b", "podĹ‚oga", text)
    text = re.sub(r"(?<=[a-zA-Z0-9])_(?=[a-zA-Z0-9])", " podkreĹ›lenie ", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"\\n", " znak nowej linii ", text)
    text = re.sub(r"\\t", " znak tabulacji ", text)
    text = re.sub(r"\\r", " powrĂłt karetki ", text)
    text = re.sub(r"\\", " odwrotny ukoĹ›nik ", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"\s+=\s+", " rĂłwna siÄ™ ", text)
    text = re.sub(r"(?<=\s)<(?=\s)", " mniejsze niĹĽ ", text)
    text = re.sub(r"(?<=\s)>(?=\s)", " wiÄ™ksze niĹĽ ", text)
    text = re.sub(r"\s+\|\s+", " lub ", text)

    # Caret `^`
    text = re.sub(r"\^", " daszek ", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_special_characters(text: str) -> str:
    """Main function normalizing all special characters, operators, units, and symbols."""
    if not text:
        return ""

    # 1. Technology names with special characters (e.g. C++, C#, .NET)
    for pat, rep in TECH_NAMES:
        text = re.sub(pat, rep, text)

    # 2. Symbole prawne i typograficzne (np. Â©, Â®, â„˘, Â°C)
    for pat, rep in LEGAL_AND_TYPO_SYMBOLS:
        text = re.sub(pat, rep, text)

    # 3. Jednostki techniczne i bity (np. 1-bitowy, 150 Âµs, 50 ns)
    text = normalize_technical_units(text)

    # 4. Email addresses, URLs, and files
    text = normalize_urls_and_emails(text)

    # 5. Programming and mathematical operators (:=, !=, ==, <-, ->, &, *, $, ~, _, \, /, %, =, <, >)
    text = normalize_operators_and_symbols(text)

    return text
