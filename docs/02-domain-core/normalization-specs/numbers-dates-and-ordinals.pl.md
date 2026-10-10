# Specyfikacja odmiany liczb, dat i liczebników porządkowych

## Przegląd

Dokument zawiera specyfikację reguł fonetyzacji liczb, ułamków, wartości procentowych, dat, stuleci oraz notacji złożoności obliczeniowej. Za poprawną odmianę gramatyczną odpowiada moduł `lektor.domain.normalizers.numbers`.

---

## 1. Złożoność obliczeniowa i mnożniki

Notacja asymptotyczna oraz mnożniki wydajności są tłumaczone na polskie zwroty matematyczne:

| Notacja matematyczna | Postać mówiona |
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

## 2. Liczby rzymskie: wieki, dekady i części dzieła

Cyfry rzymskie są analizowane w kontekście sąsiadujących słów i odmieniane przez odpowiednie przypadki:

```python
# Wieki w miejscowniku ("w XXI wieku")
"w XXI wieku"   -> "w dwudziestym pierwszym wieku"
"w XIX w."      -> "w dziewiętnastym wieku"

# Wieki w dopełniaczu ("początek XX wieku")
"początek XX w." -> "początek dwudziestego wieku"

# Części książki ("Część I")
"Część I"       -> "Część pierwsza"
"w Części II"   -> "w Części drugiej"

# Dekady ("lata 90.")
"w latach 90."  -> "w latach dziewięćdziesiątych"
"lata 80."      -> "lata osiemdziesiąte"

```

---

## 3. Daty kalendarzowe, lata i wersje oprogramowania

Liczby powiązane z określeniami czasu są rozwijane zgodnie z polską deklinacją:

* Rok w miejscowniku: `w 2024 roku` $\to$ `w dwa tysiące dwudziestym czwartym roku`.
* Zakresy lat w dopełniaczu: `od 1995 do 2010 roku` $\to$ `od tysiąc dziewięćset dziewięćdziesiątego piątego do dwa tysiące dziesiątego roku`.
* Połączenie miesiąca i roku: `w maju 2026 r.` $\to$ `w maju dwa tysiące dwudziestego szóstego roku`.
* Wersjonowanie: `v1.22.4` $\to$ `wersja jeden dwadzieścia dwa cztery`.
* Protokoły sieciowe: `HTTP/2` $\to$ `ha te te pe dwa`, `HTTP/1.1` $\to$ `ha te te pe jeden jeden`.

---

## 4. Wartości procentowe, jednostki i ułamki

* Procenty: `99.9%` $\to$ `dziewięćdziesiąt dziewięć przecinek dziewięć procent`.
* Ułamki dziesiętne: `3.14` $\to$ `trzy przecinek czternaście`.
* Jednostki techniczne: `250 ms` $\to$ `dwieście pięćdziesiąt milisekund`, `64-bitowy` $\to$ `sześćdziesięcioczterobitowy`.
