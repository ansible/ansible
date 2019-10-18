#
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
from ansible.modules.network.ovs import openvswitch_port
from units.modules.utils import set_module_args
from .ovs_module import TestOpenVSwitchModule, load_fixture

test_name_side_effect_matrix = {
    'test_openvswitch_port_absent_idempotent': [
        (0, '', '')],
    'test_openvswitch_port_absent_removes_port': [
        (0, 'list_ports_test_br.cfg', ''),
        (0, 'get_port_eth2_tag.cfg', ''),
        (0, 'get_port_eth2_external_ids.cfg', ''),
        (0, '', '')],
    'test_openvswitch_port_present_idempotent': [
        (0, 'list_ports_test_br.cfg', ''),
        (0, 'get_port_eth2_tag.cfg', ''),
        (0, 'get_port_eth2_external_ids.cfg', ''),
        (0, '', '')],
    'test_openvswitch_port_present_creates_port': [
        (0, '', ''),
        (0, '', ''),
        (0, '', '')],
    'test_openvswitch_port_present_changes_tag': [
        (0, 'list_ports_test_br.cfg', ''),
        (0, 'get_port_eth2_tag.cfg', ''),
        (0, 'get_port_eth2_external_ids.cfg', ''),
        (0, '', '')],
    'test_openvswitch_port_present_changes_external_id': [
        (0, 'list_ports_test_br.cfg', ''),
        (0, 'get_port_eth2_tag.cfg', ''),
        (0, 'get_port_eth2_external_ids.cfg', ''),
        (0, '', '')],
    'test_openvswitch_port_present_adds_external_id': [
        (0, 'list_ports_test_br.cfg', ''),
        (0, 'get_port_eth2_tag.cfg', ''),
        (0, 'get_port_eth2_external_ids.cfg', ''),
        (0, '', '')],
    'test_openvswitch_port_present_clears_external_id': [
        (0, 'list_ports_test_br.cfg', ''),
        (0, 'get_port_eth2_tag.cfg', ''),
        (0, 'get_port_eth2_external_ids.cfg', ''),
        (0, '', '')],
    'test_openvswitch_port_present_runs_set_mode': [
        (0, '', ''),
        (0, '', ''),
        (0, '', '')],
}


class TestOpenVSwitchPortModule(TestOpenVSwitchModule):

    module = openvswitch_port

    def setUp(self):
        super(TestOpenVSwitchPortModule, self).setUp()

        self.mock_run_command = (
            patch('ansible.module_utils.basic.AnsibleModule.run_command'))
        self.run_command = self.mock_run_command.start()
        self.mock_get_bin_path = (
            patch('ansible.module_utils.basic.AnsibleModule.get_bin_path'))
        self.get_bin_path = self.mock_get_bin_path.start()

    def tearDown(self):
        super(TestOpenVSwitchPortModule, self).tearDown()

        self.mock_run_command.stop()
        self.mock_get_bin_path.stop()

    def load_fixtures(self, test_name):
        test_side_effects = []
        for s in test_name_side_effect_matrix[test_name]:
            rc = s[0]
            out = s[1] if s[1] == '' else str(load_fixture(s[1]))
            err = s[2]
            side_effect_with_fixture_loaded = (rc, out, err)
            test_side_effects.append(side_effect_with_fixture_loaded)
        self.run_command.side_effect = test_side_effects

        self.get_bin_path.return_value = '/usr/bin/ovs-vsctl'

    def test_openvswitch_port_absent_idempotent(self):
        set_module_args(dict(state='absent',
                             bridge='test-br',
                             port='eth2'))
        self.execute_module(test_name='test_openvswitch_port_absent_idempotent')

    def test_openvswitch_port_absent_removes_port(self):
        set_module_args(dict(state='absent',
                             bridge='test-br',
                             port='eth2'))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 del-port test-br eth2',
        ]
        self.execute_module(changed=True, commands=commands,
                            test_name='test_openvswitch_port_absent_removes_port')

    def test_openvswitch_port_present_idempotent(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             port='eth2',
                             tag=10,
                             external_ids={'foo': 'bar'}))
        self.execute_module(test_name='test_openvswitch_port_present_idempotent')

    def test_openvswitch_port_present_creates_port(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             port='eth2',
                             tag=10,
                             external_ids={'foo': 'bar'}))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 add-port test-br eth2 tag=10',
            '/usr/bin/ovs-vsctl -t 5 set port eth2 external_ids:foo=bar'
        ]
        self.execute_module(changed=True,
                            commands=commands,
                            test_name='test_openvswitch_port_present_creates_port')

    def test_openvswitch_port_present_changes_tag(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             port='eth2',
                             tag=20,
                             external_ids={'foo': 'bar'}))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 set port eth2 tag=20'
        ]
        self.execute_module(changed=True,
                            commands=commands,
                            test_name='test_openvswitch_port_present_changes_tag')

    def test_openvswitch_port_present_changes_external_id(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             port='eth2',
                             tag=10,
                             external_ids={'foo': 'baz'}))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 set port eth2 external_ids:foo=baz'
        ]
        self.execute_module(changed=True,
                            commands=commands,
                            test_name='test_openvswitch_port_present_changes_external_id')

    def test_openvswitch_port_present_adds_external_id(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             port='eth2',
                             tag=10,
                             external_ids={'foo2': 'bar2'}))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 set port eth2 external_ids:foo2=bar2'
        ]
        self.execute_module(changed=True,
                            commands=commands,
                            test_name='test_openvswitch_port_present_adds_external_id')

    def test_openvswitch_port_present_clears_external_id(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             port='eth2',
                             tag=10,
                             external_ids={'foo': None}))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 remove port eth2 external_ids foo'
        ]
        self.execute_module(changed=True,
                            commands=commands,
                            test_name='test_openvswitch_port_present_clears_external_id')

    def test_openvswitch_port_present_runs_set_mode(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             port='eth2',
                             tag=10,
                             external_ids={'foo': 'bar'},
                             set="port eth2 other_config:stp-path-cost=10"))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 add-port test-br eth2 tag=10 -- set'
            ' port eth2 other_config:stp-path-cost=10',
            '/usr/bin/ovs-vsctl -t 5 set port eth2 external_ids:foo=bar'
        ]
        self.execute_module(changed=True, commands=commands,
                            test_name='test_openvswitch_port_present_runs_set_mode')
