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

from io import StringIO

from six import text_type, binary_type
from collections import Sequence, Set, Mapping

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

from ansible.parsing.yaml.loader import AnsibleLoader

try:
    from _yaml import ParserError
except ImportError:
    from yaml.parser import ParserError


class NameStringIO(StringIO):
    """In py2.6, StringIO doesn't let you set name because a baseclass has it
    as readonly property"""
    name = None
    def __init__(self, *args, **kwargs):
        super(NameStringIO, self).__init__(*args, **kwargs)

class TestAnsibleLoaderBasic(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_number(self):
        stream = StringIO(u"""
                1
                """)
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, 1)
        # No line/column info saved yet

    def test_parse_string(self):
        stream = StringIO(u"""
                Ansible
                """)
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, u'Ansible')
        self.assertIsInstance(data, text_type)

        self.assertEqual(data.ansible_pos, ('myfile.yml', 2, 17))

    def test_parse_utf8_string(self):
        stream = StringIO(u"""
                Cafè Eñyei
                """)
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, u'Cafè Eñyei')
        self.assertIsInstance(data, text_type)

        self.assertEqual(data.ansible_pos, ('myfile.yml', 2, 17))

    def test_parse_dict(self):
        stream = StringIO(u"""
                webster: daniel
                oed: oxford
                """)
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, {'webster': 'daniel', 'oed': 'oxford'})
        self.assertEqual(len(data), 2)
        self.assertIsInstance(list(data.keys())[0], text_type)
        self.assertIsInstance(list(data.values())[0], text_type)

        # Beginning of the first key
        self.assertEqual(data.ansible_pos, ('myfile.yml', 2, 17))

        self.assertEqual(data[u'webster'].ansible_pos, ('myfile.yml', 2, 26))
        self.assertEqual(data[u'oed'].ansible_pos, ('myfile.yml', 3, 22))

    def test_parse_list(self):
        stream = StringIO(u"""
                - a
                - b
                """)
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, [u'a', u'b'])
        self.assertEqual(len(data), 2)
        self.assertIsInstance(data[0], text_type)

        self.assertEqual(data.ansible_pos, ('myfile.yml', 2, 17))

        self.assertEqual(data[0].ansible_pos, ('myfile.yml', 2, 19))
        self.assertEqual(data[1].ansible_pos, ('myfile.yml', 3, 19))

    def test_parse_short_dict(self):
        stream = StringIO(u"""{"foo": "bar"}""")
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, dict(foo=u'bar'))

        self.assertEqual(data.ansible_pos, ('myfile.yml', 1, 1))
        self.assertEqual(data[u'foo'].ansible_pos, ('myfile.yml', 1, 9))

        stream = StringIO(u"""foo: bar""")
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, dict(foo=u'bar'))

        self.assertEqual(data.ansible_pos, ('myfile.yml', 1, 1))
        self.assertEqual(data[u'foo'].ansible_pos, ('myfile.yml', 1, 6))

    def test_error_conditions(self):
        stream = StringIO(u"""{""")
        loader = AnsibleLoader(stream, 'myfile.yml')
        self.assertRaises(ParserError, loader.get_single_data)

    def test_front_matter(self):
        stream = StringIO(u"""---\nfoo: bar""")
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, dict(foo=u'bar'))

        self.assertEqual(data.ansible_pos, ('myfile.yml', 2, 1))
        self.assertEqual(data[u'foo'].ansible_pos, ('myfile.yml', 2, 6))

        # Initial indent (See: #6348)
        stream = StringIO(u""" - foo: bar\n   baz: qux""")
        loader = AnsibleLoader(stream, 'myfile.yml')
        data = loader.get_single_data()
        self.assertEqual(data, [{u'foo': u'bar', u'baz': u'qux'}])

        self.assertEqual(data.ansible_pos, ('myfile.yml', 1, 2))
        self.assertEqual(data[0].ansible_pos, ('myfile.yml', 1, 4))
        self.assertEqual(data[0][u'foo'].ansible_pos, ('myfile.yml', 1, 9))
        self.assertEqual(data[0][u'baz'].ansible_pos, ('myfile.yml', 2, 9))


