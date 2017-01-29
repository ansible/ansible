# -*- coding: utf-8 -*-
# (c) 2015-2016, Toshio Kuratomi <tkuratomi@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import sys
import json

from ansible.compat.tests import unittest
from units.mock.procenv import ModuleTestCase
from units.mock.generator import add_method


# Strings that should be converted into a typed value
VALID_STRINGS = (
    [("'a'", 'a')],
    [("'1'", '1')],
    [("1", 1)],
    [("True", True)],
    [("False", False)],
    [("{}", {})],
    )

# Passing things that aren't strings should just return the object
NONSTRINGS = (
    [({'a':1}, {'a':1})],
    )

# These strings are not basic types.  For security, these should not be
# executed.  We return the same string and get an exception for some
INVALID_STRINGS = (
    [("a=1", "a=1", SyntaxError)],
    [("a.foo()", "a.foo()", None)],
    [("import foo", "import foo", None)],
    [("__import__('foo')", "__import__('foo')", ValueError)],
    )


def _check_simple_types(self, code, expected):
    # test some basic usage for various types
    self.assertEqual(self.am.safe_eval(code), expected)

def _check_simple_types_with_exceptions(self, code, expected):
    # Test simple types with exceptions requested
    self.assertEqual(self.am.safe_eval(code, include_exceptions=True), (expected, None))

def _check_invalid_strings(self, code, expected):
    self.assertEqual(self.am.safe_eval(code), expected)

def _check_invalid_strings_with_exceptions(self, code, expected, exception):
    res = self.am.safe_eval("a=1", include_exceptions=True)
    self.assertEqual(res[0], "a=1")
    self.assertEqual(type(res[1]), SyntaxError)

@add_method(_check_simple_types, *VALID_STRINGS)
@add_method(_check_simple_types, *NONSTRINGS)
@add_method(_check_simple_types_with_exceptions, *VALID_STRINGS)
@add_method(_check_simple_types_with_exceptions, *NONSTRINGS)
@add_method(_check_invalid_strings, *[[i[0][0:-1]] for i in INVALID_STRINGS])
@add_method(_check_invalid_strings_with_exceptions, *INVALID_STRINGS)
class TestSafeEval(ModuleTestCase):

    def setUp(self):
        super(TestSafeEval, self).setUp()

        from ansible.module_utils import basic
        self.old_ansible_args = basic._ANSIBLE_ARGS

        basic._ANSIBLE_ARGS = None
        self.am = basic.AnsibleModule(
            argument_spec=dict(),
        )

    def tearDown(self):
        super(TestSafeEval, self).tearDown()

        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = self.old_ansible_args
