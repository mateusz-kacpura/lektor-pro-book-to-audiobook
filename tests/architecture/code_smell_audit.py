"""Statyczne wykrywanie wybranych smell code w projekcie."""

from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from tests.architecture.audit import discover_python_files

SmellSeverity = Literal["warning", "error"]
SmellKind = Literal[
    "duzy_plik",
    "dluga_funkcja",
    "zbyt_wiele_parametrow",
    "zlozona_funkcja",
    "glebokie_zagniezdzenie",
    "szeroki_wyjatek",
    "blad_parsowania",
]


@dataclass(frozen=True)
class MetricRule:
    """Konfiguracja pojedynczej metryki i jej poziomow alarmowych."""

    kind: SmellKind
    warning_limit: int
    error_limit: int
    recommendation: str


METRIC_RULES: dict[SmellKind, MetricRule] = {
    "duzy_plik": MetricRule(
        kind="duzy_plik",
        warning_limit=500,
        error_limit=1000,
        recommendation="Podziel odpowiedzialnosci na mniejsze moduly.",
    ),
    "dluga_funkcja": MetricRule(
        kind="dluga_funkcja",
        warning_limit=80,
        error_limit=160,
        recommendation="Wydziel mniejsze kroki o jednej odpowiedzialnosci.",
    ),
    "zbyt_wiele_parametrow": MetricRule(
        kind="zbyt_wiele_parametrow",
        warning_limit=6,
        error_limit=12,
        recommendation="Przekaz obiekt danych lub rozdziel odpowiedzialnosci.",
    ),
    "zlozona_funkcja": MetricRule(
        kind="zlozona_funkcja",
        warning_limit=10,
        error_limit=25,
        recommendation="Podziel logike warunkowa na mniejsze funkcje lub strategie.",
    ),
    "glebokie_zagniezdzenie": MetricRule(
        kind="glebokie_zagniezdzenie",
        warning_limit=4,
        error_limit=8,
        recommendation="Uzyj wczesnych powrotow albo wydziel osobne funkcje.",
    ),
}


@dataclass(frozen=True)
class CodeSmell:
    """Pojedyncze znalezisko wraz z metryka i zaleceniem."""

    smell: SmellKind
    severity: SmellSeverity
    path: str
    line: int
    symbol: str
    metric: int
    threshold: int
    message: str
    recommendation: str

    def as_dict(self) -> dict[str, int | str]:
        """Zwraca rekord gotowy do zapisania w raporcie JSON."""

        return asdict(self)


@dataclass(frozen=True)
class CodeSmellReport:
    """Raport wynikow skanowania kodu Python."""

    files_scanned: int
    smells: tuple[CodeSmell, ...]

    @property
    def warnings(self) -> tuple[CodeSmell, ...]:
        return tuple(item for item in self.smells if item.severity == "warning")

    @property
    def blocking_smells(self) -> tuple[CodeSmell, ...]:
        return tuple(item for item in self.smells if item.severity == "error")

    def as_dict(self) -> dict[str, object]:
        """Zwraca caly raport w formacie serializowalnym do JSON."""

        return {
            "files_scanned": self.files_scanned,
            "warnings": len(self.warnings),
            "blocking_smells": len(self.blocking_smells),
            "smells": [item.as_dict() for item in self.smells],
        }

    def render_text(self) -> str:
        """Buduje podsumowanie dla terminala."""

        lines = [
            "Raport zapachow kodu",
            f"Pliki przeskanowane: {self.files_scanned}",
            f"Ostrzezenia: {len(self.warnings)}",
            f"Naruszenia blokujace: {len(self.blocking_smells)}",
        ]
        for item in self.smells:
            lines.append(
                f"[{item.severity.upper()}] {item.path}:{item.line} "
                f"{item.symbol} - {item.message} Zalecenie: {item.recommendation}"
            )
        return "\n".join(lines)


_CONTROL_FLOW_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.With,
    ast.AsyncWith,
    ast.Match,
)


