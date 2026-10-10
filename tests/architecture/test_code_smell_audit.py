"""Testy kontraktowe analizatora zapachow kodu."""

from pathlib import Path

from tests.architecture.audit import discover_python_files
from tests.architecture.code_smell_audit import (
    analyze_source,
    audit_code_smells,
    detect_code_smells,
)


def test_code_smell_audit_scans_all_python_files() -> None:
    project_root = Path(__file__).resolve().parents[2]
    report = audit_code_smells(project_root)

    assert report.files_scanned == len(discover_python_files(project_root))
    assert report.files_scanned > 0


def test_code_smell_audit_detects_representative_smells() -> None:
    source = """
def suspicious(a, b, c, d, e, f, g):
    try:
        if a and b and c and d and e and f:
            for item in c:
                if item:
                    while d:
                        if e:
                            return f
    except Exception:
        return g
"""

    smells = detect_code_smells(source, "fixture.py")
    smell_names = {item.smell for item in smells}

    assert "zbyt_wiele_parametrow" in smell_names
    assert "zlozona_funkcja" in smell_names
    assert "glebokie_zagniezdzenie" in smell_names
    assert "szeroki_wyjatek" in smell_names


def test_code_smell_audit_detects_bare_and_base_exception_handlers() -> None:
    source = """
def broad(value):
    try:
        return value
    except:
        return None

def base(value):
    try:
        return value
    except BaseException:
        return None
"""

    smells = detect_code_smells(source, "fixture.py")

    assert sum(item.smell == "szeroki_wyjatek" for item in smells) == 2


def test_code_smell_audit_does_not_flag_specific_exception() -> None:
    source = """
def safe(value):
    try:
        return value
    except ValueError:
        return None
"""

    smells = detect_code_smells(source, "fixture.py")

    assert not any(item.smell == "szeroki_wyjatek" for item in smells)


def test_code_smell_audit_marks_extreme_metrics_as_blocking() -> None:
    source = "\n".join(["def huge(value):", *[f"    value = {index}" for index in range(170)], "    return value"])

    smells = detect_code_smells(source, "fixture.py")

    assert any(item.smell == "dluga_funkcja" and item.severity == "error" for item in smells)


def test_code_smell_audit_reports_invalid_python_without_stopping() -> None:
    smells = analyze_source("def broken(:\n", "invalid.py")

    assert len(smells) == 1
    assert smells[0].smell == "blad_parsowania"
    assert smells[0].severity == "error"


def test_code_smell_report_contains_recommendations() -> None:
    smells = detect_code_smells("x = 1\n" * 501, "large.py")
    report = audit_code_smells(Path(__file__).resolve().parents[2])
    rendered = report.render_text()

    assert any(item.recommendation for item in smells)
    assert "Zalecenie:" in rendered
