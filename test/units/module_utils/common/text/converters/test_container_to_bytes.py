# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.text.converters import container_to_bytes


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
        (b'str', b'str'),
        (u'str', b'str'),
        ([u'str'], [b'str']),
        ((u'str'), (b'str')),
        ({u'str': u'str'}, {b'str': b'str'}),
    ]
)
@pytest.mark.parametrize('encoding', ['utf-8', 'latin1', 'shift_jis', 'big5', 'koi8_r'])
@pytest.mark.parametrize('errors', ['strict', 'surrogate_or_strict', 'surrogate_then_replace'])
def test_container_to_bytes(test_input, expected, encoding, errors):
    """Test for passing objects to container_to_bytes()."""
    assert container_to_bytes(test_input, encoding=encoding, errors=errors) == expected


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
        (u'str', u'str'.encode(DEFAULT_ENCODING)),
        (u'くらとみ', u'くらとみ'.encode(DEFAULT_ENCODING)),
        (u'café', u'café'.encode(DEFAULT_ENCODING)),
        (b'str', u'str'.encode(DEFAULT_ENCODING)),
        (u'str', u'str'.encode(DEFAULT_ENCODING)),
        ([u'str'], [u'str'.encode(DEFAULT_ENCODING)]),
        ((u'str'), (u'str'.encode(DEFAULT_ENCODING))),
        ({u'str': u'str'}, {u'str'.encode(DEFAULT_ENCODING): u'str'.encode(DEFAULT_ENCODING)}),
    ]
)
def test_container_to_bytes_default_encoding_err(test_input, expected):
    """
    Test for passing objects to container_to_bytes(). Default encoding and errors
    """
    assert container_to_bytes(test_input, encoding=DEFAULT_ENCODING,
                              errors=DEFAULT_ERR_HANDLER) == expected


@pytest.mark.parametrize(
    'test_input,encoding',
    [
        (u'くらとみ', 'latin1'),
        (u'café', 'shift_jis'),
    ]
)
@pytest.mark.parametrize('errors', ['surrogate_or_strict', 'strict'])
def test_container_to_bytes_incomp_chars_and_encod(test_input, encoding, errors):
    """
    Test for passing incompatible characters and encodings container_to_bytes().
    """
    with pytest.raises(UnicodeEncodeError, match="codec can't encode"):
        container_to_bytes(test_input, encoding=encoding, errors=errors)


@pytest.mark.parametrize(
    'test_input,encoding,expected',
    [
        (u'くらとみ', 'latin1', b'????'),
        (u'café', 'shift_jis', b'caf?'),
    ]
)
def test_container_to_bytes_surrogate_then_replace(test_input, encoding, expected):
    """
    Test for container_to_bytes() with surrogate_then_replace err handler.
    """
    assert container_to_bytes(test_input, encoding=encoding,
                              errors='surrogate_then_replace') == expected
