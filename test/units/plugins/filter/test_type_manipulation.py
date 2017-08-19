# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.plugins.filter.type_manipulation import (list_to_dict, dict_to_list)
from ansible.errors import AnsibleError, AnsibleFilterError


class TestTypeFilter(unittest.TestCase):
    def test_list_to_dict(self):
        # Good test
        list_original = [{"proto":"eigrp", "state":"enabled"}, {"proto":"ospf", "state":"enabled"}] 
        key = 'proto'
        dict_return = {'eigrp': {'state': 'enabled', 'proto': 'eigrp'}, 'ospf': {'state': 'enabled', 'proto': 'ospf'}}
        self.assertEqual(list_to_dict(list_original, key), dict_return)

        
        # Fail when key is not found
        key = 'key_not_to_be_found'
        self.assertRaises(AnsibleFilterError, list_to_dict, list_original, key)

        # Fail when key is duplicated
        list_original = [{"proto":"eigrp", "state":"enabled"}, {"proto":"ospf", "state":"enabled"}, {"proto":"ospf", "state":"enabled"}] 
        key = 'proto'
        self.assertRaises(AnsibleFilterError, list_to_dict, list_original, key)

        # Fail when list item is not a dict
        list_original = [{"proto":"eigrp", "state":"enabled"}, "ospf"] 
        key = 'proto'
        self.assertRaises(AnsibleFilterError, list_to_dict, list_original, key)

