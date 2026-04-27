# base unit test classes for ansible/module_utils/facts/ tests
# -*- coding: utf-8 -*-
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
#

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch


class BaseFactsTest(unittest.TestCase):
    # just a base class, not an actual test
    __test__ = False

    gather_subset = ['all']
    valid_subsets = None
    fact_namespace = None
    collector_class = None

    # a dict ansible_facts. Some fact collectors depend on facts gathered by
    # other collectors (like 'ansible_architecture' or 'ansible_system') which
    # can be passed via the collected_facts arg to collect()
    collected_facts = None

    def _mock_module(self):
        mock_module = Mock()
        mock_module.params = {'gather_subset': self.gather_subset,
                              'gather_timeout': 5,
                              'filter': '*'}
        mock_module.get_bin_path = Mock(return_value=None)
        return mock_module

    @patch('platform.system', return_value='Linux')
    @patch('ansible.module_utils.facts.system.service_mgr.get_file_content', return_value='systemd')
    def test_collect(self, mock_gfc, mock_ps):
        self._test_collect()

    def _test_collect(self):
        module = self._mock_module()
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module, collected_facts=self.collected_facts)
        self.assertIsInstance(facts_dict, dict)
        return facts_dict

    @patch('platform.system', return_value='Linux')
    @patch('ansible.module_utils.facts.system.service_mgr.get_file_content', return_value='systemd')
    def test_collect_with_namespace(self, mock_gfc, mock_ps):
        module = self._mock_module()
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect_with_namespace(module=module,
                                                           collected_facts=self.collected_facts)
        self.assertIsInstance(facts_dict, dict)
