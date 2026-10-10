# Reguły biznesowe: normalizacja tekstu i słownik (BR-006 do BR-010)

## Przegląd

Niniejsze reguły określają standardy lingwistyczne, zasady ochrony pojęć technicznych oraz reguły przekształcania tekstu pisanego na postać mówioną przed wysłaniem do silników syntezy.

---

### BR-006: Ochrona składni kodu źródłowego

- **Treść reguły**: Podczas ekstrakcji wizyjnej i normalizacji tekstu bloki kodu (np. ```` ```go ````, ```` ```python ````, ```` ```yaml ````) muszą zachować nienaruszoną strukturę składniową, nazwy zmiennych i sygnatury funkcji.
- **Niezmiennik**: Tłumaczeniu podlegają wyłącznie komentarze wewnątrz bloków kodu. Słowa kluczowe i identyfikatory muszą pozostać w oryginalnym zapisie.
- **Egzekwowanie**: Wymagane przez `DEFAULT_SYSTEM_PROMPT` w `lektor.adapters.ocr.vision_adapter` oraz weryfikowane przez `lektor.domain.normalizers.code_cleaner.process_code_block`.

---

### BR-007: Ochrona terminologii Cloud Native

- **Treść reguły**: Powszechnie przyjęte terminy branżowe (np. *Kubernetes*, *Pod*, *gRPC*, *etcd*, *Goroutine*, *Channel*, *Circuit Breaker*) nie mogą być zniekształcane ani tłumaczone na nieporadne odpowiedniki polskie.
- **Niezmiennik**: Terminy ze słownika `PROTECTED_TERMS` są zastępowane tokenami `__LEKTOR_TERM_{idx}__` przed analizą przez model językowy i przywracane w oryginalnej postaci po zakończeniu tłumaczenia.
- **Egzekwowanie**: Realizowane przez `lektor.domain.normalizers.glossary.TechnicalGlossaryService`.

```python
# Przebieg tokenizacji terminów
surowy = "Klastry Kubernetes przekazują ruch gRPC do obiektów Pod."
chroniony, tokeny = glossary.protect_technical_terms(surowy)
# Wynik: "Klastry __LEKTOR_TERM_0__ przekazują ruch __LEKTOR_TERM_12__ do obiektów __LEKTOR_TERM_3__."
przywrocony = glossary.restore_technical_terms(chroniony, tokeny)

```

---

### BR-008: Deterministyczna fonetyzacja składni Go

* **Treść reguły**: Operatory programistyczne oraz idiomy języka Go muszą być przekształcane na jednoznaczne, naturalne zwroty w języku polskim.
* **Niezmiennik**: Normalizator przypisuje fonetyczne odpowiedniki według ścisłych reguł:
* `:=` $\to$ `deklaracja i przypisanie`
* `!=` $\to$ `różne od`
* `==` $\to$ `równe`
* `<-` $\to$ `odbiór lub wysłanie do kanału`
* `*Typ` $\to$ `wskaźnik na Typ`
* `&zmienna` $\to$ `ampersand zmienna` lub `pobranie adresu zmiennej zmienna`


* **Egzekwowanie**: Zarządzane przez moduł `GoCodeReader` oraz podpakiet `lektor.domain.normalizers.go_translators`.

---

### BR-009: Gramatyczna odmiana liczb i dat

* **Treść reguły**: Wszystkie cyfry arabskie, liczebniki porządkowe, daty, procenty oraz zapisy złożoności obliczeniowej muszą zostać zamienione na słowa z poprawną odmianą gramatyczną.
* **Niezmiennik**:
* Złożoność obliczeniowa: $O(1)$ $\to$ `złożoność rzędu jeden`, $O(n \log n)$ $\to$ `złożoność rzędu en logarytm en`.
* Wieki: `XXI wieku` $\to$ `dwudziestego pierwszego wieku`.
* Dekady: `w latach 90.` $\to$ `w latach dziewięćdziesiątych`.
* Wersje: `v2.4.1` $\to$ `wersja dwa cztery jeden`.


* **Egzekwowanie**: Realizowane przez `lektor.domain.normalizers.numbers.normalize_numbers_and_symbols`.

---

### BR-010: Usuwanie elementów wizualnych Markdownu

* **Treść reguły**: Elementy typograficzne przeznaczone wyłącznie dla wzroku oraz metadane muszą zostać usunięte z tekstu przed syntezą mowy, aby zapobiec artefaktom i zakłóceniom dźwiękowym.
* **Niezmiennik**:
* Definicje przypisów dolnych (`[^1]: ...`) i odsyłacze w treści (`[^1]`) są usuwane w całości.
* Komentarze HTML (`<!-- ... -->`) oraz bloki nagłówka YAML są odcinane.
* Wielokropki (`...` / `…`) na krawędziach zdań są wycinane, co eliminuje wahania intonacji i dudnienie lektora.


* **Egzekwowanie**: Realizowane przez `lektor.domain.normalizers.markdown.clean_markdown_document`.
