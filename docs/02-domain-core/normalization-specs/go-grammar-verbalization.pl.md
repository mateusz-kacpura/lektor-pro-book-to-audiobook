# Specyfikacja fonetyzacji składni języka Go

## Przegląd

Dokument określa reguły przekształcania składni języka Go na tekst mówiony przeznaczony dla neuronowych syntezatorów mowy. Odpowiada za to moduł `GoCodeReader` oraz podpakiet `lektor.domain.normalizers.go_translators`, zamieniając konstrukcje kodu na naturalną polską narrację techniczną.

---

## 1. Odwzorowanie operatorów i symboli

Kluczowe operatory kodu są zamieniane na zwroty słowne, co zapobiega zniekształceniom i błędom intonacyjnym lektora:

| Wzorzec składni | Postać mówiona | Znaczenie semantyczne |
| :--- | :--- | :--- |
| `:=` | `deklaracja i przypisanie` | Krótka deklaracja zmiennej z wnioskowaniem typu |
| `!=` | `różne od` | Porównanie nierówności |
| `==` | `równe` | Porównanie równości |
| `<-ch` | `odbiór z kanału ch` | Odczyt wartości z kanału |
| `ch <- v` | `wysłanie wartości v do kanału ch` | Zapis wartości do kanału |
| `*Typ` | `wskaźnik na Typ` | Deklaracja wskaźnika lub dereferencja |
| `&zmienna` | `pobranie adresu zmiennej zmienna` | Operator pobrania adresu pamięci |
| `...Typ` | `zmienna liczba argumentów typu Typ` | Parametr wariadyczny funkcji |

---

## 2. Wzorce współbieżności i synchronizacji

Struktury wielowątkowe wymagają pełnego opisu intencji zamiast surowego czytania znaków:

### Kanały i instrukcja wyboru `select`
- `case <-time.After(5 * time.Second):` $\to$ `Przypadek case: przekroczenie limitu czasu timeout po upływie pięciu sekund za pomocą time.After.`
- `select { ... }` $\to$ `Instrukcja wyboru select, multiplexująca asynchroniczne operacje na kanałach:`
- `close(ch)` $\to$ `Zamknięcie kanału ch wywołaniem funkcji close, sygnalizujące brak dalszych transmisji.`

### Uruchamianie gorutyn
- `go worker()` $\to$ `Uruchomienie współbieżnej gorutyny wykonującej funkcję worker.`
- `go func() { ... }()` $\to$ `Uruchomienie nowej współbieżnej gorutyny realizującej anonimowy literał funkcyjny.`

### Narzędzia synchronizacji (`sync`)
- `mu.Lock()` $\to$ `Zablokowanie muteksa mu metodą Lock w celu zabezpieczenia sekcji krytycznej.`
- `defer mu.Unlock()` $\to$ `Odroczone wywołanie defer odblokowania muteksa mu Unlock przy wyjściu z bieżącej funkcji.`
- `wg.Add(1)` $\to$ `Zwiększenie licznika grupy oczekiwania wg o jeden za pomocą metody Add.`
- `wg.Wait()` $\to$ `Zablokowanie wykonywania metodą Wait do czasu ukończenia wszystkich zadań w grupie wg.`

---

## 3. Alokacja pamięci i typy danych

Instrukcje alokacji są wzbogacane o kontekst parametrów:

- `make([]byte, 10, 20)` $\to$ `Alokacja wycinka bajtów o nazwie ... funkcją make, o długości początkowej dziesięć oraz pojemności dwadzieścia bajtów.`
- `make(chan int, 5)` $\to$ `Utworzenie buforowanego kanału ... dla typu int o pojemności bufora pięć elementów.`
- `make(chan int)` $\to$ `Utworzenie niebuforowanego kanału ... dla typu int. Kanał wymaga jednoczesnej gotowości nadawcy i odbiorcy.`
- `new(User)` $\to$ `Alokacja zerowej wartości typu User za pomocą new i przypisanie wskaźnika.`

---

## 4. Sygnatury funkcji i metody

Deklaracje funkcji i metod są tłumaczone na płynny opis lektorski:

- Odbiornik metody: `func (s *Server) Start(port int) error` $\to$ `Definicja metody Start ze wskaźnikowym odbiorcą s typu Server, przyjmująca: argument port typu int, zwracająca wartość typu error.`
- Obsługa błędów: `if err != nil` $\to$ `Sprawdzenie błędu: jeśli zmienna err nie jest równa nil, następuje obsługa sytuacji wyjątkowej.`
- Puste wyjście z funkcji: `return nil` $\to$ `Zwrócenie wartości nil oznaczające pomyślny brak błędu.`
