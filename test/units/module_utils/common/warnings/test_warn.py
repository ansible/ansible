# -*- coding: utf-8 -*-
# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common import warnings

from ansible.module_utils.common.warnings import warn, get_warning_messages


@pytest.fixture
def warning_messages():
    return [
        'First warning',
        'Second warning',
        'Third warning',
    ]


def test_warn():
    warn('Warning message')
    assert warnings._global_warnings == ['Warning message']


def test_multiple_warnings(warning_messages):
    for w in warning_messages:
        warn(w)

    assert warning_messages == warnings._global_warnings


def test_get_warning_messages(warning_messages):
    for w in warning_messages:
        warn(w)

    accessor_warnings = get_warning_messages()
    assert isinstance(accessor_warnings, tuple)
    assert len(accessor_warnings) == 3


@pytest.mark.parametrize(
    'test_case',
    (
        1,
        True,
        [1],
        {'k1': 'v1'},
        (1, 2),
        6.62607004,
        b'bytestr',
        None,
    )
)
def test_warn_failure(test_case):
    with pytest.raises(TypeError, match='warn requires a string not a %s' % type(test_case)):
        warn(test_case)
