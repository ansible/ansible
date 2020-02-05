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
from ansible.modules.network.cloudengine import ce_static_route_bfd
from units.modules.network.cloudengine.ce_module import TestCloudEngineModule, load_fixture
from units.modules.utils import set_module_args


class TestCloudEngineLacpModule(TestCloudEngineModule):
    module = ce_static_route_bfd

    def setUp(self):
        super(TestCloudEngineLacpModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.cloudengine.ce_static_route_bfd.get_nc_config')
        self.get_nc_config = self.mock_get_config.start()

        self.mock_set_config = patch('ansible.modules.network.cloudengine.ce_static_route_bfd.set_nc_config')
        self.set_nc_config = self.mock_set_config.start()
        self.set_nc_config.return_value = load_fixture('ce_lldp', 'result_ok.txt')

    def tearDown(self):
        super(TestCloudEngineLacpModule, self).tearDown()
        self.mock_set_config.stop()
        self.mock_get_config.stop()

    def test_ce_static_route_bfd_changed_false(self):
        srBfdPara_1 = load_fixture('ce_static_route_bfd', 'srBfdPara_1.txt')
        staticrtbase_1 = load_fixture('ce_static_route_bfd', 'staticrtbase_1.txt')
        self.get_nc_config.side_effect = (srBfdPara_1, srBfdPara_1, staticrtbase_1, staticrtbase_1)

        config = dict(
            prefix='255.255.0.0',
            mask=22,
            aftype='v4',
            next_hop='10.10.1.1',
            nhp_interface='10GE1/0/1',
            vrf='mgnt',
            destvrf='_public_',
            tag=23,
            description='for a test',
            pref='22',
            function_flag='dynamicBFD',
            min_tx_interval='32',
            min_rx_interval='23',
            detect_multiplier='24',
            bfd_session_name='43'
        )
        set_module_args(config)
        self.execute_module(changed=False)

    def test_ce_static_route_bfd_changed_true(self):
        srBfdPara_1 = load_fixture('ce_static_route_bfd', 'srBfdPara_1.txt')
        srBfdPara_2 = load_fixture('ce_static_route_bfd', 'srBfdPara_2.txt')
        staticrtbase_1 = load_fixture('ce_static_route_bfd', 'staticrtbase_1.txt')
        staticrtbase_2 = load_fixture('ce_static_route_bfd', 'staticrtbase_2.txt')
        self.get_nc_config.side_effect = (srBfdPara_1, staticrtbase_1, srBfdPara_2, staticrtbase_2)
        updates = ['ip route-static vpn-instance mgnt 255.255.0.0 255.255.252.0 10GE1/0/1 10.10.1.1',
                   ' preference 22',
                   ' tag 23',
                   ' track bfd-session 43',
                   ' description for a test']
        config = dict(
            prefix='255.255.0.0',
            mask=22,
            aftype='v4',
            next_hop='10.10.1.1',
            nhp_interface='10GE1/0/1',
            vrf='mgnt',
            destvrf='_public_',
            tag=23,
            description='for a test',
            pref='22',
            function_flag='dynamicBFD',
            min_tx_interval='32',
            min_rx_interval='23',
            detect_multiplier='24',
            bfd_session_name='43'
        )
        set_module_args(config)
        result = self.execute_module(changed=True)
        self.assertEqual(sorted(result['updates']), sorted(updates))
