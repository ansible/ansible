# (c) 2016 Red Hat Inc.
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
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosIPInterfaceModule(TestNxosModule):

    module = nxos_pim_interface

    def setUp(self):
        super(TestNxosIPInterfaceModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_pim_interface.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_pim_interface.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_pim_interface.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestNxosIPInterfaceModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None, device=''):
        module_name = self.module.__name__.rsplit('.', 1)[1]

        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for command in commands:
                if type(command) == dict:
                    command = command['command']
                filename = str(command).split(' | ')[0].replace(' ', '_').replace('/', '_')
                output.append(load_fixture(module_name, filename))
            return output

        self.get_config.return_value = load_fixture(module_name, 'config.cfg')
        self.load_config.return_value = None
        self.run_commands.side_effect = load_from_file

    def test_nxos_pim_interface_present(self):
        set_module_args(dict(interface='eth2/1', dr_prio=10, hello_interval=40, sparse=True, border=False))
        self.execute_module(
            changed=True,
            commands=[
                'interface eth2/1', 'ip pim dr-priority 10', 'ip pim hello-interval 40000',
                'ip pim sparse-mode']
        )

    def test_nxos_pim_interface_jp(self):
        set_module_args(dict(
            interface='eth2/1', jp_policy_in='JPIN', jp_policy_out='JPOUT',
            jp_type_in='routemap', jp_type_out='routemap',
        ))
        self.execute_module(
            changed=True,
            commands=['interface eth2/1', 'ip pim jp-policy JPOUT out',
                      'ip pim jp-policy JPIN in']
        )

    def test_nxos_pim_interface_default(self):
        set_module_args(dict(interface='eth2/1', state='default'))
        self.execute_module(
            changed=False,
            commands=[]
        )

    def test_nxos_pim_interface_ip_absent(self):
        set_module_args(dict(interface='eth2/1', state='absent'))
        self.execute_module(changed=False, commands=[])
