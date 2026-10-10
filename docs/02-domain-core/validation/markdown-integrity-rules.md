# Markdown integrity rules

## Overview

This specification defines the validation criteria and structural invariants enforced on generated Polish Markdown pages prior to persistence. Implemented in `lektor.domain.validators.markdown_validator`, these rules guarantee document sanity, syntax preservation, and completeness.

---

## 1. Document-level invariants

The `MarkdownPageValidationService.validate_page_integrity` service evaluates output Markdown against structural requirements:

| Invariant rule | Verification criteria | Failure condition |
| :--- | :--- | :--- |
| **Non-empty content** | Text length must exceed 20 characters after stripping whitespace | Page rejected if empty or stub |
| **Code fence balance** | Triple-backtick markers (```` ``` ````) must appear in pairs | Odd count indicates an unclosed code block |
| **Heading presence** | Page must contain at least one Markdown heading (`#`, `##`, `###`) | Emits warning if page lacks topical structure |
| **Diagram completeness** | Mermaid blocks must have valid opening keywords and closed node brackets | Broken graph syntax raises validation errors |

---

## 2. Code block parity and fence balance

Source code snippets must be closed to avoid leaking text into syntax-highlighted containers.

```python
def check_code_fence_parity(content: str) -> bool:
    fences = re.findall(r"^```", content, re.MULTILINE)
    return len(fences) % 2 == 0

```

* If an unclosed code block is detected at the end of an LLM generation due to context cut-off, the validation pipeline triggers an automated repair pass by appending a closing ````` fence, or flags the page for regeneration if truncation exceeds threshold bounds.

---

## 3. Structural repair and normalization pass

When minor formatting deviations occur during multimodal extraction, `MarkdownPageValidationService.repair_structural_glitches` executes safe automated corrections:

1. **Unbalanced asterisks**: Repairs dangling bold/italic markers at sentence boundaries.
2. **Trailing ellipses**: Replaces trailing `...` or `…` with clean terminal punctuation (`.`).
3. **Escaped backticks**: Normalizes unintended escaping of inline code backticks (`\` -> ```).
4. **Header spacing**: Ensures standard blank lines precede and follow heading lines (`\n\n# Heading\n\n`).
