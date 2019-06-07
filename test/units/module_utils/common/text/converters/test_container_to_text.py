# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.text.converters import container_to_text


DEFAULT_ENCODING = 'utf-8'
DEFAULT_ERR_HANDLER = 'surrogate_or_strict'


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ({1: 1}, {1: 1}),
        ([1, 2], [1, 2]),
        ((1, 2), (1, 2)),
        (1, 1),
        (1.1, 1.1),
        (b'str', u'str'),
        (u'str', u'str'),
        ([b'str'], [u'str']),
        ((b'str'), (u'str')),
        ({b'str': b'str'}, {u'str': u'str'}),
    ]
)
@pytest.mark.parametrize('encoding', ['utf-8', 'latin1', 'shift-jis', 'big5', 'koi8_r', ])
@pytest.mark.parametrize('errors', ['strict', 'surrogate_or_strict', 'surrogate_then_replace', ])
def test_container_to_text_different_types(test_input, expected, encoding, errors):
    """Test for passing objects to container_to_text()."""
    assert container_to_text(test_input, encoding=encoding, errors=errors) == expected


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ({1: 1}, {1: 1}),
        ([1, 2], [1, 2]),
        ((1, 2), (1, 2)),
        (1, 1),
        (1.1, 1.1),
        (True, True),
        (None, None),
        (u'str', u'str'),
        (u'くらとみ'.encode(DEFAULT_ENCODING), u'くらとみ'),
        (u'café'.encode(DEFAULT_ENCODING), u'café'),
        (u'str'.encode(DEFAULT_ENCODING), u'str'),
        ([u'str'.encode(DEFAULT_ENCODING)], [u'str']),
        ((u'str'.encode(DEFAULT_ENCODING)), (u'str')),
        ({b'str': b'str'}, {u'str': u'str'}),
    ]
)
def test_container_to_text_default_encoding_and_err(test_input, expected):
    """
    Test for passing objects to container_to_text(). Default encoding and errors
    """
    assert container_to_text(test_input, encoding=DEFAULT_ENCODING,
                             errors=DEFAULT_ERR_HANDLER) == expected


@pytest.mark.parametrize(
    'test_input,encoding,expected',
    [
        (u'й'.encode('utf-8'), 'latin1', u'Ð¹'),
        (u'café'.encode('utf-8'), 'shift_jis', u'cafﾃｩ'),
    ]
)
@pytest.mark.parametrize('errors', ['strict', 'surrogate_or_strict', 'surrogate_then_replace', ])
def test_container_to_text_incomp_encod_chars(test_input, encoding, errors, expected):
    """
    Test for passing incompatible characters and encodings container_to_text().
    """
    assert container_to_text(test_input, encoding=encoding, errors=errors) == expected
