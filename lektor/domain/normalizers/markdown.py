"""
Markdown syntax cleaning and pre-normalization.
Removes footnotes, headers, tables, links, and bold/italic markup.
"""
import re


def clean_markdown_document(text: str) -> str:
    """Cleans entire Markdown document structure before speech segmentation."""
    # Implementation note: see the surrounding code for the behavior described here.
    is_endnotes_page = bool(re.search(r"przypisy\s+ko[nĹ„]cowe", text, re.IGNORECASE))

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", text, flags=re.DOTALL)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(
        r"#{1,6}\s*Przypisy\s+ko[nĹ„]cowe.*?(?=(\n#{1,3}\s|\Z))",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Implementation note: see the surrounding code for the behavior described here.
    # e.g. [^1]: ..., - [^1]: ..., - [^1] **1:** ..., [^1] **Footnote 1:** ...
    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(
        r"^\s*[-*]?\s*\[\^\d+\].*(?:\n(?:[ \t]{2,}|\t).*)*",
        "",
        text,
        flags=re.MULTILINE
    )

    # Implementation note: see the surrounding code for the behavior described here.
    # Implementation note: see the surrounding code for the behavior described here.
    # Implementation note: see the surrounding code for the behavior described here.
    if is_endnotes_page:
        text = re.sub(r"^\s*\*\*\d+\*\*\s+.*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*#+\s*Strona\s+\d+\s*[â€”â€“-]\s*Przypisy\s+ko[nĹ„]cowe.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r"^\s*#+\s*Przypisy\s+ko[nĹ„]cowe.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"\s*(?:oraz|i)\s*przypis(?:y)?(?:\s+ko[nĹ„]cowe)?(?:\s*\(.*?\))?", "", text, flags=re.IGNORECASE)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"\[\^\d+\]", "", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"^\s*\*?Oryginalny\s+skan\s+strony:?\*?\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^\s*<br\s*/?>\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", "", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"^\s*#\s*Strona\s+\d+\s*[â€”â€“-].*$", "", text, flags=re.MULTILINE)

    return text


def clean_markdown_structure(text: str) -> str:
    """Removes Markdown syntax markers and converts them to readable text."""
    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"^\s*#\s*Strona\s+\d+\s*[â€”â€“-].*$", "", text, flags=re.MULTILINE)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"<[^>]+>", " ", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Implementation note: see the surrounding code for the behavior described here.
    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"^\s*[-*]?\s*\[\^\d+\].*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[\^\d+\]", "", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*\n]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"(?<=\s)\*(?=\s)", " ", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Implementation note: see the surrounding code for the behavior described here.
    text = text.replace("â€”", ", ")
    text = text.replace("â€“", ", ")

    # Implementation note: see the surrounding code for the behavior described here.
    text = text.replace("â€ž", '"').replace("â€ť", '"').replace("Â»", '"').replace("Â«", '"')
    text = text.replace("â€™", "'").replace("â€", "'")

    # Implementation note: see the surrounding code for the behavior described here.
    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"^[ \t]*(\.{2,}|â€¦)[ \t]*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]*(\.{2,}|â€¦)[ \t]*$", ".", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]*(\.{2,}|â€¦)[ \t]*", ", ", text)

    # Implementation note: see the surrounding code for the behavior described here.
    text = re.sub(r"^[ \t]*[,;:\-â€“â€”]+[ \t]*", "", text, flags=re.MULTILINE)

    return text


def extract_markdown_title(md_text: str, fallback_title: str = "Nagranie") -> str:
    """Extracts title from Markdown text (first level-1 header)."""
    for line in md_text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            clean = re.sub(r"^#+\s*", "", line).strip()
            clean = re.sub(r"^Strona\s+\d+\s*[â€”â€“-]\s*", "", clean).strip()
            if clean:
                return clean[:80]
    cleaned = re.sub(r"[`*#_\-\[\]()]", "", md_text).strip()
    first_sentence = cleaned.split(".")[0].strip()
    if first_sentence:
        return first_sentence[:50]
    return fallback_title

