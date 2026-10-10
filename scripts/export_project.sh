#!/usr/bin/env bash

# Skrypt eksportujący pliki projektu do jednego pliku tekstowego.
# Zawiera pliki *.py (bez .pyc), *.yml, *.yaml, .env.example, .gitignore
# oraz strukturę katalogów folderu 'data'.

set -euo pipefail

OUTPUT_FILE="${1:-project_export.txt}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_ROOT"

echo "Rozpoczynam eksport projektu do: $OUTPUT_FILE"
> "$OUTPUT_FILE"

# 1. Nagłówek i data wygenerowania
echo "================================================================================" >> "$OUTPUT_FILE"
echo "EKSPORT PROJEKTU: Cloud Native in Go / Lektor" >> "$OUTPUT_FILE"
echo "Data: $(date '+%Y-%m-%d %H:%M:%S')" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 2. Układ katalogów folderu data
echo "================================================================================" >> "$OUTPUT_FILE"
echo "STRUKTURA KATALOGÓW: data/" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"

if [ -d "data" ]; then
    if command -v tree >/dev/null 2>&1; then
        tree data -d -I ".cache|__pycache__" --noreport >> "$OUTPUT_FILE"
    else
        # Reprezentacja drzewiasta w czystym Bashu (z pominięciem wewnętrznego .cache i __pycache__)
        find data \( -name ".cache" -o -name "__pycache__" \) -prune -o -type d -print | sort | sed -e 's/[^-][^\/]*\//  |/g' -e 's/|\([^ ]\)/|-- \1/' >> "$OUTPUT_FILE"
    fi
else
    echo "(Folder 'data' nie istnieje)" >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
echo "ZAWARTOŚĆ PLIKÓW PROJEKTU" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 3. Wyszukiwanie i eksport zawartości plików
# Wykluczamy: katalogi środowisk wirtualnych, cache, .git, folder data (tylko struktura powyżej)
find . \
    -path "./.git" -prune -o \
    -path "./.venv*" -prune -o \
    -path "./.mypy_cache" -prune -o \
    -path "./.ruff_cache" -prune -o \
    -path "./.pytest_cache" -prune -o \
    -path "./__pycache__" -prune -o \
    -path "./.vscode" -prune -o \
    -path "./.idea" -prune -o \
    -path "./data" -prune -o \
    -type f \
    \( \
        -name "*.py" -o \
        -name "*.yml" -o \
        -name "*.yaml" -o \
        -name ".env.example" -o \
        -name ".gitignore" \
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
