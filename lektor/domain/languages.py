"""
Shared language catalog and TTS model code mappings.

Serves as the Single Source of Truth for GUI, OCR, and TTS adapters.
OmniVoice supports arbitrary ISO codes, while Chatterbox uses its native 23 languages.
"""

import re
from dataclasses import dataclass
from typing import Final, Literal, TypedDict

TTSProvider = Literal["omnivoice", "chatterbox"]


class LanguageOption(TypedDict):
    """Language catalog row returned to the user interface."""

    code: str
    name: str
    name_pl: str
    name_en: str
    flag: str
    popular: bool
    custom: bool


@dataclass(frozen=True)
class LanguageSpec:
    """Language specification including model-specific codes."""

    code: str
    name_pl: str
    name_en: str
    flag: str
    omnivoice_code: str | None = None
    chatterbox_code: str | None = None
    popular: bool = False

    def model_code(self, provider: TTSProvider) -> str | None:
        """Returns provider code for the specified TTS model."""
        if provider == "omnivoice":
            return self.omnivoice_code
        return self.chatterbox_code


_POPULAR_SPECS: Final[tuple[LanguageSpec, ...]] = (
    LanguageSpec("pl", "polski", "Polish", "🇵🇱", "pl", "pl", True),
    LanguageSpec("en", "angielski", "English", "🇬🇧", "en", "en", True),
    LanguageSpec("de", "niemiecki", "German", "🇩🇪", "de", "de", True),
    LanguageSpec("es", "hiszpański", "Spanish", "🇪🇸", "es", "es", True),
    LanguageSpec("fr", "francuski", "French", "🇫🇷", "fr", "fr", True),
    LanguageSpec("it", "włoski", "Italian", "🇮🇹", "it", "it", True),
    LanguageSpec("uk", "ukraiński", "Ukrainian", "🇺🇦", "uk", None, True),
    LanguageSpec("ja", "japoński", "Japanese", "🇯🇵", "ja", "ja", True),
    LanguageSpec("zh", "chiński", "Chinese", "🇨🇳", "zh", "zh", True),
    LanguageSpec("pt", "portugalski", "Portuguese", "🇵🇹", "pt", "pt", True),
)


_CHATTERBOX_SPECS: Final[tuple[LanguageSpec, ...]] = (
    LanguageSpec("ar", "arabski", "Arabic", "🇸🇦", "ar", "ar"),
    LanguageSpec("da", "duński", "Danish", "🇩🇰", "da", "da"),
    LanguageSpec("el", "grecki", "Greek", "🇬🇷", "el", "el"),
    LanguageSpec("fi", "fiński", "Finnish", "🇫🇮", "fi", "fi"),
    LanguageSpec("he", "hebrajski", "Hebrew", "🇮🇱", "he", "he"),
    LanguageSpec("hi", "hindi", "Hindi", "🇮🇳", "hi", "hi"),
    LanguageSpec("ko", "koreański", "Korean", "🇰🇷", "ko", "ko"),
    LanguageSpec("ms", "malajski", "Malay", "🇲🇾", "ms", "ms"),
    LanguageSpec("nl", "niderlandzki", "Dutch", "🇳🇱", "nl", "nl"),
    LanguageSpec("no", "norweski", "Norwegian", "🇳🇴", "no", "no"),
    LanguageSpec("ru", "rosyjski", "Russian", "🇷🇺", "ru", "ru"),
    LanguageSpec("sv", "szwedzki", "Swedish", "🇸🇪", "sv", "sv"),
    LanguageSpec("sw", "suahili", "Swahili", "🇰🇪", "sw", "sw"),
    LanguageSpec("tr", "turecki", "Turkish", "🇹🇷", "tr", "tr"),
)


_OMNIVOICE_COMMON_CODES: Final[tuple[str, ...]] = (
    "af", "am", "az", "be", "bg", "bn", "bs", "ca", "cs", "cy", "et", "eu",
    "fa", "fil", "ga", "gl", "gu", "ha", "hr", "hu", "hy", "id", "is", "ka",
    "kk", "km", "kn", "ky", "la", "lb", "lo", "lt", "lv", "mk", "ml", "mn",
    "mr", "mt", "my", "ne", "pa", "ps", "ro", "sk", "sl", "so", "sq", "sr",
    "ta", "te", "tg", "th", "tk", "tt", "ur", "uz", "vi", "xh", "yi", "yo", "zu",
)


