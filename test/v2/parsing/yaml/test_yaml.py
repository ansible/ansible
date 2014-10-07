# TODO: header

import unittest
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

class TestSafeLoad(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_safe_load(self):
        # test basic dictionary
        res = safe_load(data1)
        assert type(res) == AnsibleMapping
        assert res._line_number == 2

        # test data with multiple dictionaries
        res = safe_load(data2)
        assert len(res) == 4
        assert res[0]._line_number == 2
        assert res[1]._line_number == 3
        assert res[2]._line_number == 5
        assert res[3]._line_number == 8

        # test data with multiple sub-dictionaries
        res = safe_load(data3)
        assert len(res) == 3
        assert res[0]._line_number == 2
        assert res[1]._line_number == 7
        assert res[2]._line_number == 9
        assert res[0]['key1']._line_number == 3
        assert res[1]['key2']._line_number == 8
        assert res[2]['list1'][0]._line_number == 10
