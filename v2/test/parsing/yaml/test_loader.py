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

from StringIO import StringIO
from collections import Sequence, Set, Mapping

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

from ansible.parsing.yaml.loader import AnsibleLoader

class TestAnsibleLoaderBasic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_number(self):
        stream = StringIO("""
                1
                """)
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, 1)
        # No line/column info saved yet

    def test_parse_string(self):
        stream = StringIO("""
                Ansible
                """)
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, u'Ansible')
        self.assertIsInstance(data, unicode)

        self.assertEqual(data._line_number, 2)
        self.assertEqual(data._column_number, 17)
        self.assertEqual(data._data_source, 'myfile.yml')

    def test_parse_utf8_string(self):
        stream = StringIO("""
                Cafè Eñyei
                """)
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, u'Cafè Eñyei')
        self.assertIsInstance(data, unicode)

        self.assertEqual(data._line_number, 2)
        self.assertEqual(data._column_number, 17)
        self.assertEqual(data._data_source, 'myfile.yml')

    def test_parse_dict(self):
        stream = StringIO("""
                webster: daniel
                oed: oxford
                """)
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, {'webster': 'daniel', 'oed': 'oxford'})
        self.assertEqual(len(data), 2)
        self.assertIsInstance(data.keys()[0], unicode)
        self.assertIsInstance(data.values()[0], unicode)

        # Note: this is the beginning of the first value.
        # May be changed in the future to beginning of the first key
        self.assertEqual(data._line_number, 2)
        self.assertEqual(data._column_number, 25)
        self.assertEqual(data._data_source, 'myfile.yml')

        self.assertEqual(data[u'webster']._line_number, 2)
        self.assertEqual(data[u'webster']._column_number, 17)
        self.assertEqual(data[u'webster']._data_source, 'myfile.yml')

        self.assertEqual(data[u'oed']._line_number, 3)
        self.assertEqual(data[u'oed']._column_number, 17)
        self.assertEqual(data[u'oed']._data_source, 'myfile.yml')

    def test_parse_list(self):
        stream = StringIO("""
                - a
                - b
                """)
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, [u'a', u'b'])
        self.assertEqual(len(data), 2)
        self.assertIsInstance(data[0], unicode)
        # No line/column info saved yet

