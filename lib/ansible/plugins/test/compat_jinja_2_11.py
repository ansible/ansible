# -*- coding: utf-8 -*-

# Copyright (c) 2017, the Jinja Team
# BSD 3-Clause "New" or "Revised" License (see https://opensource.org/licenses/BSD-3-Clause)

# XXX: These tests exist for compatibility with Jinja < 2.11.  Once every
# platform has at least 2.11 version of jinja, this file can go away.
# originally from https://github.com/pallets/jinja/pull/824

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import jinja2
from distutils.version import LooseVersion
from ansible.module_utils.six import integer_types


def test_boolean(value):
    """Return true if the object is a boolean value.
    .. versionadded:: 2.11
    """
    return value is True or value is False


def test_false(value):
    """Return true if the object is False.
    .. versionadded:: 2.11
    """
    return value is False


def test_true(value):
    """Return true if the object is True.
    .. versionadded:: 2.11
    """
    return value is True


# NOTE: The existing Jinja2 'number' test matches booleans and floats
def test_integer(value):
    """Return true if the object is an integer.
    .. versionadded:: 2.11
    """
    return isinstance(value, integer_types) and value is not True and value is not False


# NOTE: The existing Jinja2 'number' test matches booleans and integers
def test_float(value):
    """Return true if the object is a float.
    .. versionadded:: 2.11
    """
    return isinstance(value, float)


class TestModule:
    """copied from jinja 2.11 for consistent test behavior independent of the
    system jinja version
    """

    def tests(self):
        if LooseVersion(str(jinja2.__version__)) >= LooseVersion('2.11'):
            return {}

        return {
            'boolean': test_boolean,
            'false': test_false,
            'true': test_true,
            'integer': test_integer,
            'float': test_float,
        }
