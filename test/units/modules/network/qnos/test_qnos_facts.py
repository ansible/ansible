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

from units.compat.mock import patch, MagicMock
from ansible.modules.network.qnos import qnos_facts
from ansible.plugins.cliconf.qnos import Cliconf
from ansible.module_utils.six import assertCountEqual
from units.modules.utils import set_module_args
from .qnos_module import TestQnosModule, load_fixture

class TestQnosFactsModule(TestQnosModule):

    module = qnos_facts

    def setUp(self):
        super(TestQnosFactsModule, self).setUp()
        self.mock_run_commands = patch('ansible.modules.network.qnos.qnos_facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.cliconf_obj = Cliconf(MagicMock())

        self.mock_get_device_info = MagicMock(return_value=self.cliconf_obj.get_device_info())
        self.get_device_info = self.mock_get_device_info.start()
        self.get_device_info.return_value = {
            'network_os': 'qnos',
            'network_os_hostname': 'an-qnos-01',
            'network_os_model': 'QUANTA LY9',
            'network_os_version': '18.12'
        }

    def tearDown(self):
        super(TestQnosFactsModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_get_device_info.stop()

    def load_fixtures(self, commands=None):

        def load_from_file(*args, **kwargs):
            module = args
            commands = kwargs['commands']
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                filename = str(filename).replace('/', '_')
                output.append(load_fixture('qnos_facts_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_qnos_facts_stacked(self):
        set_module_args(dict(gather_subset='default'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_model'], 'QUANTA LY9'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_serialnum'], 'QTFCNB6100010'
        )


    def test_qnos_facts_tunnel_address(self):
        set_module_args(dict(gather_subset='interfaces'))
        result = self.execute_module()

        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['port'][0]['0/2']['macaddress'], '54:AB:3A:64:F7:FA'
        )


    def test_qnos_facts_neighbors(self):
        set_module_args(dict(gather_subset='interfaces'))
        result = self.execute_module()

        assertCountEqual(
            self,
            result['ansible_facts']['ansible_net_neighbors'].keys(), ['0/1', '0/2']
        )
        assertCountEqual(
            self,
            result['ansible_facts']['ansible_net_neighbors']['0/1'],
            [{'host': 'Switch1', 'port': '0/1', 'chassis_id':'00:01:02:03:04:05'}]
        )
        assertCountEqual(
            self,
            result['ansible_facts']['ansible_net_neighbors']['0/2'],
            [{'host': 'Switch2', 'port': '0/1', 'chassis_id':'00:02:02:03:04:05'}]
        )
