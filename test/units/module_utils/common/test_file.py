# -*- coding: utf-8 -*-
# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.common.file import FILE_ATTRIBUTES, format_attributes, _sort_attr_flags

import pytest


# flags as lsattr reports them, expected ordering
SORT_CASES = [
    ('', ''),
    ('A', 'A'),
    ('Ad', 'dA'),      # lsattr prints nodump ahead of noatime
    ('dA', 'dA'),
    ('eIA', 'AIe'),
    ('AdeC', 'dAeC'),
    ('QA', 'AQ'),      # flags missing from the table sort after the known ones
    ('zQ', 'Qz'),
]


@pytest.mark.parametrize('flags, expected', SORT_CASES)
def test_sort_attr_flags(flags, expected):
    assert _sort_attr_flags(flags) == expected


def test_file_attributes_is_in_lsattr_order():
    # _sort_attr_flags depends on the dict preserving this order
    assert ''.join(FILE_ATTRIBUTES) == 'suSDiadAcEjItTeCxFNPVmhXZ'


@pytest.mark.parametrize('flag, name', [
    ('x', 'dax'),
    ('F', 'casefold'),
    ('P', 'projinherit'),
    ('V', 'verity'),
    ('m', 'nocompress'),
])
def test_newly_recognized_attributes_are_named(flag, name):
    assert format_attributes(flag) == [name]
