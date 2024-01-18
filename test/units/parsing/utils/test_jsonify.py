# -*- coding: utf-8 -*-
# (c) 2016, James Cammarata <jimi@sngx.net>
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
from ansible.parsing.utils.jsonify import jsonify


class TestJsonify(unittest.TestCase):
    def test_jsonify_simple(self):
        self.assertEqual(jsonify(dict(a=1, b=2, c=3)), '{"a": 1, "b": 2, "c": 3}')

    def test_jsonify_simple_format(self):
        res = jsonify(dict(a=1, b=2, c=3), format=True)
        cleaned = "".join([x.strip() for x in res.splitlines()])
        self.assertEqual(cleaned, '{"a": 1,"b": 2,"c": 3}')

    def test_jsonify_unicode(self):
        self.assertEqual(jsonify(dict(toshio=u'くらとみ')), u'{"toshio": "くらとみ"}')

    def test_jsonify_empty(self):
        self.assertEqual(jsonify(None), '{}')
