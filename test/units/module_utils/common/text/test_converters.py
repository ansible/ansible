# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import pytest

from datetime import datetime
from pytz import timezone as tz

from ansible.module_utils.common._collections_compat import Set
from ansible.module_utils.common.text.converters import (
    _json_encode_fallback,
    container_to_bytes,
    container_to_text,
    jsonify,
)


DEFAULT_ENCODING = 'utf-8'


class Test_json_encode_fallback:

    """Namespace for testing _json_encode_fallback."""

    @pytest.fixture(scope='class')
    def _set(self, request):
        """
        Returns object of mock Set class.

        The object is used for testing handling of collections.Set objects
        in _json_encode_fallback().
        """

        class S(Set):

            """Mock Set class."""

            def __init__(self, iterable):
                self.elements = lst = []
                for value in iterable:
                    if value not in lst:
                        lst.append(value)

            def __iter__(self):
                return iter(self.elements)

            def __contains__(self, value):
                return value in self.elements

            def __len__(self):
                return len(self.elements)

        return S(request.param)

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

    @pytest.mark.parametrize(
        '_set,expected',
        [
            ([1], [1]),
            ([1, 2], [1, 2]),
            (['one'], ['one']),
            ([1, 'two'], [1, 'two']),
        ], indirect=['_set'],
    )
    def test_collections_Set(self, _set, expected):
        """
        Test for passing collections.Set object to _json_encode_fallback().
        """
        assert _json_encode_fallback(_set) == expected

    @pytest.mark.parametrize(
        'test_input,expected',
        [
            (set([1]), [1]),
            (set([2]), [2]),
        ]
    )
    def test_common_set(self, test_input, expected):
        """
        Test for passing common set object to _json_encode_fallback().
        """
        assert _json_encode_fallback(test_input) == expected

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
        with pytest.raises(TypeError):
            _json_encode_fallback(test_input)


class Test_container_to_bytes:

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
        ]
    )
    @pytest.mark.parametrize('encoding', ['utf-8', 'ascii'])
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


class Test_container_to_text:

    """Namespace for testing container_to_text()."""

    @pytest.mark.parametrize(
        'test_input,expected',
        [
            ({1: 1}, {1: 1}),
            ([1, 2], [1, 2]),
            ((1, 2), (1, 2)),
            (1, 1),
            (1.1, 1.1),
            (b'str', 'str'),
            ([b'str'], ['str']),
            ((b'str'), ('str')),
            ({b'str': b'str'}, {'str': 'str'}),
        ]
    )
    @pytest.mark.parametrize('encoding', ['utf-8', 'ascii'])
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
            ('str'.encode(DEFAULT_ENCODING), 'str'),
            (['str'.encode(DEFAULT_ENCODING)], ['str']),
            (('str'.encode(DEFAULT_ENCODING)), ('str')),
            ({'str'.encode(DEFAULT_ENCODING): 'str'.encode(DEFAULT_ENCODING)}, {'str': 'str'}),
        ]
    )
    def test_to_text_default_encoding_err(self, test_input, expected):
        """
        Test for passing objects to container_to_text(). Default encoding and errors
        """

        assert container_to_text(test_input) == expected


class Test_jsonify:

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
