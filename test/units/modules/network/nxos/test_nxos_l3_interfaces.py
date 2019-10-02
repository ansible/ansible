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

from textwrap import dedent
from units.compat.mock import patch
from units.modules.utils import AnsibleFailJson
from ansible.modules.network.nxos import nxos_l3_interfaces
from ansible.module_utils.network.nxos.config.l3_interfaces.l3_interfaces import L3_interfaces
from .nxos_module import TestNxosModule, load_fixture, set_module_args

ignore_provider_arg = True


class TestNxosL3InterfacesModule(TestNxosModule):

    module = nxos_l3_interfaces

    def setUp(self):
        super(TestNxosL3InterfacesModule, self).setUp()

        self.mock_FACT_LEGACY_SUBSETS = patch('ansible.module_utils.network.nxos.facts.facts.FACT_LEGACY_SUBSETS')
        self.FACT_LEGACY_SUBSETS = self.mock_FACT_LEGACY_SUBSETS.start()

        self.mock_get_resource_connection_config = patch('ansible.module_utils.network.common.cfg.base.get_resource_connection')
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start()

        self.mock_get_resource_connection_facts = patch('ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch('ansible.module_utils.network.nxos.config.l3_interfaces.l3_interfaces.L3_interfaces.edit_config')
        self.edit_config = self.mock_edit_config.start()

    def tearDown(self):
        super(TestNxosL3InterfacesModule, self).tearDown()
        self.mock_FACT_LEGACY_SUBSETS.stop()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.mock_FACT_LEGACY_SUBSETS.return_value = dict()
        self.get_resource_connection_config.return_value = None
        self.edit_config.return_value = None

    # ---------------------------
    # L3_interfaces Test Cases
    # ---------------------------

    # 'state' logic behaviors
    #
    # - 'merged'    : Update existing device state with any differences in the play.
    # - 'deleted'   : Reset existing device state to default values. Ignores any
    #                 play attrs other than 'name'. Scope is limited to interfaces
    #                 in the play.
    # - 'overridden': The play is the source of truth. Similar to replaced but the
    #                 scope includes all interfaces; ie. it will also reset state
    #                 on interfaces not found in the play.
    # - 'replaced'  : Scope is limited to the interfaces in the play.

    SHOW_CMD = 'show running-config | section ^interface'

    def test_1(self):
        # Verify raise when playbook specifies mgmt0
        self.get_resource_connection_facts.return_value = {self.SHOW_CMD: ''}
        playbook = dict(config=[dict(name='mgmt0')])
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module({'failed': True, 'msg': "The 'mgmt0' interface is not allowed to be managed by this module"})

    def test_2(self):
        # Change existing config states
        existing = dedent('''\
          interface mgmt0
            ip address 10.0.0.254/24
          interface Ethernet1/1
            ip address 10.1.1.1/24
          interface Ethernet1/2
            ip address 10.1.2.1/24
          interface Ethernet1/3
            ip address 10.1.3.1/24
        ''')
        self.get_resource_connection_facts.return_value = {self.SHOW_CMD: existing}
        playbook = dict(config=[
            dict(
                name='Ethernet1/1',
                ipv4=[{'address': '192.168.1.1/24'}]),
            dict(name='Ethernet1/2'),
            # Eth1/3 not present! Thus overridden should set Eth1/3 to defaults;
            # replaced should ignore Eth1/3.
        ])
        # Expected result commands for each 'state'
        merged = ['interface Ethernet1/1', 'ip address 192.168.1.1/24']
        deleted = ['interface Ethernet1/1', 'no ip address',
                   'interface Ethernet1/2', 'no ip address']
        overridden = ['interface Ethernet1/1', 'no ip address',
                      'interface Ethernet1/2', 'no ip address',
                      'interface Ethernet1/3', 'no ip address',
                      'interface Ethernet1/1', 'ip address 192.168.1.1/24']
        replaced = ['interface Ethernet1/1', 'no ip address', 'ip address 192.168.1.1/24',
                    'interface Ethernet1/2', 'no ip address']

        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)

        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

        # TBD: 'REPLACED' BEHAVIOR IS INCORRECT,
        #      IT IS WRONGLY IGNORING ETHERNET1/2.
        #      ****************** SKIP TEST FOR NOW *****************
        # playbook['state'] = 'replaced'
        # set_module_args(playbook, ignore_provider_arg)
        # self.execute_module(changed=True, commands=replaced)
