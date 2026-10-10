"""
lektor.domain.normalizers.spelling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Abstract protocol contract for converting numbers into natural language words.
Pure domain with zero external dependencies.
Strict typing without Any.
"""

from typing import Protocol


class NumberSpellingProtocol(Protocol):
    """Protocol responsible for converting numbers into words in Polish."""

    def int_to_polish_words(self, num: int) -> str:
        """Returns cardinal number in masculine nominative (e.g. 15 -> 'piętnaście')."""
        ...

    def int_to_ordinal_masc_nom(self, num: int) -> str:
        """Returns ordinal number in masculine nominative (e.g. 1 -> 'pierwszy')."""
        ...

    def int_to_ordinal_masc_loc(self, num: int) -> str:
        """Returns ordinal number in masculine locative (e.g. 1976 -> 'tysiąc dziewięćset siedemdziesiątym szóstym')."""
        ...

    def int_to_ordinal_masc_gen(self, num: int) -> str:
        """Returns ordinal number in masculine genitive (e.g. 2024 -> 'dwa tysiące dwudziestego czwartego')."""
        ...

    def int_to_ordinal_fem_nom(self, num: int) -> str:
        """Returns ordinal number in feminine nominative (e.g. 20 -> 'dwudziesta')."""
        ...

    def int_to_ordinal_fem_loc(self, num: int) -> str:
        """Returns ordinal number in feminine locative (e.g. 9 -> 'dziewiątej')."""
        ...
