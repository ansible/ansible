# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.plugins.filter.cast_type import (cast_list_to_dict, cast_dict_to_list)
from ansible.errors import AnsibleError, AnsibleFilterError


class TestTypeFilter(unittest.TestCase):
    def test_cast_list_to_dict(self):
        # Good test
        list_original = [{"proto": "eigrp", "state": "enabled"}, {"proto": "ospf", "state": "enabled"}]
        key = 'proto'
        dict_return = {'eigrp': {'state': 'enabled', 'proto': 'eigrp'}, 'ospf': {'state': 'enabled', 'proto': 'ospf'}}
        self.assertEqual(cast_list_to_dict(list_original, key), dict_return)

        # Fail when key is not found
        key = 'key_not_to_be_found'
        self.assertRaisesRegexp(AnsibleFilterError, 'was not found', cast_list_to_dict, list_original, key)

        # Fail when key is duplicated
        list_original = [{"proto": "eigrp", "state": "enabled"}, {"proto": "ospf", "state": "enabled"}, {"proto": "ospf", "state": "enabled"}]
        key = 'proto'
        self.assertRaisesRegexp(AnsibleFilterError, 'is not unique', cast_list_to_dict, list_original, key)

        # Fail when list item is not a dict
        list_original = [{"proto": "eigrp", "state": "enabled"}, "ospf"]
        key = 'proto'
        self.assertRaisesRegexp(AnsibleFilterError, 'List item is not a valid dict', cast_list_to_dict, list_original, key)

        # Fail when a non list is sent
        list_original = {"proto": "eigrp", "state": "enabled"}
        key = 'proto'
        self.assertRaisesRegexp(AnsibleFilterError, 'not a valid list', cast_list_to_dict, list_original, key)

    def test_cast_dict_to_list(self):
        # Good test
        dict_original = {'eigrp': {'state': 'enabled', 'as': '1'}, 'ospf': {'state': 'enabled', 'as': '2'}}
        key_name = 'proto'
        list_return = [{'state': 'enabled', 'proto': 'ospf', 'as': '2'}, {'state': 'enabled', 'proto': 'eigrp', 'as': '1'}]
        actual_return = cast_dict_to_list(dict_original, key_name)

        try:
            _assertItemsEqual = self.assertCountEqual
            _assertItemsEqual(actual_return, list_return)
        except AttributeError:
            self.assertEqual(sorted(actual_return), sorted(list_return))

        # Fail when dict key is already used
        dict_original = {'eigrp': {'state': 'enabled', 'as': '1', 'proto': 'bgp'}, 'ospf': {'state': 'enabled', 'as': '2'}}
        key_name = 'proto'
        self.assertRaisesRegexp(AnsibleFilterError, ' already in use, cannot correctly turn into dict', cast_dict_to_list, dict_original, key_name)

        # Fail when sending a non-dict
        dict_original = [{'eigrp': {'state': 'enabled', 'as': '1'}, 'ospf': {'state': 'enabled', 'as': '2'}}]
        key_name = 'proto'
        self.assertRaisesRegexp(AnsibleFilterError, 'Type is not a valid dict', cast_dict_to_list, dict_original, key_name)

        # Fail when dict value is not a dict
        dict_original = {'eigrp': [{'state': 'enabled', 'as': '1'}], 'ospf': {'state': 'enabled', 'as': '2'}}
        key_name = 'proto'
        self.assertRaisesRegexp(AnsibleFilterError, 'Type of key', cast_dict_to_list, dict_original, key_name)
