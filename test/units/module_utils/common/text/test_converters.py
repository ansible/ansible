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
            'string',
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
            ('str', b'str'),
            (['str'], [b'str']),
            (('str'), (b'str')),
            ({'str': 'str'}, {b'str': b'str'}),
            ({u'str': u'str'}, {b'str': b'str'}),
        ]
    )
    @pytest.mark.parametrize('encoding', ['utf-8', 'latin1'])
    @pytest.mark.parametrize('errors', ['strict', 'ignore'])
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
            ('str', 'str'.encode(DEFAULT_ENCODING)),
            (b'str', 'str'.encode(DEFAULT_ENCODING)),
            (u'str', 'str'.encode(DEFAULT_ENCODING)),
            (['str'], ['str'.encode(DEFAULT_ENCODING)]),
            (('str'), ('str'.encode(DEFAULT_ENCODING))),
            ({'str': 'str'}, {'str'.encode(DEFAULT_ENCODING): 'str'.encode(DEFAULT_ENCODING)}),
        ]
    )
    def test_to_bytes_default_encoding_err(self, test_input, expected):
        """
        Test for passing objects to container_to_bytes(). Default encoding and errors
        """

        assert container_to_bytes(test_input) == expected


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
            ('str', u'str'),
            (b'str', u'str'),
            (u'str', u'str'),
            ([b'str'], [u'str']),
            ((b'str'), (u'str')),
            ({b'str': b'str'}, {u'str': u'str'}),
        ]
    )
    @pytest.mark.parametrize('encoding', ['utf-8', 'latin1'])
    @pytest.mark.parametrize('errors', ['strict', 'ignore'])
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
            ('str'.encode(DEFAULT_ENCODING), u'str'),
            (['str'.encode(DEFAULT_ENCODING)], [u'str']),
            (('str'.encode(DEFAULT_ENCODING)), (u'str')),
            ({b'str': b'str'}, {u'str': u'str'}),
        ]
    )
    def test_to_text_default_encoding_err(self, test_input, expected):
        """
        Test for passing objects to container_to_text(). Default encoding and errors
        """

        assert container_to_text(test_input) == expected


class TestJsonify:

    """Namespace for testing jsonify()."""

    @pytest.mark.parametrize(
        'test_input,expected',
        [
            (1, '1'),
            ('string', '"string"'),
            (False, 'false'),
            ('b_string'.encode('utf-8'), '"b_string"'),
        ]
    )
    def test_common_test(self, test_input, expected):
        """
        Test for passing common set object to _json_encode_fallback().
        """

        assert jsonify(test_input) == expected
