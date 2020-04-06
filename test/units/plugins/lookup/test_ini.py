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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat import unittest
from ansible.plugins.lookup.ini import _parse_params


class TestINILookup(unittest.TestCase):

    # Currently there isn't a new-style
    old_style_params_data = (
        # Simple case
        dict(
            term=u'keyA section=sectionA file=/path/to/file',
            expected=[u'file=/path/to/file', u'keyA', u'section=sectionA'],
        ),
        dict(
            term=u'keyB section=sectionB with space file=/path/with/embedded spaces and/file',
            expected=[u'file=/path/with/embedded spaces and/file', u'keyB', u'section=sectionB with space'],
        ),
        dict(
            term=u'keyC section=sectionC file=/path/with/equals/cn=com.ansible',
            expected=[u'file=/path/with/equals/cn=com.ansible', u'keyC', u'section=sectionC'],
        ),
        dict(
            term=u'keyD section=sectionD file=/path/with space and/equals/cn=com.ansible',
            expected=[u'file=/path/with space and/equals/cn=com.ansible', u'keyD', u'section=sectionD'],
        ),
        dict(
            term=u'keyE section=sectionE file=/path/with/unicode/くらとみ/file',
            expected=[u'file=/path/with/unicode/くらとみ/file', u'keyE', u'section=sectionE'],
        ),
        dict(
            term=u'keyF section=sectionF file=/path/with/utf 8 and spaces/くらとみ/file',
            expected=[u'file=/path/with/utf 8 and spaces/くらとみ/file', u'keyF', u'section=sectionF'],
        ),
    )

    def test_parse_parameters(self):
        for testcase in self.old_style_params_data:
            # print(testcase)
            params = _parse_params(testcase['term'])
            params.sort()
            self.assertEqual(params, testcase['expected'])
