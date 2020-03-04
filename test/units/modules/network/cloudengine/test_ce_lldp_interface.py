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
from ansible.modules.network.cloudengine import ce_lldp_interface
from units.modules.network.cloudengine.ce_module import TestCloudEngineModule, load_fixture
from units.modules.utils import set_module_args


class TestCloudEngineLacpModule(TestCloudEngineModule):
    module = ce_lldp_interface

    def setUp(self):
        super(TestCloudEngineLacpModule, self).setUp()

        # self.mock_get_config = patch('ansible.modules.network.cloudengine.ce_lldp.get_nc_config')
        self.mock_get_config = patch('ansible.modules.network.cloudengine.ce_lldp_interface.get_nc_config')
        self.get_nc_config = self.mock_get_config.start()

        self.mock_set_nc_config = patch('ansible.modules.network.cloudengine.ce_lldp_interface.set_nc_config')
        self.set_nc_config = self.mock_set_nc_config.start()
        self.xml_absent = load_fixture('ce_lldp_interface', 'lldp_interface_existing.txt')
        self.xml_present = load_fixture('ce_lldp_interface', 'lldp_interface_changed.txt')
        self.result_ok = load_fixture('ce_lldp_interface', 'result_ok.txt')

    def tearDown(self):
        super(TestCloudEngineLacpModule, self).tearDown()
        self.mock_set_nc_config.stop()
        self.mock_get_config.stop()

    def test_lldp_present(self):
        self.get_nc_config.side_effect = (self.xml_absent, self.xml_present) * 5
        self.set_nc_config.return_value = self.result_ok
        config = dict(
            lldpenable='enabled',
            function_lldp_interface_flag='disableINTERFACE',
            type_tlv_disable='basic_tlv',
            type_tlv_enable='dot1_tlv',
            ifname='10GE1/0/1',
            lldpadminstatus='txOnly',
            manaddrtxenable=True,
            portdesctxenable=True,
            syscaptxenable=True,
            sysdesctxenable=True,
            sysnametxenable=True,
            portvlantxenable=True,
            protovlantxenable=True,
            txprotocolvlanid=True,
            vlannametxenable=True,
            txvlannameid=8,
            txinterval=8,
            protoidtxenable=True,
            macphytxenable=True,
            linkaggretxenable=True,
            maxframetxenable=True,
            eee=True,
            dcbx=True
        )
        set_module_args(config)
        result = self.execute_module(changed=True)

    def test_lldp_absent(self):
        self.get_nc_config.side_effect = (self.xml_present, self.xml_present, self.xml_absent, self.xml_absent)
        self.set_nc_config.return_value = self.result_ok
        config = dict(
            lldpenable='enabled',
            function_lldp_interface_flag='disableINTERFACE',
            type_tlv_disable='basic_tlv',
            type_tlv_enable='dot1_tlv',
            ifname='10GE1/0/1',
            lldpadminstatus='txOnly',
            manaddrtxenable=False,
            portdesctxenable=False,
            syscaptxenable=False,
            sysdesctxenable=False,
            sysnametxenable=False,
            portvlantxenable=False,
            protovlantxenable=False,
            txprotocolvlanid=False,
            vlannametxenable=False,
            txvlannameid=18,
            txinterval=18,
            protoidtxenable=False,
            macphytxenable=False,
            linkaggretxenable=False,
            maxframetxenable=False,
            eee=False,
            dcbx=False,
            state='absent'
        )
        set_module_args(config)
        result = self.execute_module(changed=False)
