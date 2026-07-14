"""Tests for the diff module."""
from __future__ import annotations

import pathlib
import pytest
import typing as t

if t.TYPE_CHECKING:  # pragma: nocover
    # noinspection PyProtectedMember
    from ansible_test._internal.diff import FileDiff


@pytest.fixture()
def diffs(request: pytest.FixtureRequest) -> list[FileDiff]:
    """A fixture which returns the parsed diff associated with the current test."""
    return get_parsed_diff(request.node.name.removeprefix('test_'))


def get_parsed_diff(name: str) -> list[FileDiff]:
    """Parse and return the named git diff."""
    cache = pathlib.Path(__file__).parent / 'diff' / f'{name}.diff'
    content = cache.read_text()
    lines = content.splitlines()

    assert lines

    # noinspection PyProtectedMember
    from ansible_test._internal.diff import parse_diff

    diffs = parse_diff(lines)

    assert diffs

    for item in diffs:
        assert item.headers
        assert item.is_complete

        item.old.format_lines()
        item.new.format_lines()

        for line_range in item.old.ranges:
            assert line_range[1] >= line_range[0] > 0

        for line_range in item.new.ranges:
            assert line_range[1] >= line_range[0] > 0

    return diffs


def test_add_binary_file(diffs: list[FileDiff]) -> None:
    """Add a binary file."""
    assert len(diffs) == 1

    assert diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'binary.dat'
    assert diffs[0].new.path == 'binary.dat'

    assert diffs[0].old.eof_newline
    assert diffs[0].new.eof_newline


def test_add_text_file(diffs: list[FileDiff]) -> None:
    """Add a new file."""
    assert len(diffs) == 1

    assert not diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'test.txt'
    assert diffs[0].new.path == 'test.txt'

    assert diffs[0].old.eof_newline
    assert diffs[0].new.eof_newline


def test_remove_trailing_newline(diffs: list[FileDiff]) -> None:
    """Remove the trailing newline from a file."""
    assert len(diffs) == 1

    assert diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'test.txt'
    assert diffs[0].new.path == 'test.txt'

    assert diffs[0].old.eof_newline
    assert not diffs[0].new.eof_newline


def test_add_trailing_newline(diffs: list[FileDiff]) -> None:
    """Add a trailing newline to a file."""
    assert len(diffs) == 1

    assert diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'test.txt'
    assert diffs[0].new.path == 'test.txt'

    assert not diffs[0].old.eof_newline
    assert diffs[0].new.eof_newline


def test_add_two_text_files(diffs: list[FileDiff]) -> None:
    """Add two text files."""
    assert len(diffs) == 2

    assert not diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'one.txt'
    assert diffs[0].new.path == 'one.txt'

    assert diffs[0].old.eof_newline
    assert diffs[0].new.eof_newline

    assert not diffs[1].old.exists
    assert diffs[1].new.exists

    assert diffs[1].old.path == 'two.txt'
    assert diffs[1].new.path == 'two.txt'

    assert diffs[1].old.eof_newline
    assert diffs[1].new.eof_newline


def test_context_no_trailing_newline(diffs: list[FileDiff]) -> None:
    """Context without a trailing newline."""
    assert len(diffs) == 1

    assert diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'test.txt'
    assert diffs[0].new.path == 'test.txt'

    assert not diffs[0].old.eof_newline
    assert not diffs[0].new.eof_newline


def test_multiple_context_lines(diffs: list[FileDiff]) -> None:
    """Multiple context lines."""
    assert len(diffs) == 1

    assert diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'test.txt'
    assert diffs[0].new.path == 'test.txt'

    assert diffs[0].old.eof_newline
    assert diffs[0].new.eof_newline


def test_parse_delete(diffs: list[FileDiff]) -> None:
    """Delete files."""
    assert len(diffs) == 1

    assert diffs[0].old.exists
    assert not diffs[0].new.exists

    assert diffs[0].old.path == 'changelogs/fragments/79263-runme-sh-logging-3cb482385bd59058.yaml'
    assert diffs[0].new.path == 'changelogs/fragments/79263-runme-sh-logging-3cb482385bd59058.yaml'


def test_parse_rename(diffs) -> None:
    """Rename files."""
    assert len(diffs) == 2

    assert all(item.old.path != item.new.path and item.old.exists and item.new.exists for item in diffs)

    assert diffs[0].old.path == 'packaging/debian/ansible-base.dirs'
    assert diffs[0].new.path == 'packaging/debian/ansible-core.dirs'

    assert diffs[1].old.path == 'packaging/debian/ansible-base.install'
    assert diffs[1].new.path == 'packaging/debian/ansible-core.install'
