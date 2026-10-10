# Business rules: text normalization & glossary (BR-006 to BR-010)

## Overview

These business rules define the linguistic invariants, technical glossary protection, and verbalization standards required before submitting text to speech synthesis.

---

### BR-006: Preservation of source code syntax

- **Statement**: During AI vision extraction and linguistic normalization, code blocks (e.g. ```` ```go ````, ```` ```python ````, ```` ```yaml ````) must maintain syntax structure, variable names, and function signatures.
- **Invariant**: Translators and normalizers must never translate keywords, variable names, or logic. Only inline comments within code blocks may be localized.
- **Enforcement**: Dictated by `DEFAULT_SYSTEM_PROMPT` in `lektor.adapters.ocr.vision_adapter` and verified by `lektor.domain.normalizers.code_cleaner.process_code_block`.

---

### BR-007: Cloud Native glossary protection

- **Statement**: Established industry terms (e.g. *Kubernetes*, *Pod*, *gRPC*, *etcd*, *Goroutine*, *Channel*, *Circuit Breaker*) must not be corrupted or translated into Polish equivalents.
- **Invariant**: Terms registered in `PROTECTED_TERMS` are shielded using token placeholders (`__LEKTOR_TERM_{idx}__`) before prompt submission and restored verbatim post-inference.
- **Enforcement**: Handled by `lektor.domain.normalizers.glossary.TechnicalGlossaryService`.

```python
# Term tokenization process
raw = "Kubernetes clusters route gRPC payloads to Pods."
protected, tokens = glossary.protect_technical_terms(raw)
# Result: "__LEKTOR_TERM_0__ clusters route __LEKTOR_TERM_12__ payloads to __LEKTOR_TERM_3__."
restored = glossary.restore_technical_terms(protected, tokens)

```

---

### BR-008: Deterministic verbalization of Go grammar

* **Statement**: Programming operators and language constructs must be expanded into unambiguous, phonetically natural Polish words suitable for text-to-speech.
* **Invariant**: The normalizer must map operators according to explicit rules:
* `:=` $\to$ `deklaracja i przypisanie`
* `!=` $\to$ `różne od`
* `==` $\to$ `równe`
* `<-` $\to$ `odbiór lub wysłanie do kanału`
* `*Type` $\to$ `wskaźnik na Type`
* `&variable` $\to$ `ampersand variable` / `pobranie adresu zmiennej variable`


* **Enforcement**: Governed by `GoCodeReader` and `lektor.domain.normalizers.go_translators`.

---

### BR-009: Grammatical verbalization of numerals and dates

* **Statement**: All raw digits, ordinals, dates, percentages, and complexity notations must be fully spelled out into grammatically inflected words.
* **Invariant**:
* Mathematical complexity: $O(1)$ $\to$ `złożoność rzędu jeden`, $O(n \log n)$ $\to$ `złożoność rzędu en logarytm en`.
* Centuries: `XXI wieku` $\to$ `dwudziestego pierwszego wieku`.
* Decades: `w latach 90.` $\to$ `w latach dziewięćdziesiątych`.
* Versions: `v2.4.1` $\to$ `wersja dwa cztery jeden`.


* **Enforcement**: Managed by `lektor.domain.normalizers.numbers.normalize_numbers_and_symbols`.

---

### BR-010: Stripping of non-spoken Markdown markup

* **Statement**: Visual-only artifacts and document metadata must be stripped out prior to speech synthesis to prevent vocoder stuttering and audio artifacts.
* **Invariant**:
* Footnote definitions (`[^1]: ...`) and inline citations (`[^1]`) are removed completely.
* HTML comments (`<!-- ... -->`) and YAML frontmatter blocks are pruned.
* Ellipses (`...` / `…`) at boundaries are removed to avoid pauses and acoustic trailing noise.


* **Enforcement**: Executed by `lektor.domain.normalizers.markdown.clean_markdown_document`.
