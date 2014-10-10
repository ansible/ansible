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

import unittest
from ansible.parsing import load
from ansible.errors import AnsibleParserError

import json

class MockFile(file):

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
        assert output['asdf'] == '1234'
        assert output['jkl'] == 5678

    def parse_json_from_file(self):
        output = load(MockFile(dict(a=1,b=2,c=3)),'json')
        assert ouput == dict(a=1,b=2,c=3)

    def parse_yaml_from_dict(self):
        input = """
        asdf: '1234'
        jkl: 5678
        """
        output = load(input)
        assert output['asdf'] == '1234'
        assert output['jkl'] == 5678

    def parse_yaml_from_file(self):
        output = load(MockFile(dict(a=1,b=2,c=3),'yaml'))
        assert output == dict(a=1,b=2,c=3)

    def parse_fail(self):
        input = """
        TEXT
            ***
               NOT VALID
        """
        self.failUnlessRaises(load(input), AnsibleParserError)

    def parse_fail_from_file(self):
        self.failUnlessRaises(load(MockFile(None,'fail')), AnsibleParserError)

    def parse_fail_invalid_type(self):
        self.failUnlessRaises(3000, AnsibleParsingError)
        self.failUnlessRaises(dict(a=1,b=2,c=3), AnsibleParserError)
        
