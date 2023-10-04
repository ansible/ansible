# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import pytest

from ansible.module_utils.common.text.converters import jsonify


@pytest.mark.parametrize(
    'test_input,expected',
    [
        (1, '1'),
        (u'string', u'"string"'),
        (u'くらとみ', u'"\\u304f\\u3089\\u3068\\u307f"'),
        (u'café', u'"caf\\u00e9"'),
        (b'string', u'"string"'),
        (False, u'false'),
        (u'string'.encode('utf-8'), u'"string"'),
    ]
)
def test_jsonify(test_input, expected):
    """Test for jsonify()."""
    assert jsonify(test_input) == expected
