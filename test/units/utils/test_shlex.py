# (c) 2015, Marius Gedminas <marius@gedmin.as>
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

import unittest

from ansible.utils.shlex import shlex_split


class TestSplit(unittest.TestCase):

    def test_trivial(self):
        self.assertEqual(shlex_split("a b c"), ["a", "b", "c"])

    def test_unicode(self):
        self.assertEqual(shlex_split(u"a b \u010D"), [u"a", u"b", u"\u010D"])

    def test_quoted(self):
        self.assertEqual(shlex_split('"a b" c'), ["a b", "c"])

    def test_comments(self):
        self.assertEqual(shlex_split('"a b" c # d', comments=True), ["a b", "c"])

    def test_error(self):
        self.assertRaises(ValueError, shlex_split, 'a "b')
