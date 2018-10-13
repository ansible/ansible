# -*- coding: utf-8 -*-
# (c) 2016, Matt Davis <mdavis@ansible.com>
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

import json

from units.compat import unittest
from ansible.module_utils.json_utils import _filter_non_json_lines


class TestAnsibleModuleExitJson(unittest.TestCase):
    single_line_json_dict = u"""{"key": "value", "olá": "mundo"}"""
    single_line_json_array = u"""["a","b","c"]"""
    multi_line_json_dict = u"""{
"key":"value"
}"""
    multi_line_json_array = u"""[
"a",
"b",
"c"]"""

    all_inputs = [
        single_line_json_dict,
        single_line_json_array,
        multi_line_json_dict,
        multi_line_json_array
    ]

    junk = [u"single line of junk", u"line 1/2 of junk\nline 2/2 of junk"]

    unparsable_cases = (
        u'No json here',
        u'"olá": "mundo"',
        u'{"No json": "ending"',
        u'{"wrong": "ending"]',
        u'["wrong": "ending"}',
    )

    def test_just_json(self):
        for i in self.all_inputs:
            filtered, warnings = _filter_non_json_lines(i)
            self.assertEquals(filtered, i)
            self.assertEquals(warnings, [])

    def test_leading_junk(self):
        for i in self.all_inputs:
            for j in self.junk:
                filtered, warnings = _filter_non_json_lines(j + "\n" + i)
                self.assertEquals(filtered, i)
                self.assertEquals(warnings, [])

    def test_trailing_junk(self):
        for i in self.all_inputs:
            for j in self.junk:
                filtered, warnings = _filter_non_json_lines(i + "\n" + j)
                self.assertEquals(filtered, i)
                self.assertEquals(warnings, [u"Module invocation had junk after the JSON data: %s" % j.strip()])

    def test_leading_and_trailing_junk(self):
        for i in self.all_inputs:
            for j in self.junk:
                filtered, warnings = _filter_non_json_lines("\n".join([j, i, j]))
                self.assertEquals(filtered, i)
                self.assertEquals(warnings, [u"Module invocation had junk after the JSON data: %s" % j.strip()])

    def test_unparsable_filter_non_json_lines(self):
        for i in self.unparsable_cases:
            self.assertRaises(
                ValueError,
                _filter_non_json_lines,
                data=i
            )
