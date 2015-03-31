# coding: utf-8
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

from cStringIO import StringIO
from collections import Sequence, Set, Mapping

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

from ansible.parsing.yaml.loader import AnsibleLoader

class TestDataLoader(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_number(self):
        stream = StringIO("""
                1
                """)
        loader = AnsibleLoader(stream)
        data = loader.get_single_data()
        self.assertEqual(data, 1)

    def test_parse_string(self):
        stream = StringIO("""
                Ansible
                """)
        loader = AnsibleLoader(stream)
        data = loader.get_single_data()
        self.assertEqual(data, u'Ansible')
        self.assertIsInstance(data, unicode)

    def test_parse_utf8_string(self):
        stream = StringIO("""
                Cafè Eñyei
                """)
        loader = AnsibleLoader(stream)
        data = loader.get_single_data()
        self.assertEqual(data, u'Cafè Eñyei')
        self.assertIsInstance(data, unicode)

    def test_parse_dict(self):
        stream = StringIO("""
                webster: daniel
                oed: oxford
                """)
        loader = AnsibleLoader(stream)
        data = loader.get_single_data()
        self.assertEqual(data, {'webster': 'daniel', 'oed': 'oxford'})
        self.assertEqual(len(data), 2)
        self.assertIsInstance(data.keys()[0], unicode)
        self.assertIsInstance(data.values()[0], unicode)

    def test_parse_list(self):
        stream = StringIO("""
                - a
                - b
                """)
        loader = AnsibleLoader(stream)
        data = loader.get_single_data()
        self.assertEqual(data, [u'a', u'b'])
        self.assertEqual(len(data), 2)
        self.assertIsInstance(data[0], unicode)

    def test_parse_play(self):
        stream = StringIO("""
                - hosts: localhost
                  vars:
                    number: 1
                    string: Ansible
                    utf8_string: Cafè Eñyei
                    dictionary:
                      webster: daniel
                      oed: oxford
                    list:
                      - a
                      - b
                      - 1
                      - 2
                  tasks:
                    - name: Test case
                      ping:
                        data: "{{ utf8_string }}"

                    - name: Test 2
                      ping:
                        data: "Cafè Eñyei"

                    - name: Test 3
                      command: "printf 'Cafè Eñyei\\n'"
                """)
        loader = AnsibleLoader(stream)
        data = loader.get_single_data()
        self.assertEqual(len(data), 1)
        self.assertIsInstance(data, list)
        self.assertEqual(frozenset(data[0].keys()), frozenset((u'hosts', u'vars', u'tasks')))

        self.assertEqual(data[0][u'hosts'], u'localhost')

        self.assertEqual(data[0][u'vars'][u'number'], 1)
        self.assertEqual(data[0][u'vars'][u'string'], u'Ansible')
        self.assertEqual(data[0][u'vars'][u'utf8_string'], u'Cafè Eñyei')
        self.assertEqual(data[0][u'vars'][u'dictionary'],
                {u'webster': u'daniel',
                    u'oed': u'oxford'})
        self.assertEqual(data[0][u'vars'][u'list'], [u'a', u'b', 1, 2])

        self.assertEqual(data[0][u'tasks'],
                [{u'name': u'Test case', u'ping': {u'data': u'{{ utf8_string }}'}},
                 {u'name': u'Test 2', u'ping': {u'data': u'Cafè Eñyei'}},
                 {u'name': u'Test 3', u'command': u'printf \'Cafè Eñyei\n\''},
                    ])

        self.walk(data)

    def walk(self, data):
        # Make sure there's no str in the data
        self.assertNotIsInstance(data, str)

        # Descend into various container types
        if isinstance(data, unicode):
            # strings are a sequence so we have to be explicit here
            return
        elif isinstance(data, (Sequence, Set)):
            for element in data:
                self.walk(element)
        elif isinstance(data, Mapping):
            for k, v in data.items():
                self.walk(k)
                self.walk(v)

        # Scalars were all checked so we're good to go
        return
