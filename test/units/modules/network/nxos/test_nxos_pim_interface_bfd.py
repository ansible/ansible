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
from ansible.modules.network.nxos import nxos_pim_interface
from .nxos_module import TestNxosModule, set_module_args


class TestNxosPimInterfaceBfdModule(TestNxosModule):

    module = nxos_pim_interface

    def setUp(self):
        super(TestNxosPimInterfaceBfdModule, self).setUp()

        self.mock_get_interface_mode = patch('ansible.modules.network.nxos.nxos_pim_interface.get_interface_mode')
        self.get_interface_mode = self.mock_get_interface_mode.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_pim_interface.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_pim_interface.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_pim_interface.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestNxosPimInterfaceBfdModule, self).tearDown()
        self.mock_get_interface_mode.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def test_bfd_1(self):
        # default (None) -> enable
        self.get_config.return_value = None
        set_module_args(dict(interface='eth2/1', bfd='enable'))
        self.execute_module(
            changed=True,
            commands=[
                'interface eth2/1',
                'ip pim bfd-instance',
            ])

        # default (None) -> disable
        set_module_args(dict(interface='eth2/1', bfd='disable'))
        self.execute_module(
            changed=True,
            commands=[
                'interface eth2/1',
                'ip pim bfd-instance disable',
            ])

        # default (None) -> default (None) (idempotence)
        set_module_args(dict(interface='eth2/1', bfd='default'))
        self.execute_module(changed=False,)

        # default (None) -> interface state 'default'
        set_module_args(dict(interface='Ethernet9/3', state='default'))
        self.execute_module(changed=False,)

        # default (None) -> interface state 'absent'
        set_module_args(dict(interface='Ethernet9/3', state='absent'))
        self.execute_module(changed=False,)

    def test_bfd_2(self):
        # From disable
        self.get_config.return_value = '''
            interface Ethernet9/2
              ip pim bfd-instance disable
        '''
        # disable -> enable
        set_module_args(dict(interface='Ethernet9/2', bfd='enable'))
        self.execute_module(
            changed=True,
            commands=[
                'interface Ethernet9/2',
                'ip pim bfd-instance',
            ])

        # disable -> disable (idempotence)
        set_module_args(dict(interface='Ethernet9/2', bfd='disable'))
        self.execute_module(changed=False,)

        # disable -> default (None)
        set_module_args(dict(interface='Ethernet9/2', bfd='default'))
        self.execute_module(
            changed=True,
            commands=[
                'interface Ethernet9/2',
                'no ip pim bfd-instance',
            ])
        # disable -> interface state 'default'
        set_module_args(dict(interface='Ethernet9/3', state='default'))
        self.execute_module(
            changed=True,
            commands=[
                'interface Ethernet9/3',
                'no ip pim bfd-instance',
            ])

        # disable -> interface state 'absent'
        set_module_args(dict(interface='Ethernet9/3', state='absent'))
        self.execute_module(
            changed=True,
            commands=[
                'interface Ethernet9/3',
                'no ip pim bfd-instance',
            ])

    def test_bfd_3(self):
        # From enable
        self.get_config.return_value = '''
            interface Ethernet9/2
              ip pim bfd-instance
        '''
        # enable -> disabled
        set_module_args(dict(interface='Ethernet9/3', bfd='disable'))
        self.execute_module(
            changed=True,
            commands=[
                'interface Ethernet9/3',
                'ip pim bfd-instance disable',
            ])

        # enable -> enable (idempotence)
        set_module_args(dict(interface='Ethernet9/3', bfd='enable'))
        self.execute_module(changed=False,)

        # enable -> default (None)
        set_module_args(dict(interface='Ethernet9/3', bfd='default'))
        self.execute_module(
            changed=True,
            commands=[
                'interface Ethernet9/3',
                'no ip pim bfd-instance',
            ])

        # enable -> interface state 'default'
        set_module_args(dict(interface='Ethernet9/3', state='default'))
        self.execute_module(
            changed=True,
            commands=[
                'interface Ethernet9/3',
                'no ip pim bfd-instance',
            ])

        # enable -> interface state 'absent'
        set_module_args(dict(interface='Ethernet9/3', state='absent'))
        self.execute_module(
            changed=True,
            commands=[
                'interface Ethernet9/3',
                'no ip pim bfd-instance',
            ])
