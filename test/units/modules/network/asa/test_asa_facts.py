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
from ansible.modules.network.asa import asa_facts
from ansible.module_utils.six import assertCountEqual
from units.modules.utils import set_module_args
from .asa_module import TestAsaModule, load_fixture


class TestAsaFactsModule(TestAsaModule):

    module = asa_facts

    def setUp(self):
        super(TestAsaFactsModule, self).setUp()
        self.mock_run_commands = patch('ansible.module_utils.network.asa.facts.legacy.base.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_get_resource_connection = patch('ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection = self.mock_get_resource_connection.start()

        self.mock_get_capabilities = patch('ansible.module_utils.network.asa.facts.legacy.base.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {
            'device_info': {
                'network_os': 'asa',
                'network_os_hostname': 'ciscoasa',
                'network_os_image': 'flash0:/vasa-adventerprisek9-m',
                'network_os_version': '9.10(1)11'
            },
            'network_api': 'cliconf'
        }

    def tearDown(self):
        super(TestAsaFactsModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            module = args
            commands = kwargs['commands']
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('asa_facts_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_asa_facts_stacked(self):
        set_module_args(dict(gather_subset='default'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_serialnum'], '9AWFX1S46VQ'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_system'], 'asa'
        )

    def test_asa_facts_filesystems_info(self):
        set_module_args(dict(gather_subset='hardware'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_filesystems_info']['disk0:']['spacetotal_kb'], 8370192.0
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_filesystems_info']['disk0:']['spacefree_kb'], 8348976.0
        )
