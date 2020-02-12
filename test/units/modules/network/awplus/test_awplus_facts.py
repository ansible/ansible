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
from ansible.modules.network.awplus import awplus_facts
from ansible.module_utils.six import assertCountEqual
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusFactsModule(TestAwplusModule):
    module = awplus_facts

    def setUp(self):
        super(TestAwplusModule, self).setUp()
        self.mock_run_commands = patch(
            'ansible.module_utils.network.awplus.facts.legacy.base.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_get_resource_connection = patch(
            'ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection = self.mock_get_resource_connection.start()

        self.mock_get_capabilities = patch(
            'ansible.module_utils.network.awplus.facts.legacy.base.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {
            'device_info': {
                'network_os': 'awplus',
                'network_os_hostname': 'AR2050',
                'network_os_model': 'AR2050V',
                'network_os_image': 'flash:/default.cfg',
                'network_os_version': 'main-20191128-1'
            },
            'network_api': 'cliconf'
        }

    def tearDown(self):
        super(TestAwplusFactsModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            module = args
            commands = kwargs['commands']
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('awplus_facts_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_awplus_facts_filesystems_info(self):
        set_module_args(dict(gather_subset='hardware'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_filesystems_info']['debug']["spacetotal"], "10M"
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_filesystems_info']['debug']["spacefree"], "9.7M"
        )

    def test_awplus_facts_neighbors(self):
        pass

    def test_awplus_facts_hostname(self):
        set_module_args(dict(gather_subset='default'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_hostname'], 'AR2050'
        )

    def test_awplus_all_ipv4_address(self):
        set_module_args(dict(gather_subset='interfaces'))
        result = self.execute_module()
        self.assertEqual(
            len(result['ansible_facts']['ansible_net_all_ipv4_addresses']), 1
        )

    def test_awplus_interfaces(self):
        set_module_args(dict(gather_subset='interfaces'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['br0']['type'], 'Bridge'
        )

        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['eth1']['operstatus'], 'DOWN'
        )

        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['port1.0.1']['macaddress'], "001a.eb94.27bb"
        )
