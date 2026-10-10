# Numbers, dates & ordinals specification

## Overview

This specification details the verbalization of numbers, fractions, percentages, dates, centuries, and computational complexity notation. Managed by `lektor.domain.normalizers.numbers`, these transformations ensure digits are fully converted to grammatically inflected Polish words.

---

## 1. Computational complexity and multipliers

Mathematical asymptotic notation and performance multipliers are verbalized into standard Polish terminology:

| Mathematical notation | Spoken Polish verbalization |
| :--- | :--- |
| $O(1)$ | `złożoność rzędu jeden` |
| $O(n)$ | `złożoność rzędu en` |
| $O(\log n)$ | `złożoność rzędu logarytm en` |
| $O(n \log n)$ | `złożoność rzędu en logarytm en` |
| $O(n^2)$ | `złożoność rzędu en do kwadratu` |
| `10x` | `dziesięciokrotnie` |
| `100x` | `stukrotnie` |
| `10-krotne` | `dziesięciokrotne` |

---

## 2. Roman numerals: centuries, decades & parts

Roman numerals are contextualized by adjacent keywords and inflected into correct grammatical cases:

```python
# Centuries in locative ("w XXI wieku")
"w XXI wieku"   -> "w dwudziestym pierwszym wieku"
"w XIX w."      -> "w dziewiętnastym wieku"

# Centuries in genitive ("początek XX wieku")
"początek XX w." -> "początek dwudziestego wieku"

# Book parts ("Część I")
"Część I"       -> "Część pierwsza"
"w Części II"   -> "w Części drugiej"

# Decades ("lata 90.")
"w latach 90."  -> "w latach dziewięćdziesiątych"
"lata 80."      -> "lata osiemdziesiąte"

```

---

## 3. Calendar dates, years & versions

Digits followed by calendar descriptors are expanded based on Polish declension:

* Years with `w roku`: `w 2024 roku` $\to$ `w dwa tysiące dwudziestym czwartym roku` (locative).
* Years with ranges: `od 1995 do 2010 roku` $\to$ `od tysiąc dziewięćset dziewięćdziesiątego piątego do dwa tysiące dziesiątego roku` (genitive).
* Month-year pairs: `w maju 2026 r.` $\to$ `w maju dwa tysiące dwudziestego szóstego roku`.
* Semantic versions: `v1.22.4` $\to$ `wersja jeden dwadzieścia dwa cztery`.
* Protocol versions: `HTTP/2` $\to$ `ha te te pe dwa`, `HTTP/1.1` $\to$ `ha te te pe jeden jeden`.

---

## 4. Percentages, units & decimals

* Percentages: `99.9%` $\to$ `dziewięćdziesiąt dziewięć przecinek dziewięć procent`.
* Decimals: `3.14` $\to$ `trzy przecinek czternaście`.
* Technical units: `250 ms` $\to$ `dwieście pięćdziesiąt milisekund`, `64-bitowy` $\to$ `sześćdziesięcioczterobitowy`.
