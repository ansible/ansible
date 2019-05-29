# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import pytest

from datetime import datetime

from pytz import timezone as tz

from ansible.module_utils.common.text.converters import (
    _json_encode_fallback,
    container_to_bytes,
    container_to_text,
    jsonify,
)


DEFAULT_ENCODING = 'utf-8'


class TestJsonEncodeFallback:

    """Namespace for testing _json_encode_fallback."""

    @pytest.mark.parametrize(
        'test_input,expected',
        [
            (datetime(2019, 5, 14, 13, 39, 38, 569047), '2019-05-14T13:39:38.569047'),
            (datetime(2019, 5, 14, 13, 47, 16, 923866), '2019-05-14T13:47:16.923866'),
            (datetime(2019, 6, 15, 14, 45, tzinfo=tz('UTC')), '2019-06-15T14:45:00+00:00'),
            (datetime(2019, 6, 15, 14, 45, tzinfo=tz('Europe/Helsinki')), '2019-06-15T14:45:00+01:40'),
        ]
    )
    def test_date_datetime(self, test_input, expected):
        """
        Test for passing datetime.datetime objects to _json_encode_fallback().
        """

        assert _json_encode_fallback(test_input) == expected

    def test_set(self):
        """
        Test for passing a set object to _json_encode_fallback().
        """

        assert _json_encode_fallback(set([1])) == [1]

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
    def test_default_behavior(self, test_input):
        """
        Test for _json_encode_fallback() using other types.

        It must fail with TypeError.
        """

        with pytest.raises(TypeError, match='Cannot json serialize'):
            _json_encode_fallback(test_input)


class TestContainerToBytes:

    """Namespace for testing container_to_bytes()."""

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
    def test_to_bytes_different_types(self, test_input, expected, encoding, errors):
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
    def test_to_bytes_default_encoding_err(self, test_input, expected):
        """
        Test for passing objects to container_to_bytes(). Default encoding and errors
        """

        assert container_to_bytes(test_input, errors='surrogate_or_strict') == expected

    @pytest.mark.parametrize(
        'test_input,encoding',
        [
            (u'くらとみ', 'latin1'),
            (u'café', 'shift_jis'),
        ]
    )
    def test_incompatible_chars_and_encodings(self, test_input, encoding):
        """
        Test for passing incompatible characters and encodings container_to_bytes().
        """

        with pytest.raises(UnicodeEncodeError, match="codec can't encode"):
            container_to_bytes(test_input, encoding=encoding, errors='surrogate_or_strict')


class TestContainerToText:

    """Namespace for testing container_to_text()."""

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
    @pytest.mark.parametrize('encoding', ['utf-8', 'latin1', 'shift-jis', 'big5', 'koi8_r'])
    @pytest.mark.parametrize('errors', ['strict', 'surrogate_or_strict', 'surrogate_then_replace'])
    def test_to_text_different_types(self, test_input, expected, encoding, errors):
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
    def test_to_text_default_encoding_err(self, test_input, expected):
        """
        Test for passing objects to container_to_text(). Default encoding and errors
        """

        assert container_to_text(test_input, errors='surrogate_or_strict') == expected

    @pytest.mark.parametrize(
        'test_input,encoding,expected',
        [
            (u'й'.encode('utf-8'), 'latin1', u'Ð¹'),
            (u'café'.encode('utf-8'), 'shift_jis', u'cafﾃｩ'),
        ]
    )
    @pytest.mark.parametrize('errors', ['strict', 'surrogate_or_strict', 'surrogate_then_replace'])
    def test_incompatible_encodings_chars(self, test_input, encoding, errors, expected):
        """
        Test for passing incompatible characters and encodings container_to_text().
        """

        assert container_to_text(test_input, encoding=encoding, errors=errors) == expected


class TestJsonify:

    """Namespace for testing jsonify()."""

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
    def test_common_test(self, test_input, expected):
        """
        Test for jsonify().
        """

        assert jsonify(test_input) == expected
