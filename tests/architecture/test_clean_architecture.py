"""Test egzekwujący reguły Czystej Architektury z GEMINI.md."""

from pathlib import Path

from tests.architecture.audit import audit_project, discover_python_files


def test_clean_architecture_dependencies() -> None:
    """Raportuje i blokuje naruszenia separacji warstw oraz ścisłego typowania."""
    project_root = Path(__file__).resolve().parents[2]
    report = audit_project(project_root)
    print(report.render_text())
    assert report.files_scanned == len(discover_python_files(project_root))
    assert report.files_scanned >= 143
    assert not report.violations, report.render_text()
