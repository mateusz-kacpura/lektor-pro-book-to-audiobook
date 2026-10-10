"""Statyczny audyt zależności zgodny z zasadami Czystej Architektury."""

from __future__ import annotations

import ast
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Final

LAYER_ORDER: Final[dict[str, int]] = {
    "domain": 0,
    "application": 1,
    "adapters": 2,
    "infrastructure": 3,
}
FORBIDDEN_DOMAIN_IMPORTS: Final[frozenset[str]] = frozenset(
    {"fastapi", "httpx", "numpy", "pydantic", "torch", "fitz", "soundfile", "transformers"}
)
FORBIDDEN_APPLICATION_IMPORTS: Final[frozenset[str]] = frozenset(
    {"fastapi", "httpx", "numpy", "pydantic", "torch", "fitz", "soundfile", "transformers"}
)



EXCLUDED_DIRECTORY_NAMES: Final[frozenset[str]] = frozenset(
    {".git", ".venv-cuda", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".test-tmp"}
)


@dataclass(frozen=True)
class ArchitectureViolation:
    """Pojedyncze naruszenie reguły architektonicznej."""

    rule: str
    path: str
    line: int
    symbol: str
    message: str

    def as_dict(self) -> dict[str, str | int]:
        return {
            "rule": self.rule,
            "path": self.path,
            "line": self.line,
            "symbol": self.symbol,
            "message": self.message,
        }


@dataclass(frozen=True)
class ArchitectureAuditReport:
    """Wynik audytu wraz z metrykami separowalności logiki."""

    files_scanned: int
    layer_files: dict[str, int]
    local_edges: int
    allowed_local_edges: int
    violations: tuple[ArchitectureViolation, ...]

    @property
    def separability_score(self) -> float:
        """Wskaźnik kierunku zależności, a nie ogólna miara jakości kodu."""
        if self.local_edges == 0:
            return 100.0
        return round(self.allowed_local_edges / self.local_edges * 100, 2)

    def as_dict(self) -> dict[str, object]:
        return {
            "files_scanned": self.files_scanned,
            "layer_files": self.layer_files,
            "local_edges": self.local_edges,
            "allowed_local_edges": self.allowed_local_edges,
            "separability_score_percent": self.separability_score,
            "violations": [item.as_dict() for item in self.violations],
        }

    def render_text(self) -> str:
        lines = [
            "RAPORT AUDYTU CZYSTEJ ARCHITEKTURY",
            f"Pliki przeskanowane: {self.files_scanned}",
            f"Zależności wewnętrzne: {self.local_edges}",
            f"Zależności zgodne z kierunkiem: {self.allowed_local_edges}",
            f"Separowalność kierunku zależności: {self.separability_score:.2f}%",
            f"Naruszenia: {len(self.violations)}",
        ]
        if self.layer_files:
            lines.append("Pliki według warstw: " + ", ".join(
                f"{layer}={count}" for layer, count in sorted(self.layer_files.items())
            ))
        if self.violations:
            lines.append("Szczegóły:")
            lines.extend(
                f"- [{item.rule}] {item.path}:{item.line} {item.symbol}: {item.message}"
                for item in self.violations
            )
        else:
            lines.append("Wynik: brak naruszeń.")
        return "\n".join(lines)


def _module_name(path: Path, project_root: Path) -> str:
    relative = path.relative_to(project_root).with_suffix("")
    return ".".join(relative.parts)


def _layer(module_name: str) -> str | None:
    parts = module_name.split(".")
    return parts[1] if len(parts) > 1 and parts[1] in LAYER_ORDER else None


def _resolve_import(module_name: str, imported: ast.ImportFrom) -> str:
    current_parts = module_name.split(".")
    package_parts = current_parts[:-1]
    if imported.level:
        base_parts = package_parts[: len(package_parts) - imported.level + 1]
        if imported.module:
            base_parts.extend(imported.module.split("."))
        return ".".join(base_parts)
    return imported.module or ""


