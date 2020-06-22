# unit tests for ansible system lsb fact collectors
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import Mock, patch

from .. base import BaseFactsTest

from ansible.module_utils.facts.system.lsb import LSBFactCollector


lsb_release_a_fedora_output = '''
LSB Version:	:core-4.1-amd64:core-4.1-noarch:cxx-4.1-amd64:cxx-4.1-noarch:desktop-4.1-amd64:desktop-4.1-noarch:languages-4.1-amd64:languages-4.1-noarch:printing-4.1-amd64:printing-4.1-noarch
Distributor ID:	Fedora
Description:	Fedora release 25 (Twenty Five)
Release:	25
Codename:	TwentyFive
'''  # noqa

# FIXME: a
etc_lsb_release_ubuntu14 = '''DISTRIB_ID=Ubuntu
DISTRIB_RELEASE=14.04
DISTRIB_CODENAME=trusty
DISTRIB_DESCRIPTION="Ubuntu 14.04.3 LTS"
'''
etc_lsb_release_no_decimal = '''DISTRIB_ID=AwesomeOS
DISTRIB_RELEASE=11
DISTRIB_CODENAME=stonehenge
DISTRIB_DESCRIPTION="AwesomeÖS 11"
'''


class TestLSBFacts(BaseFactsTest):
    __test__ = True
    gather_subset = ['!all', 'lsb']
    valid_subsets = ['lsb']
    fact_namespace = 'ansible_lsb'
    collector_class = LSBFactCollector

    def _mock_module(self):
        mock_module = Mock()
        mock_module.params = {'gather_subset': self.gather_subset,
                              'gather_timeout': 10,
                              'filter': '*'}
        mock_module.get_bin_path = Mock(return_value='/usr/bin/lsb_release')
        mock_module.run_command = Mock(return_value=(0, lsb_release_a_fedora_output, ''))
        return mock_module

    def test_lsb_release_bin(self):
        module = self._mock_module()
        fact_collector = self.collector_class()
        facts_dict = fact_collector.collect(module=module)

        self.assertIsInstance(facts_dict, dict)
        self.assertEqual(facts_dict['lsb']['release'], '25')
        self.assertEqual(facts_dict['lsb']['id'], 'Fedora')
        self.assertEqual(facts_dict['lsb']['description'], 'Fedora release 25 (Twenty Five)')
        self.assertEqual(facts_dict['lsb']['codename'], 'TwentyFive')
        self.assertEqual(facts_dict['lsb']['major_release'], '25')

    def test_etc_lsb_release(self):
        module = self._mock_module()
        module.get_bin_path = Mock(return_value=None)
        with patch('ansible.module_utils.facts.system.lsb.os.path.exists',
                   return_value=True):
            with patch('ansible.module_utils.facts.system.lsb.get_file_lines',
                       return_value=etc_lsb_release_ubuntu14.splitlines()):
                fact_collector = self.collector_class()
                facts_dict = fact_collector.collect(module=module)

        self.assertIsInstance(facts_dict, dict)
        self.assertEqual(facts_dict['lsb']['release'], '14.04')
        self.assertEqual(facts_dict['lsb']['id'], 'Ubuntu')
        self.assertEqual(facts_dict['lsb']['description'], 'Ubuntu 14.04.3 LTS')
        self.assertEqual(facts_dict['lsb']['codename'], 'trusty')

    def test_etc_lsb_release_no_decimal_release(self):
        module = self._mock_module()
        module.get_bin_path = Mock(return_value=None)
        with patch('ansible.module_utils.facts.system.lsb.os.path.exists',
                   return_value=True):
            with patch('ansible.module_utils.facts.system.lsb.get_file_lines',
                       return_value=etc_lsb_release_no_decimal.splitlines()):
                fact_collector = self.collector_class()
                facts_dict = fact_collector.collect(module=module)

        self.assertIsInstance(facts_dict, dict)
        self.assertEqual(facts_dict['lsb']['release'], '11')
        self.assertEqual(facts_dict['lsb']['id'], 'AwesomeOS')
        self.assertEqual(facts_dict['lsb']['description'], 'AwesomeÖS 11')
        self.assertEqual(facts_dict['lsb']['codename'], 'stonehenge')
