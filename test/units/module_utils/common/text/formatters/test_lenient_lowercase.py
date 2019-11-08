# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from datetime import datetime

import pytest

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

result_list = lenient_lowercase(INPUT_LIST)


@pytest.mark.parametrize(
    'input_value,expected_outcome',
    [
        (result_list[0], EXPECTED_LIST[0]),
        (result_list[1], EXPECTED_LIST[1]),
        (result_list[2], EXPECTED_LIST[2]),
        (result_list[3], EXPECTED_LIST[3]),
        (result_list[4], EXPECTED_LIST[4]),
        (result_list[5], EXPECTED_LIST[5]),
        (result_list[6], EXPECTED_LIST[6]),
        (result_list[7], EXPECTED_LIST[7]),
        (result_list[8], EXPECTED_LIST[8]),
        (result_list[9], EXPECTED_LIST[9]),
    ]
)
def test_lenient_lowercase(input_value, expected_outcome):
    """Test that lenient_lowercase() proper results."""
    assert input_value == expected_outcome


@pytest.mark.parametrize('input_data', [1, False, 1.001, 1j, datetime.now(), ])
def test_lenient_lowercase_illegal_data_type(input_data):
    """Test passing objects of illegal types to lenient_lowercase()."""
    with pytest.raises(TypeError, match='object is not iterable'):
        lenient_lowercase(input_data)
