# -*- coding: utf-8 -*-
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
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
from units.mock.procenv import swap_stdin_and_argv

try:
    from importlib import reload
except:
    # Py2 has reload as a builtin
    pass

class TestAnsibleModuleExitJson(unittest.TestCase):

    def test_module_utils_basic_safe_eval(self):
        from ansible.module_utils import basic

        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={}, ANSIBLE_MODULE_CONSTANTS={}))

        with swap_stdin_and_argv(stdin_data=args):
            reload(basic)
            am = basic.AnsibleModule(
                argument_spec=dict(),
            )

            # test some basic usage
            # string (and with exceptions included), integer, bool
            self.assertEqual(am.safe_eval("'a'"), 'a')
            self.assertEqual(am.safe_eval("'a'", include_exceptions=True), ('a', None))
            self.assertEqual(am.safe_eval("1"), 1)
            self.assertEqual(am.safe_eval("True"), True)
            self.assertEqual(am.safe_eval("False"), False)
            self.assertEqual(am.safe_eval("{}"), {})
            # not passing in a string to convert
            self.assertEqual(am.safe_eval({'a':1}), {'a':1})
            self.assertEqual(am.safe_eval({'a':1}, include_exceptions=True), ({'a':1}, None))
            # invalid literal eval
            self.assertEqual(am.safe_eval("a=1"), "a=1")
            res = am.safe_eval("a=1", include_exceptions=True)
            self.assertEqual(res[0], "a=1")
            self.assertEqual(type(res[1]), SyntaxError)
            self.assertEqual(am.safe_eval("a.foo()"), "a.foo()")
            res = am.safe_eval("a.foo()", include_exceptions=True)
            self.assertEqual(res[0], "a.foo()")
            self.assertEqual(res[1], None)
            self.assertEqual(am.safe_eval("import foo"), "import foo")
            res = am.safe_eval("import foo", include_exceptions=True)
            self.assertEqual(res[0], "import foo")
            self.assertEqual(res[1], None)
            self.assertEqual(am.safe_eval("__import__('foo')"), "__import__('foo')")
            res = am.safe_eval("__import__('foo')", include_exceptions=True)
            self.assertEqual(res[0], "__import__('foo')")
            self.assertEqual(type(res[1]), ValueError)

