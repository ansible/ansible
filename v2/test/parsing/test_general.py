# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from .. compat import unittest
from ansible.parsing import load
from ansible.errors import AnsibleParserError

import json

from io import FileIO

class MockFile(FileIO):

    def __init__(self, ds, method='json'):
        self.ds = ds
        self.method = method

    def read(self):
        if method == 'json':
            return json.dumps(ds)
        elif method == 'yaml':
            return yaml.dumps(ds)
        elif method == 'fail':
            return """
            AAARGGGGH
               THIS WON'T PARSE !!!
                  NOOOOOOOOOOOOOOOOOO
            """
        else:
            raise Exception("untestable serializer")

    def close(self):
        pass

class TestGeneralParsing(unittest.TestCase):

    def __init__(self):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def parse_json_from_string(self):
        input = """
        {
            "asdf" : "1234",
            "jkl" : 5678
        }
        """
        output = load(input)
        self.assertEqual(output['asdf'], '1234')
        self.assertEqual(output['jkl'], 5678)

    def parse_json_from_file(self):
        output = load(MockFile(dict(a=1,b=2,c=3)),'json')
        self.assertEqual(ouput, dict(a=1,b=2,c=3))

    def parse_yaml_from_dict(self):
        input = """
        asdf: '1234'
        jkl: 5678
        """
        output = load(input)
        self.assertEqual(output['asdf'], '1234')
        self.assertEqual(output['jkl'], 5678)

    def parse_yaml_from_file(self):
        output = load(MockFile(dict(a=1,b=2,c=3),'yaml'))
        self.assertEqual(output, dict(a=1,b=2,c=3))

    def parse_fail(self):
        input = """
        TEXT
            ***
               NOT VALID
        """
        self.assertRaises(load(input), AnsibleParserError)

    def parse_fail_from_file(self):
        self.assertRaises(load(MockFile(None,'fail')), AnsibleParserError)

    def parse_fail_invalid_type(self):
        self.assertRaises(3000, AnsibleParsingError)
        self.assertRaises(dict(a=1,b=2,c=3), AnsibleParserError)

