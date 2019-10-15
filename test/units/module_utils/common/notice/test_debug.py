# -*- coding: utf-8 -*-
# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

import ansible.module_utils.common.notice as notice

from ansible.module_utils.common.notice import debug
from ansible.module_utils.six import PY3


def test_debug():
    debug('Debug message')
    assert notice.global_debugs == ['Debug message']


def test_multiple_debug_messages():
    debug_messages = [
        'First warning',
        'Second warning',
        'Third warning',
    ]
    for w in debug_messages:
        debug(w)

    assert debug_messages == notice.global_debugs


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
def test_debug_failure(test_case):
    with pytest.raises(TypeError, match='debug requires a string not a %s' % type(test_case)):
        debug(test_case)
