# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import pytest

from ansible.module_utils import _internal
from ansible.module_utils.common.text.converters import jsonify


@pytest.mark.parametrize(
    'test_input,expected',
    [
        (1, '1'),
        ('string', '"string"'),
        ('くらとみ', '"\\u304f\\u3089\\u3068\\u307f"'),
        ('café', '"caf\\u00e9"'),
        pytest.param(b'string', '"string"', marks=pytest.mark.skipif(_internal.is_controller, reason="bytes not supported by controller")),
        (False, 'false'),
        pytest.param('string'.encode('utf-8'), '"string"', marks=pytest.mark.skipif(_internal.is_controller, reason="bytes not supported by controller")),
    ]
)
def test_jsonify(test_input, expected):
    """Test for jsonify()."""
    assert jsonify(test_input) == expected
