# -*- coding: utf-8 -*-
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import itertools

import pytest

from ansible.module_utils.common.text.converters import to_text, to_bytes, to_native


# Format: byte representation, text representation, encoding of byte representation
VALID_STRINGS = (
    (b'abcde', u'abcde', 'ascii'),
    (b'caf\xc3\xa9', u'caf\xe9', 'utf-8'),
    (b'caf\xe9', u'caf\xe9', 'latin-1'),
    # u'くらとみ'
    (b'\xe3\x81\x8f\xe3\x82\x89\xe3\x81\xa8\xe3\x81\xbf', u'\u304f\u3089\u3068\u307f', 'utf-8'),
    (b'\x82\xad\x82\xe7\x82\xc6\x82\xdd', u'\u304f\u3089\u3068\u307f', 'shift-jis'),
)


@pytest.mark.parametrize('in_string, encoding, expected',
                         itertools.chain(((d[0], d[2], d[1]) for d in VALID_STRINGS),
                                         ((d[1], d[2], d[1]) for d in VALID_STRINGS)))
def test_to_text(in_string, encoding, expected):
    """test happy path of decoding to text"""
    assert to_text(in_string, encoding) == expected


@pytest.mark.parametrize('in_string, encoding, expected',
                         itertools.chain(((d[0], d[2], d[0]) for d in VALID_STRINGS),
                                         ((d[1], d[2], d[0]) for d in VALID_STRINGS)))
def test_to_bytes(in_string, encoding, expected):
    """test happy path of encoding to bytes"""
    assert to_bytes(in_string, encoding) == expected


@pytest.mark.parametrize('in_string, encoding, expected',
                         itertools.chain(((d[0], d[2], d[1]) for d in VALID_STRINGS),
                                         ((d[1], d[2], d[1]) for d in VALID_STRINGS)))
def test_to_native(in_string, encoding, expected):
    """test happy path of encoding to native strings"""
    assert to_native(in_string, encoding) == expected


def test_type_hints() -> None:
    """This test isn't really here to test the functionality of to_text/to_bytes
    but more to ensure the overloads are properly validated for type hinting
    """
    d: dict[str, str] = {'k': 'v'}
    s: str = 's'
    b: bytes = b'b'

    to_bytes_bytes: bytes = to_bytes(b)
    to_bytes_str: bytes = to_bytes(s)
    to_bytes_dict: bytes = to_bytes(d)
    assert to_bytes_dict == repr(d).encode('utf-8')

    to_bytes_bytes_repr: bytes = to_bytes(b, nonstring='simplerepr')
    to_bytes_str_repr: bytes = to_bytes(s, nonstring='simplerepr')
    to_bytes_dict_repr: bytes = to_bytes(d, nonstring='simplerepr')
    assert to_bytes_dict_repr == repr(d).encode('utf-8')

    to_bytes_bytes_passthru: bytes = to_bytes(b, nonstring='passthru')
    to_bytes_str_passthru: bytes = to_bytes(s, nonstring='passthru')
    to_bytes_dict_passthru: dict[str, str] = to_bytes(d, nonstring='passthru')
    assert to_bytes_dict_passthru == d

    to_bytes_bytes_empty: bytes = to_bytes(b, nonstring='empty')
    to_bytes_str_empty: bytes = to_bytes(s, nonstring='empty')
    to_bytes_dict_empty: bytes = to_bytes(d, nonstring='empty')
    assert to_bytes_dict_empty == b''

    to_bytes_bytes_strict: bytes = to_bytes(b, nonstring='strict')
    to_bytes_str_strict: bytes = to_bytes(s, nonstring='strict')
    with pytest.raises(TypeError):
        to_bytes_dict_strict: bytes = to_bytes(d, nonstring='strict')

    to_text_bytes: str = to_text(b)
    to_text_str: str = to_text(s)
    to_text_dict: str = to_text(d)
    assert to_text_dict == repr(d)

    to_text_bytes_repr: str = to_text(b, nonstring='simplerepr')
    to_text_str_repr: str = to_text(s, nonstring='simplerepr')
    to_text_dict_repr: str = to_text(d, nonstring='simplerepr')
    assert to_text_dict_repr == repr(d)

    to_text_bytes_passthru: str = to_text(b, nonstring='passthru')
    to_text_str_passthru: str = to_text(s, nonstring='passthru')
    to_text_dict_passthru: dict[str, str] = to_text(d, nonstring='passthru')
    assert to_text_dict_passthru == d

    to_text_bytes_empty: str = to_text(b, nonstring='empty')
    to_text_str_empty: str = to_text(s, nonstring='empty')
    to_text_dict_empty: str = to_text(d, nonstring='empty')
    assert to_text_dict_empty == ''

    to_text_bytes_strict: str = to_text(b, nonstring='strict')
    to_text_str_strict: str = to_text(s, nonstring='strict')
    with pytest.raises(TypeError):
        to_text_dict_strict: str = to_text(d, nonstring='strict')
