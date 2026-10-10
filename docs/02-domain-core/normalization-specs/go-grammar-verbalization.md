# Go grammar verbalization specification

## Overview

This document specifies the verbalization rules applied when transforming Go programming syntax into spoken text for neural speech synthesis. Handled by `GoCodeReader` and `lektor.domain.normalizers.go_translators`, this system translates code structures into unambiguous Polish technical narration.

---

## 1. Operator and symbol mappings

Core operators are converted to phonetic verbalizations to avoid silent or incorrect rendering by vocoders:

| Syntax pattern | Verbalized Polish output | Context / semantic role |
| :--- | :--- | :--- |
| `:=` | `deklaracja i przypisanie` | Short variable declaration with type inference |
| `!=` | `różne od` | Inequality comparison |
| `==` | `równe` | Equality comparison |
| `<-ch` | `odbiór z kanału ch` | Channel read operation |
| `ch <- v` | `wysłanie wartości v do kanału ch` | Channel write operation |
| `*Type` | `wskaźnik na Type` | Pointer type declaration or dereference |
| `&var` | `pobranie adresu zmiennej var` | Address-of operator |
| `...Type` | `zmienna liczba argumentów typu Type` | Variadic parameter declaration |

---

## 2. Concurrency and synchronization patterns

Concurrency constructs require explicit semantic explanations rather than raw token reading:

### Channels and select multiplexing
- `case <-time.After(5 * time.Second):` $\to$ `Przypadek case: przekroczenie limitu czasu timeout po upływie pięciu sekund za pomocą time.After.`
- `select { ... }` $\to$ `Instrukcja wyboru select, multiplexująca asynchroniczne operacje na kanałach:`
- `close(ch)` $\to$ `Zamknięcie kanału ch wywołaniem funkcji close, sygnalizujące brak dalszych transmisji.`

### Goroutine spawning
- `go worker()` $\to$ `Uruchomienie współbieżnej gorutyny wykonującej funkcję worker.`
- `go func() { ... }()` $\to$ `Uruchomienie nowej współbieżnej gorutyny realizującej anonimowy literał funkcyjny.`

### Synchronization primitives (`sync`)
- `mu.Lock()` $\to$ `Zablokowanie muteksa mu metodą Lock w celu zabezpieczenia sekcji krytycznej.`
- `defer mu.Unlock()` $\to$ `Odroczone wywołanie defer odblokowania muteksa mu Unlock przy wyjściu z bieżącej funkcji.`
- `wg.Add(1)` $\to$ `Zwiększenie licznika grupy oczekiwania wg o jeden za pomocą metody Add.`
- `wg.Wait()` $\to$ `Zablokowanie wykonywania metodą Wait do czasu ukończenia wszystkich zadań w grupie wg.`

---

## 3. Memory allocation and types

Built-in allocation statements are verbalized with parameter context:

- `make([]byte, 10, 20)` $\to$ `Alokacja wycinka bajtów o nazwie ... funkcją make, o długości początkowej dziesięć oraz pojemności dwadzieścia bajtów.`
- `make(chan int, 5)` $\to$ `Utworzenie buforowanego kanału ... dla typu int o pojemności bufora pięć elementów.`
- `make(chan int)` $\to$ `Utworzenie niebuforowanego kanału ... dla typu int. Kanał wymaga jednoczesnej gotowości nadawcy i odbiorcy.`
- `new(User)` $\to$ `Alokacja zerowej wartości typu User za pomocą new i przypisanie wskaźnika.`

---

## 4. Function signatures and methods

Function declarations are parsed into descriptive prose:

- Receiver parsing: `func (s *Server) Start(port int) error` $\to$ `Definicja metody Start ze wskaźnikowym odbiorcą s typu Server, przyjmująca: argument port typu int, zwracająca wartość typu error.`
- Error handling idiom: `if err != nil` $\to$ `Sprawdzenie błędu: jeśli zmienna err nie jest równa nil, następuje obsługa sytuacji wyjątkowej.`
- Nil return: `return nil` $\to$ `Zwrócenie wartości nil oznaczające pomyślny brak błędu.`
