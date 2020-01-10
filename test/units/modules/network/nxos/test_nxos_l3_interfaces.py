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

        self.mock_get_platform_type = patch('ansible.module_utils.network.nxos.config.l3_interfaces.l3_interfaces.L3_interfaces.get_platform_type')
        self.get_platform_type = self.mock_get_platform_type.start()

    def tearDown(self):
        super(TestNxosL3InterfacesModule, self).tearDown()
        self.mock_FACT_LEGACY_SUBSETS.stop()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_platform_type.stop()

    def load_fixtures(self, commands=None, device='N9K'):
        self.mock_FACT_LEGACY_SUBSETS.return_value = dict()
        self.get_resource_connection_config.return_value = None
        self.edit_config.return_value = None
        self.get_platform_type.return_value = device

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
        # basic tests
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
        replaced = ['interface Ethernet1/1', 'ip address 192.168.1.1/24',
                    'interface Ethernet1/2', 'no ip address']
        overridden = ['interface Ethernet1/1', 'ip address 192.168.1.1/24',
                      'interface Ethernet1/2', 'no ip address',
                      'interface Ethernet1/3', 'no ip address']

        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)

        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced)

        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

    def test_3(self):
        # encap testing
        existing = dedent('''\
          interface mgmt0
            ip address 10.0.0.254/24
          interface Ethernet1/1.41
            encapsulation dot1q 4100
            ip address 10.1.1.1/24
          interface Ethernet1/1.42
            encapsulation dot1q 42
          interface Ethernet1/1.44
            encapsulation dot1q 44
          interface Ethernet1/1.45
            encapsulation dot1q 45
            ip address 10.5.5.5/24
            ipv6 address 10::5/128
        ''')
        self.get_resource_connection_facts.return_value = {self.SHOW_CMD: existing}
        playbook = dict(config=[
            dict(name='Ethernet1/1.41', dot1q=41, ipv4=[{'address': '10.2.2.2/24'}]),
            dict(name='Ethernet1/1.42', dot1q=42),
            dict(name='Ethernet1/1.43', dot1q=43, ipv6=[{'address': '10::2/128'}]),
            dict(name='Ethernet1/1.44')
        ])
        # Expected result commands for each 'state'
        merged = [
            'interface Ethernet1/1.41', 'encapsulation dot1q 41', 'ip address 10.2.2.2/24',
            'interface Ethernet1/1.43', 'encapsulation dot1q 43', 'ipv6 address 10::2/128',
        ]
        deleted = [
            'interface Ethernet1/1.41', 'no encapsulation dot1q', 'no ip address',
            'interface Ethernet1/1.42', 'no encapsulation dot1q',
            'interface Ethernet1/1.44', 'no encapsulation dot1q'
        ]
        replaced = [
            'interface Ethernet1/1.41', 'encapsulation dot1q 41', 'ip address 10.2.2.2/24',
            # 42 no chg
            'interface Ethernet1/1.43', 'encapsulation dot1q 43', 'ipv6 address 10::2/128',
            'interface Ethernet1/1.44', 'no encapsulation dot1q'
        ]
        overridden = [
            'interface Ethernet1/1.41', 'encapsulation dot1q 41', 'ip address 10.2.2.2/24',
            # 42 no chg
            'interface Ethernet1/1.44', 'no encapsulation dot1q',
            'interface Ethernet1/1.45', 'no encapsulation dot1q', 'no ip address', 'no ipv6 address',
            'interface Ethernet1/1.43', 'encapsulation dot1q 43', 'ipv6 address 10::2/128'
        ]

        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)

        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced)

        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

    def test_4(self):
        # IPv4-centric testing
        existing = dedent('''\
          interface mgmt0
            ip address 10.0.0.254/24
          interface Ethernet1/1
            no ip redirects
            ip address 10.1.1.1/24 tag 11
            ip address 10.2.2.2/24 secondary tag 12
            ip address 10.3.3.3/24 secondary
            ip address 10.4.4.4/24 secondary tag 14
            ip address 10.5.5.5/24 secondary tag 15
            ip address 10.6.6.6/24 secondary tag 16
          interface Ethernet1/2
            ip address 10.12.12.12/24
          interface Ethernet1/3
            ip address 10.13.13.13/24
          interface Ethernet1/5
            no ip redirects
            ip address 10.15.15.15/24
            ip address 10.25.25.25/24 secondary
        ''')
        self.get_resource_connection_facts.return_value = {self.SHOW_CMD: existing}
        playbook = dict(config=[
            dict(name='Ethernet1/1',
                 ipv4=[{'address': '10.1.1.1/24', 'secondary': True},  # prim->sec
                       {'address': '10.2.2.2/24', 'secondary': True},  # rmv tag
                       {'address': '10.3.3.3/24', 'tag': 3},           # become prim
                       {'address': '10.4.4.4/24', 'secondary': True, 'tag': 14},  # no chg
                       {'address': '10.5.5.5/24', 'secondary': True, 'tag': 55},  # chg tag
                       {'address': '10.7.7.7/24', 'secondary': True, 'tag': 77}]),  # new ip
            dict(name='Ethernet1/2'),
            dict(name='Ethernet1/4',
                 ipv4=[{'address': '10.40.40.40/24'},
                       {'address': '10.41.41.41/24', 'secondary': True}]),
            dict(name='Ethernet1/5'),
        ])
        # Expected result commands for each 'state'
        merged = [
            'interface Ethernet1/1',
            'no ip address 10.5.5.5/24 secondary',
            'no ip address 10.2.2.2/24 secondary',
            'no ip address 10.3.3.3/24 secondary',
            'ip address 10.3.3.3/24 tag 3',  # Changes primary
            'ip address 10.1.1.1/24 secondary',
            'ip address 10.2.2.2/24 secondary',
            'ip address 10.7.7.7/24 secondary tag 77',
            'ip address 10.5.5.5/24 secondary tag 55',
            'interface Ethernet1/4',
            'ip address 10.40.40.40/24',
            'ip address 10.41.41.41/24 secondary'
        ]
        deleted = [
            'interface Ethernet1/1', 'no ip address',
            'interface Ethernet1/2', 'no ip address',
            'interface Ethernet1/5', 'no ip address'
        ]
        replaced = [
            'interface Ethernet1/1',
            'no ip address 10.5.5.5/24 secondary',
            'no ip address 10.2.2.2/24 secondary',
            'no ip address 10.3.3.3/24 secondary',
            'ip address 10.3.3.3/24 tag 3',  # Changes primary
            'ip address 10.1.1.1/24 secondary',
            'ip address 10.2.2.2/24 secondary',
            'ip address 10.7.7.7/24 secondary tag 77',
            'ip address 10.5.5.5/24 secondary tag 55',
            'interface Ethernet1/2',
            'no ip address',
            'interface Ethernet1/4',
            'ip address 10.40.40.40/24',
            'ip address 10.41.41.41/24 secondary',
            'interface Ethernet1/5',
            'no ip address'
        ]
        overridden = [
            'interface Ethernet1/1',
            'no ip address 10.6.6.6/24 secondary',
            'no ip address 10.5.5.5/24 secondary',
            'no ip address 10.2.2.2/24 secondary',
            'no ip address 10.3.3.3/24 secondary',
            'ip address 10.3.3.3/24 tag 3',  # Changes primary
            'ip address 10.1.1.1/24 secondary',
            'ip address 10.2.2.2/24 secondary',
            'ip address 10.7.7.7/24 secondary tag 77',
            'ip address 10.5.5.5/24 secondary tag 55',
            'interface Ethernet1/2',
            'no ip address',
            'interface Ethernet1/3',
            'no ip address',
            'interface Ethernet1/4',
            'ip address 10.40.40.40/24',
            'ip address 10.41.41.41/24 secondary',
            'interface Ethernet1/5',
            'no ip address',
        ]

        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)

        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced)

        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

    def test_5(self):
        # IPv6-centric testing
        existing = dedent('''\
          interface Ethernet1/1
            ipv6 address 10::1/128
            ipv6 address 10::2/128 tag 12
            ipv6 address 10::3/128 tag 13
            ipv6 address 10::4/128 tag 14
          interface Ethernet1/2
            ipv6 address 10::12/128
          interface Ethernet1/3
            ipv6 address 10::13/128
        ''')
        self.get_resource_connection_facts.return_value = {self.SHOW_CMD: existing}
        playbook = dict(config=[
            dict(name='Ethernet1/1',
                 ipv6=[{'address': '10::1/128'},               # no chg
                       {'address': '10::3/128'},               # tag rmv
                       {'address': '10::4/128', 'tag': 44},    # tag chg
                       {'address': '10::5/128'},               # new addr
                       {'address': '10::6/128', 'tag': 66}]),  # new addr+tag
            dict(name='Ethernet1/2'),
        ])
        # Expected result commands for each 'state'
        merged = [
            'interface Ethernet1/1',
            'ipv6 address 10::4/128 tag 44',
            'ipv6 address 10::5/128',
            'ipv6 address 10::6/128 tag 66',
        ]
        deleted = [
            'interface Ethernet1/1', 'no ipv6 address',
            'interface Ethernet1/2', 'no ipv6 address',
        ]
        replaced = [
            'interface Ethernet1/1',
            'no ipv6 address 10::3/128',
            'no ipv6 address 10::2/128',
            'ipv6 address 10::4/128 tag 44',
            'ipv6 address 10::3/128',
            'ipv6 address 10::5/128',
            'ipv6 address 10::6/128 tag 66',
            'interface Ethernet1/2',
            'no ipv6 address 10::12/128'
        ]
        overridden = [
            'interface Ethernet1/1',
            'no ipv6 address 10::3/128',
            'no ipv6 address 10::2/128',
            'ipv6 address 10::4/128 tag 44',
            'ipv6 address 10::3/128',
            'ipv6 address 10::5/128',
            'ipv6 address 10::6/128 tag 66',
            'interface Ethernet1/2',
            'no ipv6 address 10::12/128',
            'interface Ethernet1/3',
            'no ipv6 address'
        ]

        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)
        #
        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced)
        #
        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

    def test_6(self):
        # misc tests
        existing = dedent('''\
          interface Ethernet1/1
            ip address 10.1.1.1/24
            no ip redirects
            ip unreachables
          interface Ethernet1/2
          interface Ethernet1/3
          interface Ethernet1/4
          interface Ethernet1/5
            no ip redirects
        ''')
        self.get_resource_connection_facts.return_value = {self.SHOW_CMD: existing}
        playbook = dict(config=[
            dict(name='Ethernet1/1', redirects=True, unreachables=False,
                 ipv4=[{'address': '192.168.1.1/24'}]),
            dict(name='Ethernet1/2'),
            dict(name='Ethernet1/3', redirects=True, unreachables=False),  # defaults
            dict(name='Ethernet1/4', redirects=False, unreachables=True),
        ])
        merged = [
            'interface Ethernet1/1',
            'ip redirects',
            'no ip unreachables',
            'ip address 192.168.1.1/24',
            'interface Ethernet1/4',
            'no ip redirects',
            'ip unreachables'
        ]
        deleted = [
            'interface Ethernet1/1',
            'ip redirects',
            'no ip unreachables',
            'no ip address'
        ]
        replaced = [
            'interface Ethernet1/1',
            'ip redirects',
            'no ip unreachables',
            'ip address 192.168.1.1/24',
            'interface Ethernet1/4',
            'no ip redirects',
            'ip unreachables'
        ]
        overridden = [
            'interface Ethernet1/1',
            'ip redirects',
            'no ip unreachables',
            'ip address 192.168.1.1/24',
            'interface Ethernet1/5',
            'ip redirects',
            'interface Ethernet1/4',
            'no ip redirects',
            'ip unreachables'
        ]

        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=merged)

        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)

        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced)

        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden)

    def test_7(self):
        # idempotence
        existing = dedent('''\
          interface Ethernet1/1
            ip address 10.1.1.1/24
            ip address 10.2.2.2/24 secondary tag 2
            ip address 10.3.3.3/24 secondary tag 3
            ip address 10.4.4.4/24 secondary
            ipv6 address 10::1/128
            ipv6 address 10::2/128 tag 2
            no ip redirects
            ip unreachables
          interface Ethernet1/2
        ''')
        self.get_resource_connection_facts.return_value = {self.SHOW_CMD: existing}
        playbook = dict(config=[
            dict(name='Ethernet1/1', redirects=False, unreachables=True,
                 ipv4=[{'address': '10.1.1.1/24'},
                       {'address': '10.2.2.2/24', 'secondary': True, 'tag': 2},
                       {'address': '10.3.3.3/24', 'secondary': True, 'tag': 3},
                       {'address': '10.4.4.4/24', 'secondary': True}],
                 ipv6=[{'address': '10::1/128'},
                       {'address': '10::2/128', 'tag': 2}]),
            dict(name='Ethernet1/2')
        ])
        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=False)

        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=False)

        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=False)

        # Modify output for deleted idempotence test
        existing = dedent('''\
          interface Ethernet1/1
          interface Ethernet1/2
        ''')
        self.get_resource_connection_facts.return_value = {self.SHOW_CMD: existing}
        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=False)

    def test_8(self):
        # no 'config' key in playbook
        existing = dedent('''\
          interface Ethernet1/1
            ip address 10.1.1.1/24
        ''')
        self.get_resource_connection_facts.return_value = {self.SHOW_CMD: existing}
        playbook = dict()

        for i in ['merged', 'replaced', 'overridden']:
            playbook['state'] = i
            set_module_args(playbook, ignore_provider_arg)
            self.execute_module(failed=True)

        deleted = [
            'interface Ethernet1/1',
            'no ip address',
        ]
        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted)

    def test_9(self):
        # Platform specific checks
        # 'ip redirects' has platform-specific behaviors
        existing = dedent('''\
          interface mgmt0
            ip address 10.0.0.254/24
          interface Ethernet1/3
            ip address 10.13.13.13/24
          interface Ethernet1/5
            no ip redirects
            ip address 10.15.15.15/24
            ip address 10.25.25.25/24 secondary
        ''')
        self.get_resource_connection_facts.return_value = {self.SHOW_CMD: existing}
        playbook = dict(config=[
            dict(name='Ethernet1/3'),
            dict(name='Ethernet1/5'),
        ])
        # Expected result commands for each 'state'
        deleted = [
            'interface Ethernet1/3', 'no ip address',
            'interface Ethernet1/5', 'no ip address', 'ip redirects'
        ]
        replaced = [
            'interface Ethernet1/3', 'no ip address',
            'interface Ethernet1/5', 'no ip address', 'ip redirects'
        ]
        overridden = [
            'interface Ethernet1/3', 'no ip address',
            'interface Ethernet1/5', 'no ip address', 'ip redirects'
        ]
        platform = 'N3K'

        playbook['state'] = 'merged'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=False, device=platform)

        playbook['state'] = 'deleted'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=deleted, device=platform)

        playbook['state'] = 'replaced'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=replaced, device=platform)

        playbook['state'] = 'overridden'
        set_module_args(playbook, ignore_provider_arg)
        self.execute_module(changed=True, commands=overridden, device=platform)
