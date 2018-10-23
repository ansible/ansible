# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.vars.clean import module_response_deepcopy

import pytest


def test_module_response_deepcopy_basic():
    x = 42
    y = module_response_deepcopy(x)
    assert y == x


def test_module_response_deepcopy_atomic():
    tests = [None, 42, 2**100, 3.14, True, False, 1j,
             "hello", u"hello\u1234"]
    for x in tests:
        assert module_response_deepcopy(x) is x


def test_module_response_deepcopy_list():
    x = [[1, 2], 3]
    y = module_response_deepcopy(x)
    assert y == x
    assert x is not y
    assert x[0] is not y[0]


def test_module_response_deepcopy_empty_tuple():
    x = ()
    y = module_response_deepcopy(x)
    assert x is y


@pytest.mark.skip(reason='No current support for this situation')
def test_module_response_deepcopy_tuple():
    x = ([1, 2], 3)
    y = module_response_deepcopy(x)
    assert y == x
    assert x is not y
    assert x[0] is not y[0]


def test_module_response_deepcopy_tuple_of_immutables():
    x = ((1, 2), 3)
    y = module_response_deepcopy(x)
    assert x is y


def test_module_response_deepcopy_dict():
    x = {"foo": [1, 2], "bar": 3}
    y = module_response_deepcopy(x)
    assert y == x
    assert x is not y
    assert x["foo"] is not y["foo"]
