# Reguły integralności dokumentów Markdown

## Przegląd

Dokument określa kryteria walidacji oraz niezmienniki strukturalne wymuszane na przetłumaczonych stronach Markdown przed ich zapisaniem na dysku. Zaimplementowane w module `lektor.domain.validators.markdown_validator`, reguły te gwarantują spójność składniową, kompletność treści oraz poprawność formatowania.

---

## 1. Niezmienniki na poziomie dokumentu

Usługa domenowa `MarkdownPageValidationService.validate_page_integrity` weryfikuje stronę pod kątem następujących wymogów:

| Niezmiennik | Kryterium weryfikacji | Warunek niespełnienia |
| :--- | :--- | :--- |
| **Treść niepusta** | Długość tekstu po usunięciu spacji musi przekraczać 20 znaków | Odrzucenie strony w przypadku pustego wyniku |
| **Parzystość bloków kodu** | Znaczniki grawisów (```` ``` ````) muszą występować parami | Nieparzysta liczba oznacza niedomknięty blok kodu |
| **Obecność nagłówka** | Strona musi zawierać przynajmniej jeden nagłówek (`#`, `##`, `###`) | Ostrzeżenie w przypadku braku struktury tematycznej |
| **Kompletność diagramów** | Bloki Mermaid muszą posiadać poprawne słowa kluczowe i domknięte nawiasy | Błąd walidacji w przypadku uszkodzonej składni grafu |

---

## 2. Parzystość i domykanie bloków kodu

Fragmenty kodu źródłowego muszą być domknięte, aby zapobiec interpretowaniu tekstu narracyjnego jako części listingu.

```python
def check_code_fence_parity(content: str) -> bool:
    fences = re.findall(r"^```", content, re.MULTILINE)
    return len(fences) % 2 == 0

```

* W przypadku wykrycia niedomkniętego bloku kodu na końcu odpowiedzi modelu (np. z powodu ucięcia kontekstu), potok walidacji wykonuje automatyczną naprawę przez dodanie domykającego znacznika ````` lub oznacza stronę do ponownej syntezy, jeśli ubytek przekracza dopuszczalny próg.

---

## 3. Automatyczna naprawa drobnych usterek formatowania

W przypadku drobnych odchyleń generowania metoda `MarkdownPageValidationService.repair_structural_glitches` stosuje bezpieczne korekty:

1. **Niedomknięte gwiazdki**: Usuwa pojedyncze znaczniki pogrubienia lub kursywy na końcach zdań.
2. **Wielokropki końcowe**: Zastępuje wiszące wielokropki (`...` / `…`) kropką kończącą zdanie (`.`).
3. **Uciekające grawisy**: Usuwa niepotrzebne ukośniki poprzedzające kod inline (`\` -> ```).
4. **Odstępy wokół nagłówków**: Wymusza puste linie przed i po nagłówkach Markdown (`\n\n# Nagłówek\n\n`).
