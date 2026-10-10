#!/usr/bin/env bash

# Skrypt eksportujący zawartość modułu GUI (FastAPI / Templates / Static / Routers)
# Obsługuje pliki: *.html, *.js, *.css, *.json oraz *.py (bez .pyc)
# Generuje strukturę katalogów modułu GUI oraz pełną zawartość plików do jednego pliku tekstowego.

set -euo pipefail

OUTPUT_FILE="${1:-gui_export.txt}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_ROOT"

# Lokalizacja katalogu GUI w architekturze projektu
GUI_DIR="../lektor/adapters/gui"
if [ ! -d "$GUI_DIR" ]; then
    if [ -d "gui" ]; then
        GUI_DIR="gui"
    else
        echo "BŁĄD: Nie odnaleziono katalogu GUI (sprawdzono: $GUI_DIR oraz gui)" >&2
        exit 1
    fi
fi

echo "Rozpoczynam eksport katalogu $GUI_DIR do: $OUTPUT_FILE"
> "$OUTPUT_FILE"

# 1. Nagłówek i data wygenerowania
echo "================================================================================" >> "$OUTPUT_FILE"
echo "EKSPORT MODUŁU GUI: $GUI_DIR" >> "$OUTPUT_FILE"
echo "Data: $(date '+%Y-%m-%d %H:%M:%S')" >> "$OUTPUT_FILE"
echo "Rozszerzenia: *.html, *.js, *.css, *.json, *.py" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 2. Układ katalogów folderu GUI
echo "================================================================================" >> "$OUTPUT_FILE"
echo "STRUKTURA KATALOGÓW: $GUI_DIR/" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"

if command -v tree >/dev/null 2>&1; then
    tree "$GUI_DIR" -I "__pycache__" --noreport >> "$OUTPUT_FILE"
else
    find "$GUI_DIR" -name "__pycache__" -prune -o -type d -print | sort | sed -e 's/[^-][^\/]*\//  |/g' -e 's/|\([^ ]\)/|-- \1/' >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
echo "ZAWARTOŚĆ PLIKÓW MODUŁU GUI" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 3. Wyszukiwanie i eksport plików ze wskazanego katalogu GUI
find "$GUI_DIR" \
    -path "*/__pycache__*" -prune -o \
    -type f \
    \( \
        -name "*.html" -o \
        -name "*.js" -o \
        -name "*.css" -o \
        -name "*.json" -o \
        -name "*.py" \
    \) \
    ! -name "*.pyc" \
    ! -name "$OUTPUT_FILE" \
    -print | sort | while IFS= read -r file; do
        clean_path="${file#./}"
        echo "Eksportowanie: $clean_path"

        echo "--------------------------------------------------------------------------------" >> "$OUTPUT_FILE"
        echo "ŚCIEŻKA: $clean_path" >> "$OUTPUT_FILE"
        echo "--------------------------------------------------------------------------------" >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
done

echo "Eksport zakończony sukcesem!"
echo "Plik wynikowy: $OUTPUT_FILE"