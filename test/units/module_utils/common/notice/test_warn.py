# -*- coding: utf-8 -*-
# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

import ansible.module_utils.common.notice as notice

from ansible.module_utils.common.notice import warn
from ansible.module_utils.six import PY3


def test_debug():
    warn('Warning message')
    assert notice.global_warnings == ['Warning message']


def test_multiple_notices():
    warning_messages = [
        'First warning',
        'Second warning',
        'Third warning',
    ]
    for w in warning_messages:
        warn(w)

    assert warning_messages == notice.global_warnings


@pytest.mark.parametrize(
    'test_case',
    (
        1,
        True,
        [1],
        {'k1': 'v1'},
        (1, 2),
        6.62607004,
        b'bytestr' if PY3 else None,
        None,
    )
)
def test_warn_failure(test_case):
    with pytest.raises(TypeError, match='warn requires a string not a %s' % type(test_case)):
        warn(test_case)
