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

from ansible.compat.tests import unittest
from ansible.errors import AnsibleInternalError, AnsibleParserError
from ansible.parsing import load

import json
import yaml

from io import FileIO

class MockFile(FileIO):

    def __init__(self, ds, method='json'):
        self.ds = ds
        self.method = method

    def read(self):
        if self.method == 'json':
            return json.dumps(self.ds)
        elif self.method == 'yaml':
            return yaml.dump(self.ds)
        elif self.method == 'fail':
            return """
            AAARGGGGH:
                *****
               THIS WON'T PARSE !!!
                  NOOOOOOOOOOOOOOOOOO
            """
        else:
            raise Exception("untestable serializer")

    def close(self):
        pass

class TestGeneralParsing(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_json_from_string(self):
        data = """
        {
            "asdf" : "1234",
            "jkl" : 5678
        }
        """
        output = load(data)
        self.assertEqual(output['asdf'], '1234')
        self.assertEqual(output['jkl'], 5678)

    def test_parse_json_from_file(self):
        output = load(MockFile(dict(a=1,b=2,c=3), 'json'))
        self.assertEqual(output, dict(a=1,b=2,c=3))

    def test_parse_yaml_from_dict(self):
        data = """
        asdf: '1234'
        jkl: 5678
        """
        output = load(data)
        self.assertEqual(output['asdf'], '1234')
        self.assertEqual(output['jkl'], 5678)

    def test_parse_yaml_from_file(self):
        output = load(MockFile(dict(a=1,b=2,c=3),'yaml'))
        self.assertEqual(output, dict(a=1,b=2,c=3))

    def test_parse_fail(self):
        data = """
        TEXT:
            ***
               NOT VALID
        """
        self.assertRaises(AnsibleParserError, load, data)

    def test_parse_fail_from_file(self):
        self.assertRaises(AnsibleParserError, load, MockFile(None,'fail'))

    def test_parse_fail_invalid_type(self):
        self.assertRaises(AnsibleInternalError, load, 3000)
        self.assertRaises(AnsibleInternalError, load, dict(a=1,b=2,c=3))

