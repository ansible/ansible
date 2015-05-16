# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible import constants as C
from ansible.plugins import filter_loader, lookup_loader, module_loader
from ansible.plugins.strategies import SharedPluginLoaderObj
from ansible.template import Templar

from units.mock.loader import DictDataLoader

class TestTemplar(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_templar_simple(self):
        fake_loader = DictDataLoader({})
        shared_loader = SharedPluginLoaderObj()
        templar = Templar(loader=fake_loader, variables=dict(foo="bar", bam="{{foo}}", num=1, var_true=True, var_false=False, var_dict=dict(a="b"), bad_dict="{a='b'", var_list=[1]))

        # test some basic templating
        self.assertEqual(templar.template("{{foo}}"), "bar")
        self.assertEqual(templar.template("{{foo}}\n"), "bar")
        self.assertEqual(templar.template("{{foo}}\n", preserve_trailing_newlines=True), "bar\n")
        self.assertEqual(templar.template("foo", convert_bare=True), "bar")
        self.assertEqual(templar.template("{{bam}}"), "bar")
        self.assertEqual(templar.template("{{num}}"), 1)
        self.assertEqual(templar.template("{{var_true}}"), True)
        self.assertEqual(templar.template("{{var_false}}"), False)
        self.assertEqual(templar.template("{{var_dict}}"), dict(a="b"))
        self.assertEqual(templar.template("{{bad_dict}}"), "{a='b'")
        self.assertEqual(templar.template("{{var_list}}"), [1])

        # test set_available_variables()
        templar.set_available_variables(variables=dict(foo="bam"))
        self.assertEqual(templar.template("{{foo}}"), "bam")
        # variables must be a dict() for set_available_variables()
        self.assertRaises(AssertionError, templar.set_available_variables, "foo=bam") 

    def test_template_jinja2_extensions(self):
        fake_loader = DictDataLoader({})
        templar = Templar(loader=fake_loader)
        
        old_exts = C.DEFAULT_JINJA2_EXTENSIONS
        try:
            C.DEFAULT_JINJA2_EXTENSIONS = "foo,bar"
            self.assertEqual(templar._get_extensions(), ['foo', 'bar'])
        finally:
            C.DEFAULT_JINJA2_EXTENSIONS = old_exts

