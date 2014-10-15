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

from ... compat import unittest

from yaml.scanner import ScannerError

from ansible.parsing.yaml import safe_load
from ansible.parsing.yaml.objects import AnsibleMapping

# a single dictionary instance
data1 = '''---
key: value
'''

# multiple dictionary instances
data2 = '''---
- key1: value1
- key2: value2

- key3: value3


- key4: value4
'''

# multiple dictionary instances with other nested
# dictionaries contained within those
data3 = '''---
- key1:
    subkey1: subvalue1
    subkey2: subvalue2
    subkey3:
      subsubkey1: subsubvalue1
- key2:
    subkey4: subvalue4
- list1:
  - list1key1: list1value1
    list1key2: list1value2
    list1key3: list1value3
'''

bad_data1 = '''---
foo: bar
  bam: baz
'''

class TestSafeLoad(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_safe_load_bad(self):
        # test the loading of bad yaml data
        self.assertRaises(ScannerError, safe_load, bad_data1)

    def test_safe_load(self):
        # test basic dictionary
        res = safe_load(data1)
        self.assertEqual(type(res), AnsibleMapping)
        self.assertEqual(res._line_number, 2)

        # test data with multiple dictionaries
        res = safe_load(data2)
        self.assertEqual(len(res), 4)
        self.assertEqual(res[0]._line_number, 2)
        self.assertEqual(res[1]._line_number, 3)
        self.assertEqual(res[2]._line_number, 5)
        self.assertEqual(res[3]._line_number, 8)

        # test data with multiple sub-dictionaries
        res = safe_load(data3)
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0]._line_number, 2)
        self.assertEqual(res[1]._line_number, 7)
        self.assertEqual(res[2]._line_number, 9)
        self.assertEqual(res[0]['key1']._line_number, 3)
        self.assertEqual(res[1]['key2']._line_number, 8)
        self.assertEqual(res[2]['list1'][0]._line_number, 10)
