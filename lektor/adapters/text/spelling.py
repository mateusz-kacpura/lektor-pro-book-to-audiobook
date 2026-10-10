"""Text spelling adapter providing number verbalization."""


try:
    import num2words
except ImportError:
    num2words = None

from ...domain.normalizers.spelling import NumberSpellingProtocol


class PolishNumberSpellingAdapter(NumberSpellingProtocol):
    """Adapter translating numbers to Polish words using the num2words library."""

    def int_to_polish_words(self, num: int) -> str:
        if num == 0:
            return "zero"
        if num < 0:
            return f"minus {self.int_to_polish_words(abs(num))}"
        try:
            if num2words is not None:
                return str(num2words.num2words(num, lang="pl"))
            return str(num)
        except Exception:
            return str(num)

    def int_to_ordinal_masc_nom(self, num: int) -> str:
        try:
            if num2words is not None:
                return str(num2words.num2words(num, lang="pl", to="ordinal"))
            return str(num)
        except Exception:
            return str(num)

    def int_to_ordinal_masc_loc(self, num: int) -> str:
        try:
            if num2words is None:
                return str(num)
            ord_str = str(num2words.num2words(num, lang="pl", to="ordinal"))
            words = ord_str.split()
            res: list[str] = []
            for i, w in enumerate(words):
                if i >= max(0, len(words) - 2):
                    if w.endswith("y"):
                        res.append(w[:-1] + "ym")
                    elif w.endswith("i"):
                        res.append(w[:-1] + "im")
                    else:
                        res.append(w)
                else:
                    res.append(w)
            return " ".join(res)
        except Exception:
            return str(num)

    def int_to_ordinal_masc_gen(self, num: int) -> str:
        try:
            if num2words is None:
                return str(num)
            ord_str = str(num2words.num2words(num, lang="pl", to="ordinal"))
            words = ord_str.split()
            res: list[str] = []
            for i, w in enumerate(words):
                if i >= max(0, len(words) - 2):
                    if w.endswith("y"):
                        res.append(w[:-1] + "ego")
                    elif w.endswith("i"):
                        res.append(w[:-1] + "ego")
                    else:
                        res.append(w)
                else:
                    res.append(w)
            return " ".join(res)
        except Exception:
            return str(num)

    def int_to_ordinal_fem_nom(self, num: int) -> str:
        try:
            if num2words is None:
                return str(num)
            ord_str = str(num2words.num2words(num, lang="pl", to="ordinal"))
            words = ord_str.split()
            res: list[str] = []
            for i, w in enumerate(words):
                if i >= max(0, len(words) - 2):
                    if w.endswith("y"):
                        res.append(w[:-1] + "a")
                    elif w.endswith("ci"):
                        res.append(w[:-2] + "cia")
                    elif w.endswith("i"):
                        res.append(w[:-1] + "a")
                    else:
                        res.append(w)
                else:
                    res.append(w)
            return " ".join(res)
        except Exception:
            return str(num)

    def int_to_ordinal_fem_loc(self, num: int) -> str:
        try:
            if num2words is None:
                return str(num)
            ord_str = str(num2words.num2words(num, lang="pl", to="ordinal"))
            words = ord_str.split()
            res: list[str] = []
            for i, w in enumerate(words):
                if i >= max(0, len(words) - 2):
                    if w.endswith("y"):
                        res.append(w[:-1] + "ej")
                    elif w.endswith(("gi", "ki", "ci")):
                        res.append(w[:-1] + "iej")
                    elif w.endswith("i"):
                        res.append(w[:-1] + "ej")
                    else:
                        res.append(w)
                else:
                    res.append(w)
            return " ".join(res)
        except Exception:
            return str(num)
