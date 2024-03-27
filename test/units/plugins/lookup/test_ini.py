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

from __future__ import annotations

import unittest
from ansible.plugins.lookup.ini import _parse_params


class TestINILookup(unittest.TestCase):

    # Currently there isn't a new-style
    old_style_params_data = (
        # Simple case
        dict(
            term="keyA section=sectionA file=/path/to/file",
            expected=["file=/path/to/file", "keyA", "section=sectionA"],
        ),
        dict(
            term="keyB section=sectionB with space file=/path/with/embedded spaces and/file",
            expected=[
                "file=/path/with/embedded spaces and/file",
                "keyB",
                "section=sectionB with space",
            ],
        ),
        dict(
            term="keyC section=sectionC file=/path/with/equals/cn=com.ansible",
            expected=[
                "file=/path/with/equals/cn=com.ansible",
                "keyC",
                "section=sectionC",
            ],
        ),
        dict(
            term="keyD section=sectionD file=/path/with space and/equals/cn=com.ansible",
            expected=[
                "file=/path/with space and/equals/cn=com.ansible",
                "keyD",
                "section=sectionD",
            ],
        ),
        dict(
            term="keyE section=sectionE file=/path/with/unicode/くらとみ/file",
            expected=[
                "file=/path/with/unicode/くらとみ/file",
                "keyE",
                "section=sectionE",
            ],
        ),
        dict(
            term="keyF section=sectionF file=/path/with/utf 8 and spaces/くらとみ/file",
            expected=[
                "file=/path/with/utf 8 and spaces/くらとみ/file",
                "keyF",
                "section=sectionF",
            ],
        ),
    )

    def test_parse_parameters(self):
        pvals = {
            "file": "",
            "section": "",
            "key": "",
            "type": "",
            "re": "",
            "default": "",
            "encoding": "",
        }
        for testcase in self.old_style_params_data:
            # print(testcase)
            params = _parse_params(testcase["term"], pvals)
            params.sort()
            self.assertEqual(params, testcase["expected"])
