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

from __future__ import annotations

import jinja2
import unittest

from ansible.template import AnsibleUndefined, _escape_backslashes, _count_newlines_from_end

# These are internal utility functions only needed for templating.  They're
# algorithmic so good candidates for unit testing by themselves


class TestBackslashEscape(unittest.TestCase):

    test_data = (
        # Test backslashes in a filter arg are double escaped
        dict(
            template=u"{{ 'test2 %s' | format('\\1') }}",
            intermediate=u"{{ 'test2 %s' | format('\\\\1') }}",
            expectation=u"test2 \\1",
            args=dict()
        ),
        # Test backslashes inside the jinja2 var itself are double
        # escaped
        dict(
            template=u"Test 2\\3: {{ '\\1 %s' | format('\\2') }}",
            intermediate=u"Test 2\\3: {{ '\\\\1 %s' | format('\\\\2') }}",
            expectation=u"Test 2\\3: \\1 \\2",
            args=dict()
        ),
        # Test backslashes outside of the jinja2 var are not double
        # escaped
        dict(
            template=u"Test 2\\3: {{ 'test2 %s' | format('\\1') }}; \\done",
            intermediate=u"Test 2\\3: {{ 'test2 %s' | format('\\\\1') }}; \\done",
            expectation=u"Test 2\\3: test2 \\1; \\done",
            args=dict()
        ),
        # Test backslashes in a variable sent to a filter are handled
        dict(
            template=u"{{ 'test2 %s' | format(var1) }}",
            intermediate=u"{{ 'test2 %s' | format(var1) }}",
            expectation=u"test2 \\1",
            args=dict(var1=u'\\1')
        ),
        # Test backslashes in a variable expanded by jinja2 are double
        # escaped
        dict(
            template=u"Test 2\\3: {{ var1 | format('\\2') }}",
            intermediate=u"Test 2\\3: {{ var1 | format('\\\\2') }}",
            expectation=u"Test 2\\3: \\1 \\2",
            args=dict(var1=u'\\1 %s')
        ),
    )

    def setUp(self):
        self.env = jinja2.Environment()

    def test_backslash_escaping(self):

        for test in self.test_data:
            intermediate = _escape_backslashes(test['template'], self.env)
            self.assertEqual(intermediate, test['intermediate'])
            template = jinja2.Template(intermediate)
            args = test['args']
            self.assertEqual(template.render(**args), test['expectation'])


class TestCountNewlines(unittest.TestCase):

    def test_zero_length_string(self):
        self.assertEqual(_count_newlines_from_end(u''), 0)

    def test_short_string(self):
        self.assertEqual(_count_newlines_from_end(u'The quick\n'), 1)

    def test_one_newline(self):
        self.assertEqual(_count_newlines_from_end(u'The quick brown fox jumped over the lazy dog' * 1000 + u'\n'), 1)

    def test_multiple_newlines(self):
        self.assertEqual(_count_newlines_from_end(u'The quick brown fox jumped over the lazy dog' * 1000 + u'\n\n\n'), 3)

    def test_zero_newlines(self):
        self.assertEqual(_count_newlines_from_end(u'The quick brown fox jumped over the lazy dog' * 1000), 0)

    def test_all_newlines(self):
        self.assertEqual(_count_newlines_from_end(u'\n' * 10), 10)

    def test_mostly_newlines(self):
        self.assertEqual(_count_newlines_from_end(u'The quick brown fox jumped over the lazy dog' + u'\n' * 1000), 1000)


class TestAnsibleUndefined(unittest.TestCase):
    def test_getattr(self):
        val = AnsibleUndefined()

        self.assertIs(getattr(val, 'foo'), val)

        self.assertRaises(AttributeError, getattr, val, '__UNSAFE__')