_COMMON_NAMES: Final[dict[str, tuple[str, str, str]]] = {
    "af": ("afrikaans", "Afrikaans", "🇿🇦"),
    "am": ("amharski", "Amharic", "🇪🇹"),
    "az": ("azerski", "Azerbaijani", "🇦🇿"),
    "be": ("białoruski", "Belarusian", "🇧🇾"),
    "bg": ("bułgarski", "Bulgarian", "🇧🇬"),
    "bn": ("bengalski", "Bengali", "🇧🇩"),
    "bs": ("bośniacki", "Bosnian", "🇧🇦"),
    "ca": ("kataloński", "Catalan", "🇪🇸"),
    "cs": ("czeski", "Czech", "🇨🇿"),
    "cy": ("walijski", "Welsh", "🏴󠁧󠁢󠁷󠁬󠁳󠁿"),
    "et": ("estoński", "Estonian", "🇪🇪"),
    "eu": ("baskijski", "Basque", "🇪🇸"),
    "fa": ("perski", "Persian", "🇮🇷"),
    "fil": ("filipiński", "Filipino", "🇵🇭"),
    "ga": ("irlandzki", "Irish", "🇮🇪"),
    "gl": ("galicyjski", "Galician", "🇪🇸"),
    "gu": ("gudżarati", "Gujarati", "🇮🇳"),
    "ha": ("hausa", "Hausa", "🇳🇬"),
    "hr": ("chorwacki", "Croatian", "🇭🇷"),
    "hu": ("węgierski", "Hungarian", "🇭🇺"),
    "hy": ("ormiański", "Armenian", "🇦🇲"),
    "id": ("indonezyjski", "Indonesian", "🇮🇩"),
    "is": ("islandzki", "Icelandic", "🇮🇸"),
    "ka": ("gruziński", "Georgian", "🇬🇪"),
    "kk": ("kazachski", "Kazakh", "🇰🇿"),
    "km": ("khmerski", "Khmer", "🇰🇭"),
    "kn": ("kannada", "Kannada", "🇮🇳"),
    "ky": ("kirgiski", "Kyrgyz", "🇰🇬"),
    "la": ("łaciński", "Latin", "🌐"),
    "lb": ("luksemburski", "Luxembourgish", "🇱🇺"),
    "lo": ("laotański", "Lao", "🇱🇦"),
    "lt": ("litewski", "Lithuanian", "🇱🇹"),
    "lv": ("łotewski", "Latvian", "🇱🇻"),
    "mk": ("macedoński", "Macedonian", "🇲🇰"),
    "ml": ("malajalam", "Malayalam", "🇮🇳"),
    "mn": ("mongolski", "Mongolian", "🇲🇳"),
    "mr": ("marathi", "Marathi", "🇮🇳"),
    "mt": ("maltański", "Maltese", "🇲🇹"),
    "my": ("birmański", "Burmese", "🇲🇲"),
    "ne": ("nepalski", "Nepali", "🇳🇵"),
    "pa": ("pendżabski", "Punjabi", "🇮🇳"),
    "ps": ("paszto", "Pashto", "🇦🇫"),
    "ro": ("rumuński", "Romanian", "🇷🇴"),
    "sk": ("słowacki", "Slovak", "🇸🇰"),
    "sl": ("słoweński", "Slovenian", "🇸🇮"),
    "so": ("somalijski", "Somali", "🇸🇴"),
    "sq": ("albański", "Albanian", "🇦🇱"),
    "sr": ("serbski", "Serbian", "🇷🇸"),
    "ta": ("tamilski", "Tamil", "🇮🇳"),
    "te": ("telugu", "Telugu", "🇮🇳"),
    "tg": ("tadżycki", "Tajik", "🇹🇯"),
    "th": ("tajski", "Thai", "🇹🇭"),
    "tk": ("turkmeński", "Turkmen", "🇹🇲"),
    "tt": ("tatarski", "Tatar", "🇷🇺"),
    "ur": ("urdu", "Urdu", "🇵🇰"),
    "uz": ("uzbecki", "Uzbek", "🇺🇿"),
    "vi": ("wietnamski", "Vietnamese", "🇻🇳"),
    "xh": ("khosa", "Xhosa", "🇿🇦"),
    "yi": ("jidysz", "Yiddish", "🌐"),
    "yo": ("joruba", "Yoruba", "🇳🇬"),
    "zu": ("zulu", "Zulu", "🇿🇦"),
}


def _build_catalog() -> tuple[LanguageSpec, ...]:
    by_code: dict[str, LanguageSpec] = {spec.code: spec for spec in _POPULAR_SPECS}
    by_code.update({spec.code: spec for spec in _CHATTERBOX_SPECS})
    for code in _OMNIVOICE_COMMON_CODES:
        if code in by_code:
            continue
        name_pl, name_en, flag = _COMMON_NAMES[code]
        by_code[code] = LanguageSpec(code, name_pl, name_en, flag, code, None)
    return tuple(by_code.values())


LANGUAGE_CATALOG: Final[tuple[LanguageSpec, ...]] = _build_catalog()
SUPPORTED_LANGUAGE_CODES: Final[frozenset[str]] = frozenset(spec.code for spec in LANGUAGE_CATALOG)
POPULAR_LANGUAGE_CODES: Final[tuple[str, ...]] = tuple(spec.code for spec in _POPULAR_SPECS)
_LANGUAGE_BY_CODE: Final[dict[str, LanguageSpec]] = {spec.code: spec for spec in LANGUAGE_CATALOG}

