# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from datetime import datetime

from pytz import timezone as tz

from ansible.module_utils.common.text.converters import _json_encode_fallback


@pytest.mark.parametrize(
    'test_input,expected',
    [
        (set([1]), [1]),
        (datetime(2019, 5, 14, 13, 39, 38, 569047), '2019-05-14T13:39:38.569047'),
        (datetime(2019, 5, 14, 13, 47, 16, 923866), '2019-05-14T13:47:16.923866'),
        (datetime(2019, 6, 15, 14, 45, tzinfo=tz('UTC')), '2019-06-15T14:45:00+00:00'),
        (datetime(2019, 6, 15, 14, 45, tzinfo=tz('Europe/Helsinki')), '2019-06-15T14:45:00+01:40'),
    ]
)
def test_json_encode_fallback(test_input, expected):
    """
    Test for passing expected objects to _json_encode_fallback().
    """
    assert _json_encode_fallback(test_input) == expected


@pytest.mark.parametrize(
    'test_input',
    [
        1,
        1.1,
        u'string',
        b'string',
        [1, 2],
        True,
        None,
        {1: 1},
        (1, 2),
    ]
)
def test_json_encode_fallback_default_behavior(test_input):
    """
    Test for _json_encode_fallback() default behavior.

    It must fail with TypeError.
    """
    with pytest.raises(TypeError, match='Cannot json serialize'):
        _json_encode_fallback(test_input)