class TestAnsibleLoaderPlay(unittest.TestCase):

    def setUp(self):
        stream = NameStringIO(u"""
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
        self.assertNotIsInstance(data, binary_type)

        # Descend into various container types
        if isinstance(data, text_type):
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
        #self.assertEqual(self.data[0][u'vars'][u'number'].ansible_pos, (self.play_filename, 4, 21))

        self.assertEqual(self.data[0][u'vars'][u'string'].ansible_pos, (self.play_filename, 5, 29))
        self.assertEqual(self.data[0][u'vars'][u'utf8_string'].ansible_pos, (self.play_filename, 6, 34))

        self.assertEqual(self.data[0][u'vars'][u'dictionary'].ansible_pos, (self.play_filename, 8, 23))
        self.assertEqual(self.data[0][u'vars'][u'dictionary'][u'webster'].ansible_pos, (self.play_filename, 8, 32))
        self.assertEqual(self.data[0][u'vars'][u'dictionary'][u'oed'].ansible_pos, (self.play_filename, 9, 28))

        self.assertEqual(self.data[0][u'vars'][u'list'].ansible_pos, (self.play_filename, 11, 23))
        self.assertEqual(self.data[0][u'vars'][u'list'][0].ansible_pos, (self.play_filename, 11, 25))
        self.assertEqual(self.data[0][u'vars'][u'list'][1].ansible_pos, (self.play_filename, 12, 25))
        # Numbers don't have line/col info yet
        #self.assertEqual(self.data[0][u'vars'][u'list'][2].ansible_pos, (self.play_filename, 13, 25))
        #self.assertEqual(self.data[0][u'vars'][u'list'][3].ansible_pos, (self.play_filename, 14, 25))

    def check_tasks(self):
        #
        # First Task
        #
        self.assertEqual(self.data[0][u'tasks'][0].ansible_pos, (self.play_filename, 16, 23))
        self.assertEqual(self.data[0][u'tasks'][0][u'name'].ansible_pos, (self.play_filename, 16, 29))
        self.assertEqual(self.data[0][u'tasks'][0][u'ping'].ansible_pos, (self.play_filename, 18, 25))
        self.assertEqual(self.data[0][u'tasks'][0][u'ping'][u'data'].ansible_pos, (self.play_filename, 18, 31))

        #
        # Second Task
        #
        self.assertEqual(self.data[0][u'tasks'][1].ansible_pos, (self.play_filename, 20, 23))
        self.assertEqual(self.data[0][u'tasks'][1][u'name'].ansible_pos, (self.play_filename, 20, 29))
        self.assertEqual(self.data[0][u'tasks'][1][u'ping'].ansible_pos, (self.play_filename, 22, 25))
        self.assertEqual(self.data[0][u'tasks'][1][u'ping'][u'data'].ansible_pos, (self.play_filename, 22, 31))

        #
        # Third Task
        #
        self.assertEqual(self.data[0][u'tasks'][2].ansible_pos, (self.play_filename, 24, 23))
        self.assertEqual(self.data[0][u'tasks'][2][u'name'].ansible_pos, (self.play_filename, 24, 29))
        self.assertEqual(self.data[0][u'tasks'][2][u'command'].ansible_pos, (self.play_filename, 25, 32))

    def test_line_numbers(self):
        # Check the line/column numbers are correct
        # Note: Remember, currently dicts begin at the start of their first entry
        self.assertEqual(self.data[0].ansible_pos, (self.play_filename, 2, 19))
        self.assertEqual(self.data[0][u'hosts'].ansible_pos, (self.play_filename, 2, 26))
        self.assertEqual(self.data[0][u'vars'].ansible_pos, (self.play_filename, 4, 21))

        self.check_vars()

        self.assertEqual(self.data[0][u'tasks'].ansible_pos, (self.play_filename, 16, 21))

        self.check_tasks()
