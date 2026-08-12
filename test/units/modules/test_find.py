# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import os
import stat

import pytest

from ansible.modules.find import mode_filter


class FakeStat:
    """Stands in for the result of os.lstat, which mode_filter only reads st_mode from."""

    def __init__(self, mode: int) -> None:
        self.st_mode = stat.S_IFREG | mode


@pytest.mark.parametrize(
    'file_mode, wanted, expected',
    (
        # an exact match compares the full permission set
        (0o644, '0644', True),
        (0o644, '0645', False),
        (0o700, '0700', True),
        (0o600, '0700', False),
    )
)
def test_mode_filter_exact(file_mode, wanted, expected):
    assert mode_filter(FakeStat(file_mode), wanted, True, None) is expected


@pytest.mark.parametrize(
    'file_mode, wanted, expected',
    (
        # a single-bit mask matches whenever that bit is present
        (0o400, '0400', True),
        (0o444, '0400', True),
        (0o644, '0400', True),
        (0o200, '0400', False),
        (0o444, '0004', True),
        (0o440, '0004', False),
        # a multi-bit mask is a *minimum* set: every requested bit must be present
        (0o700, '0700', True),
        (0o750, '0700', True),
        (0o400, '0700', False),
        (0o600, '0700', False),
        (0o644, '0700', False),
        (0o666, '0606', True),
        (0o644, '0606', False),
        (0o777, '0644', True),
        (0o444, '0644', False),
    )
)
def test_mode_filter_minimum_set(file_mode, wanted, expected):
    """With exact_mode=false the mode is a minimum set of permissions, not a set of alternatives."""
    assert mode_filter(FakeStat(file_mode), wanted, False, None) is expected


def test_mode_filter_no_mode():
    assert mode_filter(FakeStat(0o644), None, True, None) is True
    assert mode_filter(FakeStat(0o644), '', False, None) is True


def test_mode_filter_ignores_file_type_bits():
    """Only the permission bits participate in the comparison."""
    st = FakeStat(0o644)
    assert st.st_mode & stat.S_IFREG
    assert mode_filter(st, '0644', True, None) is True


@pytest.mark.parametrize('file_mode, wanted, expected', ((0o700, 'u=rwx', True), (0o600, 'u=rwx', False)))
def test_mode_filter_symbolic(file_mode, wanted, expected, set_module_args):
    """A symbolic mode is resolved to octal before the comparison."""
    set_module_args({'paths': [os.sep]})

    from ansible.module_utils.basic import AnsibleModule

    module = AnsibleModule(argument_spec={'paths': {'type': 'list', 'required': True, 'elements': 'path'}})

    assert mode_filter(FakeStat(file_mode), wanted, False, module) is expected
