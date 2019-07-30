# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.frr import frr_facts
from units.modules.utils import set_module_args
from .frr_module import TestFrrModule, load_fixture


class TestFrrFactsModule(TestFrrModule):

    module = frr_facts

    def setUp(self):
        super(TestFrrFactsModule, self).setUp()
        self.mock_run_commands = patch('ansible.modules.network.frr.frr_facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_get_capabilities = patch('ansible.modules.network.frr.frr_facts.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {
            'device_info': {
                'network_os': 'frr',
                'network_os_hostname': 'rtr1',
                'network_os_version': '6.0',
            },
            'supported_protocols': {
                'ldp': False
            },
            'network_api': 'cliconf'
        }

    def tearDown(self):
        super(TestFrrFactsModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            commands = kwargs['commands']
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('frr_facts_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_frr_facts_default(self):
        set_module_args(dict(gather_subset='default'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_hostname'], 'rtr1'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_version'], '6.0'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_system'], 'frr'
        )

    def test_frr_facts_interfaces(self):
        set_module_args(dict(gather_subset='interfaces'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['eth0']['macaddress'], 'fa:16:3e:d4:32:b2'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['eth1']['macaddress'], 'fa:16:3e:95:88:f7'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['eth0']['ipv4'], [{"address": "192.168.1.8",
                                                                                 "subnet": "24"}]
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_interfaces']['eth0']['ipv6'], [{"address": "fe80::f816:3eff:fed4:32b2",
                                                                                 "subnet": "64"}]
        )
        self.assertEqual(
            sorted(result['ansible_facts']['ansible_net_all_ipv4_addresses']), sorted(["192.168.1.19",
                                                                                       "192.168.1.18",
                                                                                       "192.168.1.21",
                                                                                       "192.168.1.8"])
        )
        self.assertEqual(
            sorted(result['ansible_facts']['ansible_net_all_ipv6_addresses']), sorted(["fe80::f816:3eff:fe95:88f7",
                                                                                       "3ffe:506::1",
                                                                                       "3ffe:504::1",
                                                                                       "fe80::f816:3eff:fed4:32b2"])
        )

    def test_frr_facts_hardware(self):
        set_module_args(dict(gather_subset='hardware'))
        result = self.execute_module()

        self.assertEqual(
            result['ansible_facts']['ansible_net_mem_stats']["zebra"]['total_heap_allocated'], '4200 KiB'
        )

        self.assertEqual(
            result['ansible_facts']['ansible_net_mem_stats']["ripd"]['total_heap_allocated'], '936 KiB'
        )

        self.assertEqual(
            result['ansible_facts']['ansible_net_mem_stats']["ripd"]['used_ordinary_blocks'], '901 KiB'
        )

        self.assertEqual(
            result['ansible_facts']['ansible_net_mem_stats']["ripd"]['holding_block_headers'], '0 bytes'
        )