class TestAnsibleLoaderPlay(unittest.TestCase):

    def setUp(self):
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
        self.play_filename = '/path/to/myplay.yml'
        stream.name = self.play_filename
        self.loader = AnsibleLoader(stream)
        self.data = self.loader.get_single_data()

    def tearDown(self):
        pass

    def test_data_complete(self):
        return
        self.assertEqual(len(self.data), 1)
        self.assertIsInstance(self.data, list)
        self.assertEqual(frozenset(self.data[0].keys()), frozenset((u'hosts', u'vars', u'tasks')))

        self.assertEqual(self.data[0][u'hosts'], u'localhost')

        self.assertEqual(self.data[0][u'vars'][u'number'], 1)
        self.assertEqual(self.data[0][u'vars'][u'string'], u'Ansible')
        self.assertEqual(self.data[0][u'vars'][u'utf8_string'], u'Cafè Eñyei')
        self.assertEqual(self.data[0][u'vars'][u'dictionary'],
                {u'webster': u'daniel',
                    u'oed': u'oxford'})
        self.assertEqual(self.data[0][u'vars'][u'list'], [u'a', u'b', 1, 2])

        self.assertEqual(self.data[0][u'tasks'],
                [{u'name': u'Test case', u'ping': {u'data': u'{{ utf8_string }}'}},
                 {u'name': u'Test 2', u'ping': {u'data': u'Cafè Eñyei'}},
                 {u'name': u'Test 3', u'command': u'printf \'Cafè Eñyei\n\''},
                 ])

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

    def test_no_str_in_data(self):
        # Checks that no strings are str type
        self.walk(self.data)

    def check_vars(self):
        # Numbers don't have line/col information yet
        #self.assertEqual(self.data[0][u'vars'][u'number']._line_number, 4)
        #self.assertEqual(self.data[0][u'vars'][u'number']._column_number, 21)
        #self.assertEqual(self.data[0][u'vars'][u'number']._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'vars'][u'string']._line_number, 5)
        self.assertEqual(self.data[0][u'vars'][u'string']._column_number, 21)
        self.assertEqual(self.data[0][u'vars'][u'string']._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'vars'][u'utf8_string']._line_number, 6)
        self.assertEqual(self.data[0][u'vars'][u'utf8_string']._column_number, 21)
        self.assertEqual(self.data[0][u'vars'][u'utf8_string']._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'vars'][u'dictionary']._line_number, 8)
        self.assertEqual(self.data[0][u'vars'][u'dictionary']._column_number, 31)
        self.assertEqual(self.data[0][u'vars'][u'dictionary']._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'vars'][u'dictionary'][u'webster']._line_number, 8)
        self.assertEqual(self.data[0][u'vars'][u'dictionary'][u'webster']._column_number, 23)
        self.assertEqual(self.data[0][u'vars'][u'dictionary'][u'webster']._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'vars'][u'dictionary'][u'oed']._line_number, 9)
        self.assertEqual(self.data[0][u'vars'][u'dictionary'][u'oed']._column_number, 23)
        self.assertEqual(self.data[0][u'vars'][u'dictionary'][u'oed']._data_source, self.play_filename)

        # Lists don't yet have line/col information
        #self.assertEqual(self.data[0][u'vars'][u'list']._line_number, 10)
        #self.assertEqual(self.data[0][u'vars'][u'list']._column_number, 21)
        #self.assertEqual(self.data[0][u'vars'][u'list']._data_source, self.play_filename)

    def check_tasks(self):
        #
        # First Task
        #
        self.assertEqual(self.data[0][u'tasks'][0]._line_number, 16)
        self.assertEqual(self.data[0][u'tasks'][0]._column_number, 28)
        self.assertEqual(self.data[0][u'tasks'][0]._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'tasks'][0][u'name']._line_number, 16)
        self.assertEqual(self.data[0][u'tasks'][0][u'name']._column_number, 23)
        self.assertEqual(self.data[0][u'tasks'][0][u'name']._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'tasks'][0][u'ping']._line_number, 18)
        self.assertEqual(self.data[0][u'tasks'][0][u'ping']._column_number, 30)
        self.assertEqual(self.data[0][u'tasks'][0][u'ping']._data_source, self.play_filename)

        #self.assertEqual(self.data[0][u'tasks'][0][u'ping'][u'data']._line_number, 18)
        self.assertEqual(self.data[0][u'tasks'][0][u'ping'][u'data']._column_number, 25)
        self.assertEqual(self.data[0][u'tasks'][0][u'ping'][u'data']._data_source, self.play_filename)

        #
        # Second Task
        #
        self.assertEqual(self.data[0][u'tasks'][1]._line_number, 20)
        self.assertEqual(self.data[0][u'tasks'][1]._column_number, 28)
        self.assertEqual(self.data[0][u'tasks'][1]._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'tasks'][1][u'name']._line_number, 20)
        self.assertEqual(self.data[0][u'tasks'][1][u'name']._column_number, 23)
        self.assertEqual(self.data[0][u'tasks'][1][u'name']._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'tasks'][1][u'ping']._line_number, 22)
        self.assertEqual(self.data[0][u'tasks'][1][u'ping']._column_number, 30)
        self.assertEqual(self.data[0][u'tasks'][1][u'ping']._data_source, self.play_filename)

        #self.assertEqual(self.data[0][u'tasks'][1][u'ping'][u'data']._line_number, 22)
        self.assertEqual(self.data[0][u'tasks'][1][u'ping'][u'data']._column_number, 25)
        self.assertEqual(self.data[0][u'tasks'][1][u'ping'][u'data']._data_source, self.play_filename)

        #
        # Third Task
        #
        self.assertEqual(self.data[0][u'tasks'][2]._line_number, 24)
        self.assertEqual(self.data[0][u'tasks'][2]._column_number, 28)
        self.assertEqual(self.data[0][u'tasks'][2]._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'tasks'][2][u'name']._line_number, 24)
        self.assertEqual(self.data[0][u'tasks'][2][u'name']._column_number, 23)
        self.assertEqual(self.data[0][u'tasks'][2][u'name']._data_source, self.play_filename)

        #self.assertEqual(self.data[0][u'tasks'][2][u'command']._line_number, 25)
        self.assertEqual(self.data[0][u'tasks'][2][u'command']._column_number, 23)
        self.assertEqual(self.data[0][u'tasks'][2][u'command']._data_source, self.play_filename)

    def test_line_numbers(self):
        # Check the line/column numbers are correct
        # Note: Remember, currently dicts begin at the start of their first entry's value
        self.assertEqual(self.data[0]._line_number, 2)
        self.assertEqual(self.data[0]._column_number, 25)
        self.assertEqual(self.data[0]._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'hosts']._line_number, 2)
        self.assertEqual(self.data[0][u'hosts']._column_number, 19)
        self.assertEqual(self.data[0][u'hosts']._data_source, self.play_filename)

        self.assertEqual(self.data[0][u'vars']._line_number, 4)
        self.assertEqual(self.data[0][u'vars']._column_number, 28)
        self.assertEqual(self.data[0][u'vars']._data_source, self.play_filename)

        self.check_vars()

        # Lists don't yet have line/col info
        #self.assertEqual(self.data[0][u'tasks']._line_number, 17)
        #self.assertEqual(self.data[0][u'tasks']._column_number, 28)
        #self.assertEqual(self.data[0][u'tasks']._data_source, self.play_filename)

        self.check_tasks()