class _FunctionMetrics(ast.NodeVisitor):
    """Liczy zlozonosc i najglebsze zagniezdzenie w jednym przejsciu AST."""

    def __init__(self) -> None:
        self.complexity = 1
        self._nesting_depth = 0
        self.max_nesting = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        del node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        del node

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        del node

    def visit_If(self, node: ast.If) -> None:
        self._visit_control_node(node)

    def visit_For(self, node: ast.For) -> None:
        self._visit_control_node(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_control_node(node)

    def visit_While(self, node: ast.While) -> None:
        self._visit_control_node(node)

    def visit_Try(self, node: ast.Try) -> None:
        self._visit_control_node(node)

    def visit_With(self, node: ast.With) -> None:
        self._visit_control_node(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._visit_control_node(node)

    def visit_Match(self, node: ast.Match) -> None:
        self._visit_control_node(node)
        self.complexity += max(0, len(node.cases) - 1)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self.complexity += 1 + len(node.ifs)
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.complexity += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def _visit_control_node(self, node: ast.AST) -> None:
        self.complexity += 1
        self._nesting_depth += 1
        self.max_nesting = max(self.max_nesting, self._nesting_depth)
        self.generic_visit(node)
        self._nesting_depth -= 1


class _SmellVisitor(ast.NodeVisitor):
    """AST visitor wykrywajacy zapachy kodu w jednym module."""

    def __init__(self, path: str, source: str) -> None:
        self.path = path
        self.source_lines = len(source.splitlines())
        self.smells: list[CodeSmell] = []

    def visit_Module(self, node: ast.Module) -> None:
        self._add_metric(
            kind="duzy_plik",
            line=1,
            symbol="<modul>",
            metric=self.source_lines,
            message=f"Modul ma {self.source_lines} wierszy.",
        )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if self._handles_broad_exception(node.type):
            self.smells.append(
                CodeSmell(
                    smell="szeroki_wyjatek",
                    severity="warning",
                    path=self.path,
                    line=node.lineno,
                    symbol="except",
                    metric=1,
                    threshold=0,
                    message="Obsluga szerokiego wyjatku utrudnia diagnozowanie bledow.",
                    recommendation="Lap konkretny wyjatek i obsluz go jawnie.",
                )
            )
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        metrics = _FunctionMetrics()
        for statement in node.body:
            metrics.visit(statement)

        function_name = node.name
        line_count = (node.end_lineno or node.lineno) - node.lineno + 1
        parameter_count = self._parameter_count(node)
        self._add_metric(
            kind="dluga_funkcja",
            line=node.lineno,
            symbol=function_name,
            metric=line_count,
            message=f"Funkcja ma {line_count} wierszy.",
        )
        self._add_metric(
            kind="zbyt_wiele_parametrow",
            line=node.lineno,
            symbol=function_name,
            metric=parameter_count,
            message=f"Funkcja ma {parameter_count} parametrow.",
        )
        self._add_metric(
            kind="zlozona_funkcja",
            line=node.lineno,
            symbol=function_name,
            metric=metrics.complexity,
            message=f"Zlozonosc cyklomatyczna wynosi co najmniej {metrics.complexity}.",
        )
        self._add_metric(
            kind="glebokie_zagniezdzenie",
            line=node.lineno,
            symbol=function_name,
            metric=metrics.max_nesting,
            message=f"Najglebsze zagniezdzenie wynosi {metrics.max_nesting} poziomow.",
        )

    def _add_metric(
        self,
        *,
        kind: SmellKind,
        line: int,
        symbol: str,
        metric: int,
        message: str,
    ) -> None:
        rule = METRIC_RULES[kind]
        severity = self._severity(rule, metric)
        if severity is None:
            return
        self.smells.append(
            CodeSmell(
                smell=kind,
                severity=severity,
                path=self.path,
                line=line,
                symbol=symbol,
                metric=metric,
                threshold=rule.warning_limit,
                message=message,
                recommendation=rule.recommendation,
            )
        )

    @staticmethod
    def _severity(rule: MetricRule, metric: int) -> SmellSeverity | None:
        if metric > rule.error_limit:
            return "error"
        if metric > rule.warning_limit:
            return "warning"
        return None

    @staticmethod
    def _parameter_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        arguments = node.args
        return (
            len(arguments.posonlyargs)
            + len(arguments.args)
            + len(arguments.kwonlyargs)
            + int(arguments.vararg is not None)
            + int(arguments.kwarg is not None)
        )

    @staticmethod
    def _handles_broad_exception(node: ast.expr | None) -> bool:
        if node is None:
            return True
        if isinstance(node, ast.Name):
            return node.id in {"Exception", "BaseException"}
        if isinstance(node, ast.Tuple):
            return any(_SmellVisitor._handles_broad_exception(item) for item in node.elts)
        return False


def detect_code_smells(source: str, relative_path: str) -> tuple[CodeSmell, ...]:
    """Analizuje kod zrodlowy bez dostepu do systemu plikow."""

    tree = ast.parse(source, filename=relative_path)
    visitor = _SmellVisitor(relative_path, source)
    visitor.visit(tree)
    return tuple(visitor.smells)


def _parse_failure(path: str, error: OSError | UnicodeError | SyntaxError) -> CodeSmell:
    line = error.lineno if isinstance(error, SyntaxError) and error.lineno else 1
    return CodeSmell(
        smell="blad_parsowania",
        severity="error",
        path=path,
        line=line,
        symbol="<modul>",
        metric=1,
        threshold=0,
        message=f"Nie mozna przeanalizowac pliku: {error}",
        recommendation="Napraw kodowanie, dostep do pliku albo skladnie modulu.",
    )


def analyze_source(source: str, relative_path: str) -> tuple[CodeSmell, ...]:
    """Analizuje tekst zrodlowy i zamienia blad skladni na znalezisko."""

    try:
        return detect_code_smells(source, relative_path)
    except SyntaxError as error:
        return (_parse_failure(relative_path, error),)


def audit_code_smells(project_root: Path) -> CodeSmellReport:
    """Skanuje wszystkie pliki Python i kontynuuje po bledach pojedynczych plikow."""

    smells: list[CodeSmell] = []
    python_files = discover_python_files(project_root)
    for path in python_files:
        relative_path = path.relative_to(project_root).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            smells.append(_parse_failure(relative_path, error))
        else:
            smells.extend(analyze_source(source, relative_path))
    return CodeSmellReport(
        files_scanned=len(python_files),
        smells=tuple(sorted(smells, key=lambda item: (item.path, item.line, item.smell))),
    )


def write_report(report: CodeSmellReport, output_path: Path) -> None:
    """Zapisuje raport bez uzalezniania analizatora od konkretnego katalogu."""

    output_path.write_text(
        json.dumps(report.as_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    """Uruchamia audyt i zapisuje raport JSON w katalogu projektu."""

    project_root = Path(__file__).resolve().parents[2]
    report = audit_code_smells(project_root)
    write_report(report, project_root / "code_smell_report.json")
    print(report.render_text())
    return int(bool(report.blocking_smells))


if __name__ == "__main__":
    raise SystemExit(main())
