"""Testy wydzielonych translatorow kodu Go."""

from lektor.domain.normalizers.go_code_reader import GoCodeReader


def test_explain_code_block_handles_interface_without_line_parser() -> None:
    result = GoCodeReader.explain_code_block(
        """
type Reader interface {
    Read(p []byte) (n int, err error)
}
"""
    )

    assert "interfejsu Reader" in result
    assert "Read(p []byte)" in result


def test_explain_code_block_handles_struct_with_named_fields() -> None:
    result = GoCodeReader.explain_code_block(
        """
type Person struct {
    Name string
    Age int
}
"""
    )

    assert "struktury Person" in result
    assert "pole Name" in result
    assert "pole Age" in result


def test_explain_code_block_handles_sequential_statements() -> None:
    result = GoCodeReader.explain_code_block(
        """
select {
case value := <-input:
    return value
}
"""
    )

    assert "Instrukcja wyboru select" in result
    assert "Początek fragmentu kodu" in result
