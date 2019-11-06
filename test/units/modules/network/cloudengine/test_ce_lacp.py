# (c) 2019 Red Hat Inc.
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

from units.compat.mock import patch
from ansible.modules.network.cloudengine import ce_lacp
from units.modules.utils import set_module_args
from .ce_module import TestCloudEngineModule, load_fixture


class TestCloudEngineLacpModule(TestCloudEngineModule):
    module = ce_lacp

    def setUp(self):
        super(TestCloudEngineLacpModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.cloudengine.ce_lacp.get_nc_config')
        self.get_nc_config = self.mock_get_config.start()

        self.mock_set_config = patch('ansible.modules.network.cloudengine.ce_lacp.set_nc_config')
        self.set_nc_config = self.mock_set_config.start()
        self.set_nc_config.return_value = None

    def tearDown(self):
        super(TestCloudEngineLacpModule, self).tearDown()
        self.mock_set_config.stop()
        self.mock_get_config.stop()

    def test_lacp_eturnk_present(self):
        xml_existing = load_fixture('ce_lacp', 'ce_lacp_00.txt')
        xml_end_state = load_fixture('ce_lacp', 'ce_lacp_01.txt')
        update = ['lacp max active-linknumber 13',
                  'lacp dampening state-flapping',
                  'lacp port-id-extension enable',
                  'lacp collector delay 12',
                  'lacp preempt enable',
                  'lacp system-id 0000-1111-2222',
                  'lacp mixed-rate link enable',
                  'lacp preempt delay 130',
                  'lacp timeout user-defined 10',
                  'lacp dampening unexpected-mac disable']
        self.get_nc_config.side_effect = (xml_existing, xml_end_state)
        set_module_args(dict(
                        mode='Dynamic',
                        trunk_id='10',
                        preempt_enable='true',
                        state_flapping='true',
                        port_id_extension_enable='true',
                        unexpected_mac_disable='true',
                        system_id='0000-1111-2222',
                        timeout_type='Fast',
                        fast_timeout='10',
                        mixed_rate_link_enable='true',
                        preempt_delay=11,
                        collector_delay=12,
                        max_active_linknumber=13,
                        select='Speed',
                        state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(sorted(result['updates']), sorted(update))

    def test_lacp_eturnk_absent(self):
        xml_existing = load_fixture('ce_lacp', 'ce_lacp_10.txt')
        xml_end_state = load_fixture('ce_lacp', 'ce_lacp_00.txt')
        default_values = ['undo lacp priority',
                          'lacp timeout Fast',
                          'lacp max active-linknumber 1',
                          'lacp collector delay 0',
                          'lacp preempt enable false',
                          'lacp dampening state-flapping false',
                          'lacp dampening unexpected-mac disable false',
                          'lacp mixed-rate link enable false',
                          'lacp port-id-extension enable false',
                          'lacp preempt delay 30',
                          'lacp select Speed',
                          'lacp system-id 11-22-33',
                          'lacp timeout user-defined 3']
        self.get_nc_config.side_effect = (xml_existing, xml_end_state)
        set_module_args(dict(
                        mode='Dynamic',
                        trunk_id='10',
                        preempt_enable='true',
                        state_flapping='true',
                        port_id_extension_enable='true',
                        unexpected_mac_disable='true',
                        system_id='0000-1111-2222',
                        timeout_type='Fast',
                        fast_timeout='10',
                        mixed_rate_link_enable='true',
                        preempt_delay=11,
                        collector_delay=12,
                        max_active_linknumber=13,
                        select='Speed',
                        state='absent'
                        ))
        result = self.execute_module(changed=True)
        self.assertEqual(sorted(result['updates']), sorted(default_values))

    def test_lacp_global_present(self):
        xml_existing = load_fixture('ce_lacp', 'ce_lacp_10.txt')
        xml_end_state = load_fixture('ce_lacp', 'ce_lacp_11.txt')
        self.get_nc_config.side_effect = (xml_existing, xml_end_state)
        set_module_args(dict(global_priority=32769,
                             state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['updates'], ['lacp priority 32769'])

    def test_lacp_global_absent(self):
        xml_existing = load_fixture('ce_lacp', 'ce_lacp_11.txt')
        xml_end_state = load_fixture('ce_lacp', 'ce_lacp_10.txt')
        self.get_nc_config.side_effect = (xml_existing, xml_end_state)
        set_module_args(dict(global_priority=32769,
                             state='absent'))
        result = self.execute_module(changed=True)
        # excpect: lacp priority is set to default value(32768)
        self.assertEqual(result['updates'], ['lacp priority 32768'])
