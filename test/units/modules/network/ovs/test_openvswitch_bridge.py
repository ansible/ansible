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
from ansible.modules.network.ovs import openvswitch_bridge
from units.modules.utils import set_module_args
from .ovs_module import TestOpenVSwitchModule, load_fixture

test_name_side_effect_matrix = {
    'test_openvswitch_bridge_absent_idempotent': [
        (0, '', '')],
    'test_openvswitch_bridge_absent_removes_bridge': [
        (0, 'list_br_test_br.cfg', ''),
        (0, '', ''),
        (0, '', ''),
        (0, '', ''),
        (0, '', ''),
        (0, '', '')],
    'test_openvswitch_bridge_present_idempotent': [
        (0, 'list_br_test_br.cfg', ''),
        (0, 'br_to_parent_test_br.cfg', ''),
        (0, 'br_to_vlan_zero.cfg', ''),
        (0, 'get_fail_mode_secure.cfg', ''),
        (0, 'br_get_external_id_foo_bar.cfg', '')],
    'test_openvswitch_bridge_present_creates_bridge': [
        (0, '', ''),
        (0, '', ''),
        (0, '', ''),
        (0, '', '')],
    'test_openvswitch_bridge_present_creates_fake_bridge': [
        (0, '', ''),
        (0, '', ''),
        (0, '', ''),
        (0, '', '')],
    'test_openvswitch_bridge_present_adds_external_id': [
        (0, 'list_br_test_br.cfg', ''),
        (0, 'br_to_parent_test_br.cfg', ''),
        (0, 'br_to_vlan_zero.cfg', ''),
        (0, 'get_fail_mode_secure.cfg', ''),
        (0, 'br_get_external_id_foo_bar.cfg', ''),
        (0, '', '')],
    'test_openvswitch_bridge_present_clears_external_id': [
        (0, 'list_br_test_br.cfg', ''),
        (0, 'br_to_parent_test_br.cfg', ''),
        (0, 'br_to_vlan_zero.cfg', ''),
        (0, 'get_fail_mode_secure.cfg', ''),
        (0, 'br_get_external_id_foo_bar.cfg', ''),
        (0, '', '')],
    'test_openvswitch_bridge_present_changes_fail_mode': [
        (0, 'list_br_test_br.cfg', ''),
        (0, 'br_to_parent_test_br.cfg', ''),
        (0, 'br_to_vlan_zero.cfg', ''),
        (0, 'get_fail_mode_secure.cfg', ''),
        (0, 'br_get_external_id_foo_bar.cfg', ''),
        (0, '', '')],
    'test_openvswitch_bridge_present_runs_set_mode': [
        (0, '', ''),
        (0, '', ''),
        (0, '', ''),
        (0, '', '')],
}


class TestOpenVSwitchBridgeModule(TestOpenVSwitchModule):

    module = openvswitch_bridge

    def setUp(self):
        super(TestOpenVSwitchBridgeModule, self).setUp()

        self.mock_run_command = (
            patch('ansible.module_utils.basic.AnsibleModule.run_command'))
        self.run_command = self.mock_run_command.start()
        self.mock_get_bin_path = (
            patch('ansible.module_utils.basic.AnsibleModule.get_bin_path'))
        self.get_bin_path = self.mock_get_bin_path.start()

    def tearDown(self):
        super(TestOpenVSwitchBridgeModule, self).tearDown()

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

    def test_openvswitch_bridge_absent_idempotent(self):
        set_module_args(dict(state='absent',
                             bridge='test-br'))
        self.execute_module(test_name='test_openvswitch_bridge_absent_idempotent')

    def test_openvswitch_bridge_absent_removes_bridge(self):
        set_module_args(dict(state='absent',
                             bridge='test-br'))
        commands = ['/usr/bin/ovs-vsctl -t 5 del-br test-br']
        self.execute_module(changed=True, commands=commands,
                            test_name='test_openvswitch_bridge_absent_removes_bridge')

    def test_openvswitch_bridge_present_idempotent(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             fail_mode='secure',
                             external_ids={'foo': 'bar'}))
        self.execute_module(test_name='test_openvswitch_bridge_present_idempotent')

    def test_openvswitch_bridge_present_creates_bridge(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             fail_mode='secure',
                             external_ids={'foo': 'bar'}))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 add-br test-br',
            '/usr/bin/ovs-vsctl -t 5 set-fail-mode test-br secure',
            '/usr/bin/ovs-vsctl -t 5 br-set-external-id test-br foo bar'
        ]
        self.execute_module(changed=True, commands=commands,
                            test_name='test_openvswitch_bridge_present_creates_bridge')

    def test_openvswitch_bridge_present_creates_fake_bridge(self):
        set_module_args(dict(state='present',
                             bridge='test-br2',
                             parent='test-br',
                             vlan=10))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 add-br test-br2 test-br 10',
        ]
        self.execute_module(changed=True, commands=commands,
                            test_name='test_openvswitch_bridge_present_creates_fake_bridge')

    def test_openvswitch_bridge_present_adds_external_id(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             fail_mode='secure',
                             external_ids={'bip': 'bop'}))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 br-set-external-id test-br bip bop'
        ]
        self.execute_module(changed=True, commands=commands,
                            test_name='test_openvswitch_bridge_present_adds_external_id')

    def test_openvswitch_bridge_present_clears_external_id(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             fail_mode='secure',
                             external_ids={'foo': ''}))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 br-set-external-id test-br foo '
        ]
        self.execute_module(changed=True, commands=commands,
                            test_name='test_openvswitch_bridge_present_clears_external_id')

    def test_openvswitch_bridge_present_changes_fail_mode(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             fail_mode='standalone',
                             external_ids={'foo': 'bar'}))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 set-fail-mode test-br standalone'
        ]
        self.execute_module(changed=True, commands=commands,
                            test_name='test_openvswitch_bridge_present_changes_fail_mode')

    def test_openvswitch_bridge_present_runs_set_mode(self):
        set_module_args(dict(state='present',
                             bridge='test-br',
                             fail_mode='secure',
                             external_ids={'foo': 'bar'},
                             set="bridge test-br datapath_type=netdev"))
        commands = [
            '/usr/bin/ovs-vsctl -t 5 add-br test-br -- set bridge test-br'
            ' datapath_type=netdev',
            '/usr/bin/ovs-vsctl -t 5 set-fail-mode test-br secure',
            '/usr/bin/ovs-vsctl -t 5 br-set-external-id test-br foo bar'
        ]
        self.execute_module(changed=True, commands=commands,
                            test_name='test_openvswitch_bridge_present_runs_set_mode')
