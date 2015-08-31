# (c) 2015 Toshio Kuratomi <tkuratomi@ansible.com>
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

import jinja2
from ansible.compat.tests import unittest

from ansible.template import _preserve_backslashes


class TestBackslashEscape(unittest.TestCase):

    test_data = (
                # Test backslashes in a filter arg are double escaped
                dict(
                    template="{{ 'test2 %s' | format('\\1') }}",
                    intermediate="{{ 'test2 %s' | format('\\\\1') }}",
                    expectation="test2 \\1",
                    args=dict()
                ),
                # Test backslashes inside the jinja2 var itself are double
                # escaped
                dict(
                    template="Test 2\\3: {{ '\\1 %s' | format('\\2') }}",
                    intermediate="Test 2\\3: {{ '\\\\1 %s' | format('\\\\2') }}",
                    expectation="Test 2\\3: \\1 \\2",
                    args=dict()
                ),
                # Test backslashes outside of the jinja2 var are not double
                # escaped
                dict(
                    template="Test 2\\3: {{ 'test2 %s' | format('\\1') }}; \\done",
                    intermediate="Test 2\\3: {{ 'test2 %s' | format('\\\\1') }}; \\done",
                    expectation="Test 2\\3: test2 \\1; \\done",
                    args=dict()
                ),
                # Test backslashes in a variable sent to a filter are handled
                dict(
                    template="{{ 'test2 %s' | format(var1) }}",
                    #intermediate="{{ 'test2 %s' | format('\\\\1') }}",
                    intermediate="{{ 'test2 %s' | format(var1) }}",
                    expectation="test2 \\1",
                    args=dict(var1='\\1')
                ),
                # Test backslashes in a variable expanded by jinja2 are double
                # escaped
                dict(
                    template="Test 2\\3: {{ var1 | format('\\2') }}",
                    intermediate="Test 2\\3: {{ var1 | format('\\\\2') }}",
                    expectation="Test 2\\3: \\1 \\2",
                    args=dict(var1='\\1 %s')
                ),
            )
    def setUp(self):
        self.env = jinja2.Environment()

    def tearDown(self):
        pass

    def test_backslash_escaping(self):

        for test in self.test_data:
            intermediate = _preserve_backslashes(test['template'], self.env)
            self.assertEquals(intermediate, test['intermediate'])
            template = jinja2.Template(intermediate)
            args = test['args']
            self.assertEquals(template.render(**args), test['expectation'])

