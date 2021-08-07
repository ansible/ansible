# -*- coding: utf-8 -*-
# Copyright: (c) 2020 Thales Netherlands
# Copyright: (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat import unittest
from units.compat.mock import patch
from units.mock.loader import DictDataLoader

from ansible.plugins import AnsiblePlugin
from ansible.plugins.lookup import merge_variables
from ansible.template import Templar
from ansible.errors import AnsibleError
from ansible.utils.display import Display


class TestMergeVariablesLookup(unittest.TestCase):
    def setUp(self):
        self.loader = DictDataLoader({})
        self.templar = Templar(loader=self.loader, variables={})
        self.merge_vars_lookup = merge_variables.LookupModule(loader=self.loader, templar=self.templar)

    @patch.object(AnsiblePlugin, 'set_options')
    @patch.object(AnsiblePlugin, 'get_option', side_effect=[None, False, False])
    @patch.object(Templar, 'template', side_effect=[['item1'], ['item3']])
    def test_merge_list(self, mock_set_options, mock_get_option, mock_template):
        results = self.merge_vars_lookup.run(['__merge_list'], {
            'testlist1__merge_list': ['item1'],
            'testlist2': ['item2'],
            'testlist3__merge_list': ['item3']
        })

        self.assertEqual(results, [['item1', 'item3']])

    @patch.object(AnsiblePlugin, 'set_options')
    @patch.object(AnsiblePlugin, 'get_option', side_effect=[['initial_item'], False, False])
    @patch.object(Templar, 'template', side_effect=[['item1'], ['item3']])
    def test_merge_list_with_initial_value(self, mock_set_options, mock_get_option, mock_template):
        results = self.merge_vars_lookup.run(['__merge_list'], {
            'testlist1__merge_list': ['item1'],
            'testlist2': ['item2'],
            'testlist3__merge_list': ['item3']
        })

        self.assertEqual(results, [['initial_item', 'item1', 'item3']])

    @patch.object(AnsiblePlugin, 'set_options')
    @patch.object(AnsiblePlugin, 'get_option', side_effect=[None, False, False])
    @patch.object(Templar, 'template', side_effect=[{'item1': 'test', 'list_item': ['test1']},
                                                    {'item2': 'test', 'list_item': ['test2']}])
    def test_merge_dict(self, mock_set_options, mock_get_option, mock_template):
        results = self.merge_vars_lookup.run(['__merge_dict'], {
            'testdict1__merge_dict': {
                'item1': 'test',
                'list_item': ['test1']
            },
            'testdict2__merge_dict': {
                'item2': 'test',
                'list_item': ['test2']
            }
        })

        self.assertEqual(results, [
            {
                'item1': 'test',
                'item2': 'test',
                'list_item': ['test1', 'test2']
            }
        ])

    @patch.object(AnsiblePlugin, 'set_options')
    @patch.object(AnsiblePlugin, 'get_option', side_effect=[{'initial_item': 'random value', 'list_item': ['test0']},
                                                            False, False])
    @patch.object(Templar, 'template', side_effect=[{'item1': 'test', 'list_item': ['test1']},
                                                    {'item2': 'test', 'list_item': ['test2']}])
    def test_merge_dict_with_initial_value(self, mock_set_options, mock_get_option, mock_template):
        results = self.merge_vars_lookup.run(['__merge_dict'], {
            'testdict1__merge_dict': {
                'item1': 'test',
                'list_item': ['test1']
            },
            'testdict2__merge_dict': {
                'item2': 'test',
                'list_item': ['test2']
            }
        })

        self.assertEqual(results, [
            {
                'initial_item': 'random value',
                'item1': 'test',
                'item2': 'test',
                'list_item': ['test0', 'test1', 'test2']
            }
        ])

    @patch.object(AnsiblePlugin, 'set_options')
    @patch.object(AnsiblePlugin, 'get_option', side_effect=[None, True, False])  # override_warning enabled
    @patch.object(Templar, 'template', side_effect=[{'item': 'value1'}, {'item': 'value2'}])
    @patch.object(Display, 'warning')
    def test_merge_dict_non_unique_warning(self, mock_set_options, mock_get_option, mock_template, mock_display):
        results = self.merge_vars_lookup.run(['__merge_non_unique'], {
            'testdict1__merge_non_unique': {'item': 'value1'},
            'testdict2__merge_non_unique': {'item': 'value2'}
        })

        self.assertTrue(mock_display.called)
        self.assertEqual(results, [{'item': 'value2'}])

    @patch.object(AnsiblePlugin, 'set_options')
    @patch.object(AnsiblePlugin, 'get_option', side_effect=[None, False, True])  # override_error enabled
    @patch.object(Templar, 'template', side_effect=[{'item': 'value1'}, {'item': 'value2'}])
    def test_merge_dict_non_unique_error(self, mock_set_options, mock_get_option, mock_template):
        with self.assertRaises(AnsibleError):
            self.merge_vars_lookup.run(['__merge_non_unique'], {
                'testdict1__merge_non_unique': {'item': 'value1'},
                'testdict2__merge_non_unique': {'item': 'value2'}
            })

    @patch.object(AnsiblePlugin, 'set_options')
    @patch.object(AnsiblePlugin, 'get_option', side_effect=[None, False, False])
    @patch.object(Templar, 'template', side_effect=[{'item1': 'test', 'list_item': ['test1']},
                                                    ['item2', 'item3']])
    def test_merge_list_and_dict(self, mock_set_options, mock_get_option, mock_template):
        with self.assertRaises(AnsibleError):
            self.merge_vars_lookup.run(['__merge_var'], {
                'testlist__merge_var': {
                    'item1': 'test',
                    'list_item': ['test1']
                },
                'testdict__merge_var': ['item2', 'item3']
            })
