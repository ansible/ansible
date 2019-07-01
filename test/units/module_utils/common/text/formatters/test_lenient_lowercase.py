# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common.text.formatters import lenient_lowercase


INPUT_LIST = [
    u'HELLO',
    u'Ёлка',
    u'cafÉ',
    b'HELLO',
    1,
    {1: 'Dict'},
    True,
    [1],
]

LOWERED_LIST = [
    u'hello',
    u'ёлка',
    u'café',
    b'hello',
    1,
    {1: 'Dict'},
    True,
    [1],
]


def test_lenient_lowercase():
    """Test of lenient_lowercase function"""
    output_list = lenient_lowercase(INPUT_LIST)
    for out_elem, exp_elem in zip(output_list, LOWERED_LIST):
        assert out_elem == exp_elem


if __name__ == '__main__':
    test_lenient_lowercase()
