# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common.text.formatters import lenient_lowercase


INPUT_LIST = [
    u'HELLO',
    u'Ёлка',
    u'cafÉ',
    u'くらとみ',
    b'HELLO',
    1,
    {1: 'Dict'},
    True,
    [1],
    3.14159,
]

EXPECTED_LIST = [
    u'hello',
    u'ёлка',
    u'café',
    u'くらとみ',
    b'hello',
    1,
    {1: 'Dict'},
    True,
    [1],
    3.14159,
]


def test_lenient_lowercase():
    """Test that lenient_lowercase() proper results."""
    output_list = lenient_lowercase(INPUT_LIST)
    for out_elem, exp_elem in zip(output_list, EXPECTED_LIST):
        assert out_elem == exp_elem
