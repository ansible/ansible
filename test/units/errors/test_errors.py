from __future__ import annotations

import pathlib

import pytest

from ansible.errors import AnsibleError, AnsibleVariableTypeError
from ansible.errors.utils import SourceContext
from ansible.utils.datatag.tags import AnsibleSourcePosition

from ..test_utils.controller.display import emits_deprecation_warning


@pytest.mark.parametrize("filename, line, col, expected_filename", (
    ('nonexistent_file.txt', 3, 4, "nonexistent.txt"),
    ('short_file.txt', None, None, "short_file_no_line.txt"),
    ('short_file.txt', 324762384, 3, "short_file_overflowed_line.txt"),
    ('short_file.txt', 3, 324762384, "short_file_overflowed_col.txt"),
    ('short_file.txt', -1, 3, "short_file_underflowed_line.txt"),
    ('short_file.txt', 3, -1, "short_file_underflowed_col.txt"),
    ('short_file.txt', 2, None, "short_file_no_column.txt"),
    ('empty_file.txt', 2, 1, "empty_file_unavailable.txt"),
    ('short_file.txt', 1, 1, "short_file_no_context_left_marker.txt"),
    ('short_file.txt', 5, 1, "short_file_left_marker.txt"),
    ('short_file_missing_trailing_newline.txt', 7, 1, "short_file_missing_trailing_newline_left_marker.txt"),
    ('short_file.txt', 7, 118, "short_file_last_column_right_marker.txt"),
    ('short_file.txt', 4, 118, "short_file_truncated_target.txt"),
    ('short_file.txt', 4, 115, "short_file_truncated_target_last_displayed_char.txt"),
    ('short_file.txt', 4, 174, "short_file_long_line_truncated_past_target.txt"),
    ('long_file.txt', 14, 117, "long_file_last_column_right_marker.txt"),
    ('file_with_tabs.txt', 3, 22, "file_with_tabs_replaced_left_marker.txt"),
))
def test_source_context(filename: str, line: int | None, col: int | None, expected_filename: str) -> None:
    # set this to true to regenerate and overwrite the expected test output files
    overwrite_expected = False

    fixture_path = pathlib.Path(__file__).parent / 'fixtures'

    pos = AnsibleSourcePosition(src=str(fixture_path / 'inputs' / filename), line=line, col=col)

    # DTFIX-FUTURE: assert target_line contents as well?
    source_context = SourceContext.from_source_position(pos)
    result = '\n'.join(source_context.annotated_source_lines) + '\n'

    expected_path = fixture_path / 'outputs' / expected_filename

    if overwrite_expected:  # pragma: nocover
        expected_path.write_text(result)

    assert result == expected_path.read_text()
    assert not overwrite_expected


def test_suppress_extended_error_deprecation() -> None:
    with emits_deprecation_warning(match='suppress_extended_error.*argument'):
        AnsibleError(suppress_extended_error=True)  # pylint: disable=pointless-exception-statement


@pytest.mark.parametrize("obj, expected", (
    (1, f'Variables of type {int.__name__!r} are not supported.'),
    (int, f'Variables of type {type.__name__!r} are not supported.'),
))
def test_ansible_variable_type_error(obj: object, expected: str) -> None:
    assert str(AnsibleVariableTypeError(obj=obj)) == expected
