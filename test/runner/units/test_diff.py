"""Tests for diff module."""
import os
import subprocess
import pytest

from lib.diff import (
    parse_diff,
    FileDiff,
)


def get_diff(base, head=None):
    """Return a git diff between the base and head revision.
    :type base: str
    :type head: str | None
    :rtype: list[str]
    """
    if not head or head == 'HEAD':
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()

    cache = '/tmp/git-diff-cache-%s-%s.log' % (base, head)

    if os.path.exists(cache):
        with open(cache, 'r') as cache_fd:
            lines = cache_fd.read().splitlines()
    else:
        lines = subprocess.check_output(['git', 'diff', base, head]).splitlines()

        with open(cache, 'w') as cache_fd:
            cache_fd.write('\n'.join(lines))

    assert lines

    return lines


def get_parsed_diff(base, head=None):
    """Return a parsed git diff between the base and head revision.
    :type base: str
    :type head: str | None
    :rtype: list[FileDiff]
    """
    lines = get_diff(base, head)
    items = parse_diff(lines)

    assert items

    for item in items:
        assert item.headers
        assert item.is_complete

        item.old.format_lines()
        item.new.format_lines()

        for line_range in item.old.ranges:
            assert line_range[1] >= line_range[0] > 0

        for line_range in item.new.ranges:
            assert line_range[1] >= line_range[0] > 0

    return items


RANGES_TO_TEST = (
    ('f31421576b00f0b167cdbe61217c31c21a41ac02', 'HEAD'),
    ('b8125ac1a61f2c7d1de821c78c884560071895f1', '32146acf4e43e6f95f54d9179bf01f0df9814217')
)


@pytest.mark.parametrize("base, head", RANGES_TO_TEST)
def test_parse_diff(base, head):
    """Integration test to verify parsing of ansible/ansible history."""
    get_parsed_diff(base, head)


def test_parse_delete():
    """Integration test to verify parsing of a deleted file."""
    commit = 'ee17b914554861470b382e9e80a8e934063e0860'
    items = get_parsed_diff(commit + '~', commit)
    deletes = [item for item in items if not item.new.exists]

    assert len(deletes) == 1
    assert deletes[0].old.path == 'lib/ansible/plugins/connection/nspawn.py'
    assert deletes[0].new.path == 'lib/ansible/plugins/connection/nspawn.py'


def test_parse_rename():
    """Integration test to verify parsing of renamed files."""
    commit = '16a39639f568f4dd5cb233df2d0631bdab3a05e9'
    items = get_parsed_diff(commit + '~', commit)
    renames = [item for item in items if item.old.path != item.new.path and item.old.exists and item.new.exists]

    assert len(renames) == 2
    assert renames[0].old.path == 'test/integration/targets/eos_eapi/tests/cli/badtransport.yaml'
    assert renames[0].new.path == 'test/integration/targets/eos_eapi/tests/cli/badtransport.1'
    assert renames[1].old.path == 'test/integration/targets/eos_eapi/tests/cli/zzz_reset.yaml'
    assert renames[1].new.path == 'test/integration/targets/eos_eapi/tests/cli/zzz_reset.1'
