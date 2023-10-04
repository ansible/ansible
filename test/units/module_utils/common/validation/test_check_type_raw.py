# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


from ansible.module_utils.common.validation import check_type_raw


def test_check_type_raw():
    test_cases = (
        (1, 1),
        ('1', '1'),
        ('a', 'a'),
        ({'k1': 'v1'}, {'k1': 'v1'}),
        ([1, 2], [1, 2]),
        (b'42', b'42'),
        (u'42', u'42'),
    )
    for case in test_cases:
        assert case[1] == check_type_raw(case[0])
