# -*- coding: utf-8 -*-
# (c) 2015-2017, Toshio Kuratomi <tkuratomi@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from itertools import chain
import pytest


# Strings that should be converted into a typed value
VALID_STRINGS = (
    ("'a'", 'a'),
    ("'1'", '1'),
    ("1", 1),
    ("True", True),
    ("False", False),
    ("{}", {}),
)

# Passing things that aren't strings should just return the object
NONSTRINGS = (
    ({'a': 1}, {'a': 1}),
)

# These strings are not basic types.  For security, these should not be
# executed.  We return the same string and get an exception for some
INVALID_STRINGS = (
    ("a=1", "a=1", SyntaxError),
    ("a.foo()", "a.foo()", None),
    ("import foo", "import foo", None),
    ("__import__('foo')", "__import__('foo')", ValueError),
)


@pytest.mark.parametrize('code, expected, stdin',
                         ((c, e, {}) for c, e in chain(VALID_STRINGS, NONSTRINGS)),
                         indirect=['stdin'])
def test_simple_types(am, code, expected):
    # test some basic usage for various types
    assert am.safe_eval(code) == expected


@pytest.mark.parametrize('code, expected, stdin',
                         ((c, e, {}) for c, e in chain(VALID_STRINGS, NONSTRINGS)),
                         indirect=['stdin'])
def test_simple_types_with_exceptions(am, code, expected):
    # Test simple types with exceptions requested
    assert am.safe_eval(code, include_exceptions=True), (expected, None)


@pytest.mark.parametrize('code, expected, stdin',
                         ((c, e, {}) for c, e, dummy in INVALID_STRINGS),
                         indirect=['stdin'])
def test_invalid_strings(am, code, expected):
    assert am.safe_eval(code) == expected


@pytest.mark.parametrize('code, expected, exception, stdin',
                         ((c, e, ex, {}) for c, e, ex in INVALID_STRINGS),
                         indirect=['stdin'])
def test_invalid_strings_with_exceptions(am, code, expected, exception):
    res = am.safe_eval(code, include_exceptions=True)
    assert res[0] == expected
    if exception is None:
        assert res[1] == exception
    else:
        assert type(res[1]) == exception