_LANGUAGE_ALIASES: Final[dict[str, str]] = {
    "polski": "pl", "polish": "pl", "język polski": "pl",
    "angielski": "en", "english": "en", "język angielski": "en",
    "niemiecki": "de", "german": "de", "hiszpański": "es", "spanish": "es",
    "francuski": "fr", "french": "fr", "włoski": "it", "italian": "it",
    "ukraiński": "uk", "ukrainian": "uk", "japoński": "ja", "japanese": "ja",
    "chiński": "zh", "chinese": "zh", "portugalski": "pt", "portuguese": "pt",
}


for _spec in LANGUAGE_CATALOG:
    _LANGUAGE_ALIASES.setdefault(_spec.name_pl.casefold(), _spec.code)
    _LANGUAGE_ALIASES.setdefault(_spec.name_en.casefold(), _spec.code)


def normalize_language_code(language: str | None, default: str = "pl") -> str:
    """Normalizes ISO code, OmniVoice code, or catalog name."""
    if not language:
        return default
    normalized = language.strip().lower().replace("_", "-")
    alias = _LANGUAGE_ALIASES.get(normalized)
    if alias is not None:
        return alias
    base_code = normalized.split("-", maxsplit=1)[0]
    if re.fullmatch(r"[a-z]{2,3}", base_code):
        return base_code
    return default


def get_language_spec(language: str, *, allow_custom: bool = True) -> LanguageSpec:
    """Returns language specification; allows 2-3 char codes for OmniVoice."""
    code = normalize_language_code(language)
    known = _LANGUAGE_BY_CODE.get(code)
    if known is not None:
        return known
    if allow_custom and re.fullmatch(r"[a-z]{2,3}", code):
        return LanguageSpec(code, code.upper(), code.upper(), "🌐", code, None)
    raise ValueError(f"Nieprawidłowy kod języka: {language!r}")


def language_display_name(language: str) -> str:
    """Returns language display name for OCR prompts and telemetry."""
    spec = get_language_spec(language)
    return f"język {spec.name_pl} ({spec.name_en})"


def language_options(provider: TTSProvider = "omnivoice") -> list[LanguageOption]:
    """Builds ordered GUI language list, popular languages first."""
    if provider not in ("omnivoice", "chatterbox"):
        raise ValueError(f"Nieobsługiwany dostawca TTS: {provider}")

    available = [spec for spec in LANGUAGE_CATALOG if spec.model_code(provider) is not None]
    position = {code: index for index, code in enumerate(POPULAR_LANGUAGE_CODES)}
    available.sort(key=lambda spec: (0, position[spec.code]) if spec.popular else (1, spec.name_pl))

    result: list[LanguageOption] = []
    for spec in available:
        result.append(
            {
                "code": spec.code,
                "name": f"{spec.flag} Język {spec.name_pl} ({spec.name_en})",
                "name_pl": spec.name_pl,
                "name_en": spec.name_en,
                "flag": spec.flag,
                "popular": spec.popular,
                "custom": False,
            }
        )
    result.append(
        {
            "code": "__custom__",
            "name": "🌐 Inny język (wpisz kod lub nazwę)…",
            "name_pl": "Inny język",
            "name_en": "Custom language",
            "flag": "🌐",
            "popular": False,
            "custom": True,
        }
    )
    return result


def is_supported_language(language: str, provider: TTSProvider = "omnivoice") -> bool:
    """Checks if language is supported by the given model catalog."""
    try:
        return get_language_spec(language, allow_custom=False).model_code(provider) is not None
    except ValueError:
        return False


def provider_language_code(language: str, provider: TTSProvider) -> str:
    """Maps application code to provider model code."""
    spec = get_language_spec(language, allow_custom=provider == "omnivoice")
    model_code = spec.model_code(provider)
    if model_code is None:
        raise ValueError(
            f"Język {spec.name_pl} nie jest obsługiwany przez model {provider}. "
            "Wybierz język dostępny na liście tego modelu."
        )
    return model_code


@dataclass(frozen=True)
class LanguagePair:
    """Primary and secondary language pair configuration."""

    primary: str = "pl"
    secondary: str | None = "en"

    def __post_init__(self) -> None:
        primary = normalize_language_code(self.primary)
        secondary = normalize_language_code(self.secondary) if self.secondary else None
        if secondary == primary:
            secondary = None
        object.__setattr__(self, "primary", primary)
        object.__setattr__(self, "secondary", secondary)

    @property
    def is_bilingual(self) -> bool:
        return self.secondary is not None

    @classmethod
    def from_legacy_mode(cls, language_mode: str) -> "LanguagePair":
        if language_mode == "bilingual":
            return cls()
        return cls(primary=language_mode, secondary=None)


__all__ = [
    "LANGUAGE_CATALOG",
    "POPULAR_LANGUAGE_CODES",
    "SUPPORTED_LANGUAGE_CODES",
    "LanguageOption",
    "LanguagePair",
    "LanguageSpec",
    "TTSProvider",
    "get_language_spec",
    "is_supported_language",
    "language_display_name",
    "language_options",
    "normalize_language_code",
    "provider_language_code",
]

