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

import json

from units.compat.mock import patch
from ansible.modules.network.nxos import nxos_vlan
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosVlanModule(TestNxosModule):

    module = nxos_vlan

    def setUp(self):
        super(TestNxosVlanModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_vlan.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_vlan.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_vlan.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_get_capabilities = patch('ansible.modules.network.nxos.nxos_vlan.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {'device_info': {'network_os_platform': 'N9K-9000v'}, 'network_api': 'cliconf'}

    def tearDown(self):
        super(TestNxosVlanModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_load_config.stop()
        self.mock_get_config.stop()
        self.mock_get_capabilities.stop()

    def load_fixtures(self, commands=None, device=''):
        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for item in commands:
                try:
                    obj = json.loads(item)
                    command = obj['command']
                except ValueError:
                    command = item
                filename = '%s.txt' % str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('nxos_vlan', filename))
            return output

        def agg_load_from_file(*args, **kwargs):
            """Load vlan output for aggregate/purge tests"""
            return([load_fixture('nxos_vlan', 'agg_show_vlan_brief.txt')])

        if '_agg_' in self._testMethodName:
            self.run_commands.side_effect = agg_load_from_file
        else:
            self.run_commands.side_effect = load_from_file

        self.load_config.return_value = None
        self.get_config.return_value = load_fixture('nxos_vlan', 'config.cfg')

    def test_nxos_vlan_agg_1(self):
        # Aggregate: vlan 4/5 exist -> Add 6
        set_module_args(dict(aggregate=[
            {'name': '_5_', 'vlan_id': 5},
            {'name': '_6_', 'vlan_id': 6}
        ]))
        self.execute_module(changed=True, commands=[
            'vlan 6',
            'name _6_',
            'state active',
            'no shutdown',
            'exit'
        ])

    def test_nxos_vlan_agg_2(self):
        # Aggregate: vlan 4/5 exist -> Add none (idempotence)
        set_module_args(dict(aggregate=[
            {'name': '_5_', 'vlan_id': 5},
            {'name': '_4_', 'vlan_id': 4}
        ]))
        self.execute_module(changed=False)

    def test_nxos_vlan_agg_3(self):
        # Aggregate/Purge: vlan 4/5 exist -> Add 6, Purge 4
        set_module_args(dict(aggregate=[
            {'name': '_5_', 'vlan_id': 5},
            {'name': '_6_', 'vlan_id': 6}
        ], purge=True))
        self.execute_module(changed=True, commands=[
            'vlan 6',
            'name _6_',
            'state active',
            'no shutdown',
            'exit',
            'no vlan 4'
        ])

    def test_nxos_vlan_agg_4(self):
        # Aggregate/Purge: vlan 4/5 exist -> Purge None (idempotence)
        set_module_args(dict(aggregate=[
            {'name': '_5_', 'vlan_id': 5},
            {'name': '_4_', 'vlan_id': 4}
        ]))
        self.execute_module(changed=False)

    def test_nxos_vlan_agg_5(self):
        # Purge with Single Vlan: vlan 4/5 exist -> Add 6, Purge 4/5
        set_module_args(dict(vlan_id=6, name='_6_', purge=True))
        self.execute_module(changed=True, commands=[
            'vlan 6',
            'name _6_',
            'state active',
            'no shutdown',
            'exit',
            'no vlan 4',
            'no vlan 5'
        ])

    def test_nxos_vlan_agg_6(self):
        # Purge All: vlan 4/5 exist -> Purge 4/5
        set_module_args(dict(vlan_id=1, purge=True))
        self.execute_module(changed=True, commands=[
            'no vlan 4',
            'no vlan 5'
        ])

    def test_nxos_vlan_range(self):
        set_module_args(dict(vlan_range='6-10'))
        self.execute_module(changed=True, commands=['vlan 6', 'vlan 7', 'vlan 8', 'vlan 9', 'vlan 10'])

    def test_nxos_vlan_range_absent(self):
        set_module_args(dict(vlan_range='1-5', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['no vlan 1'])

    def test_nxos_vlan_id(self):
        set_module_args(dict(vlan_id='15', state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vlan 15', 'state active', 'no shutdown', 'exit'])

    def test_nxos_vlan_id_absent(self):
        set_module_args(dict(vlan_id='1', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['no vlan 1'])

    def test_nxos_vlan_named_vlan(self):
        set_module_args(dict(vlan_id='15', name='WEB'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vlan 15', 'name WEB', 'state active', 'no shutdown', 'exit'])

    def test_nxos_vlan_shut_down(self):
        set_module_args(dict(vlan_id='1', admin_state='down'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vlan 1', 'shutdown', 'exit'])

    def test_nxos_vlan_no_change(self):
        set_module_args(dict(vlan_id='1', name='default', vlan_state='active', admin_state='up'))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])