def _import_root(module_name: str) -> str:
    return module_name.split(".", maxsplit=1)[0]



def discover_python_files(project_root: Path) -> list[Path]:
    """Zwraca wszystkie pliki Python projektu poza srodowiskami i cache."""
    return sorted(
        path
        for path in project_root.rglob("*.py")
        if not any(part in EXCLUDED_DIRECTORY_NAMES for part in path.relative_to(project_root).parts)
    )


class _AstCollector(ast.NodeVisitor):
    def __init__(self, module_name: str) -> None:
        self._module_name = module_name
        self.imports: list[tuple[str, int, str]] = []
        self.any_lines: list[int] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append((alias.name, node.lineno, alias.name))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        imported = _resolve_import(self._module_name, node) if node.level else (node.module or "")
        self.imports.append((imported, node.lineno, imported or "."))
        if any(alias.name == "Any" for alias in node.names):
            self.any_lines.append(node.lineno)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id == "Any":
            self.any_lines.append(node.lineno)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr == "Any":
            self.any_lines.append(node.lineno)
        self.generic_visit(node)


def audit_project(project_root: Path) -> ArchitectureAuditReport:
    """Skanuje wszystkie pliki Python projektu i tworzy raport audytu."""
    violations: list[ArchitectureViolation] = []
    layer_files: Counter[str] = Counter()
    local_edges = 0
    allowed_local_edges = 0
    files = discover_python_files(project_root)

    for path in files:
        module_name = _module_name(path, project_root)
        current_layer = _layer(module_name)
        layer_files[current_layer or "unclassified"] += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as error:
            violations.append(ArchitectureViolation(
                "syntax", str(path.relative_to(project_root)), error.lineno or 0,
                module_name, f"Nie można sparsować pliku: {error.msg}",
            ))
            continue

        collector = _AstCollector(module_name)
        collector.visit(tree)
        relative_path = str(path.relative_to(project_root))
        for line in collector.any_lines:
            violations.append(ArchitectureViolation(
                "strict_typing", relative_path, line, module_name,
                "Użycie Any jest zabronione przez GEMINI.md.",
            ))

        for imported_name, line, symbol in collector.imports:
            if current_layer is None:
                continue
            if imported_name.startswith("lektor"):
                target_layer = _layer(imported_name)
                if target_layer is None:
                    continue
                local_edges += 1
                if LAYER_ORDER[target_layer] <= LAYER_ORDER[current_layer]:
                    allowed_local_edges += 1
                else:
                    violations.append(ArchitectureViolation(
                        "dependency_rule", relative_path, line, symbol,
                        f"Warstwa {current_layer} zależy od zewnętrznej warstwy {target_layer}; "
                        "zależności muszą kierować się do wewnątrz.",
                    ))
            else:
                root = _import_root(imported_name)
                forbidden = (
                    current_layer == "domain" and root in FORBIDDEN_DOMAIN_IMPORTS
                ) or (
                    current_layer == "application" and root in FORBIDDEN_APPLICATION_IMPORTS
                )
                if forbidden:
                    violations.append(ArchitectureViolation(
                        "dependency_rule", relative_path, line, symbol,
                        f"Warstwa {current_layer} importuje zewnętrzną zależność {root}; "
                        "logika wewnętrzna powinna zależeć od portu lub abstrakcji.",
                    ))

    violations.sort(key=lambda item: (item.path, item.line, item.rule, item.symbol))
    return ArchitectureAuditReport(
        files_scanned=len(files),
        layer_files=dict(layer_files),
        local_edges=local_edges,
        allowed_local_edges=allowed_local_edges,
        violations=tuple(violations),
    )


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    report = audit_project(project_root)
    print(report.render_text())
    output_path = project_root / "architecture_audit_report.json"
    output_path.write_text(json.dumps(report.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRaport JSON: {output_path}")
    return 0 if not report.violations else 1


if __name__ == "__main__":
    sys.exit(main())
