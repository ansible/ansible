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
from ansible.modules.network.cloudengine import ce_lldp
from units.modules.network.cloudengine.ce_module import TestCloudEngineModule, load_fixture
from units.modules.utils import set_module_args


class TestCloudEngineLacpModule(TestCloudEngineModule):
    module = ce_lldp

    def setUp(self):
        super(TestCloudEngineLacpModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.cloudengine.ce_lldp.get_nc_config')
        self.get_nc_config = self.mock_get_config.start()

        self.mock_set_config = patch('ansible.modules.network.cloudengine.ce_lldp.set_nc_config')
        self.set_nc_config = self.mock_set_config.start()
        self.set_nc_config.return_value = None
        xml_existing_1 = load_fixture('ce_lldp', 'ce_lldp_global_00.txt')
        xml_existing_2 = load_fixture('ce_lldp', 'ce_lldp_global_01.txt')
        xml_end_state_1 = load_fixture('ce_lldp', 'ce_lldpSysParameter_00.txt')
        xml_end_state_2 = load_fixture('ce_lldp', 'ce_lldpSysParameter_01.txt')
        self.get_side_effect = (xml_existing_1, xml_existing_2, xml_end_state_1, xml_end_state_2)
        self.result_ok = load_fixture('ce_lldp', 'result_ok.txt')

    def tearDown(self):
        super(TestCloudEngineLacpModule, self).tearDown()
        self.mock_set_config.stop()
        self.mock_get_config.stop()

    def test_lldp_global_present(self):
        update = ['lldp enable',
                  'lldp mdn enable',
                  'lldp mdn enable',
                  'lldp transmit interval 8',
                  'lldp transmit multiplier 8',
                  'lldp restart 8',
                  'lldp transmit delay 8',
                  'lldp trap-interval 8',
                  'lldp fast-count 8',
                  'lldp mdn trap-interval 8',
                  'lldp management-address 1.1.1.1',
                  'lldp management-address bind interface bind-name']
        self.get_nc_config.side_effect = self.get_side_effect
        self.set_nc_config.side_effect = [self.result_ok] * 11
        set_module_args(dict(
            lldpenable='enabled',
            mdnstatus='rxOnly',
            interval=8,
            hold_multiplier=8,
            restart_delay=8,
            transmit_delay=8,
            notification_interval=8,
            fast_count=8,
            mdn_notification_interval=8,
            management_address='1.1.1.1',
            bind_name='bind-name')
        )
        result = self.execute_module(changed=True)
        self.assertEqual(sorted(result['updates']), sorted(update))

    def test_lacp_sys_parameter_present(self):
        update = ['lldp enable',
                  'lldp mdn enable',
                  'lldp mdn enable',
                  'lldp transmit interval 8',
                  'lldp transmit multiplier 8',
                  'lldp restart 8',
                  'lldp transmit delay 8',
                  'lldp trap-interval 8',
                  'lldp fast-count 8',
                  'lldp mdn trap-interval 8',
                  'lldp management-address 1.1.1.1',
                  'lldp management-address bind interface bind-name']
        self.get_nc_config.side_effect = self.get_side_effect
        self.set_nc_config.side_effect = [self.result_ok] * 11
        set_module_args(dict(
            lldpenable='enabled',
            mdnstatus='rxOnly',
            interval=8,
            hold_multiplier=8,
            restart_delay=8,
            transmit_delay=8,
            notification_interval=8,
            fast_count=8,
            mdn_notification_interval=8,
            management_address='1.1.1.1',
            bind_name='bind-name')
        )
        result = self.execute_module(changed=True)
        self.assertEqual(sorted(result['updates']), sorted(update))
