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

from ansible.modules.network.ovs import openvswitch_db
from units.compat.mock import patch, MagicMock
from units.modules.utils import set_module_args
from .ovs_module import TestOpenVSwitchModule, load_fixture

import pytest


@pytest.fixture
def patched_openvswitch_db(monkeypatch):
    mocked_ovs_db = MagicMock()
    mocked_ovs_db.return_value = {'table': 'open_vswitch',
                                  'record': '.',
                                  'col': 'other_config',
                                  'key': 'pmd-cpu-mask',
                                  'value': '0xaaa00000000'}
    monkeypatch.setattr(openvswitch_db, 'map_config_to_obj', mocked_ovs_db)
    return openvswitch_db


test_name_side_effect_matrix = {
    'test_openvswitch_db_absent_idempotent': [
        (0, 'openvswitch_db_disable_in_band_missing.cfg', None),
        (0, None, None)],
    'test_openvswitch_db_absent_removes_key': [
        (0, 'openvswitch_db_disable_in_band_true.cfg', None),
        (0, None, None)],
    'test_openvswitch_db_present_idempotent': [
        (0, 'openvswitch_db_disable_in_band_true.cfg', None),
        (0, None, None)],
    'test_openvswitch_db_present_idempotent_value': [
        (0, None, None)],
    'test_openvswitch_db_present_adds_key': [
        (0, 'openvswitch_db_disable_in_band_missing.cfg', None),
        (0, None, None)],
    'test_openvswitch_db_present_updates_key': [
        (0, 'openvswitch_db_disable_in_band_true.cfg', None),
        (0, None, None)],
    'test_openvswitch_db_present_missing_key_on_map': [
        (0, 'openvswitch_db_disable_in_band_true.cfg', None),
        (0, None, None)],
    'test_openvswitch_db_present_stp_enable': [
        (0, 'openvswitch_db_disable_in_band_true.cfg', None),
        (0, None, None)],
}


class TestOpenVSwitchDBModule(TestOpenVSwitchModule):

    module = openvswitch_db

    def setUp(self):
        super(TestOpenVSwitchDBModule, self).setUp()

        self.mock_run_command = (
            patch('ansible.module_utils.basic.AnsibleModule.run_command'))
        self.run_command = self.mock_run_command.start()
        self.mock_get_bin_path = (
            patch('ansible.module_utils.basic.AnsibleModule.get_bin_path'))
        self.get_bin_path = self.mock_get_bin_path.start()

    def tearDown(self):
        super(TestOpenVSwitchDBModule, self).tearDown()

        self.mock_run_command.stop()
        self.mock_get_bin_path.stop()

    def load_fixtures(self, test_name):
        test_side_effects = []
        for s in test_name_side_effect_matrix[test_name]:
            rc = s[0]
            out = load_fixture(s[1]) if s[1] else None
            err = s[2]
            side_effect_with_fixture_loaded = (rc, out, err)
            test_side_effects.append(side_effect_with_fixture_loaded)
        self.run_command.side_effect = test_side_effects

        self.get_bin_path.return_value = '/usr/bin/ovs-vsctl'

    def test_openvswitch_db_absent_idempotent(self):
        set_module_args(dict(state='absent',
                             table='Bridge', record='test-br',
                             col='other_config', key='disable-in-band',
                             value='true'))
        self.execute_module(test_name='test_openvswitch_db_absent_idempotent')

    def test_openvswitch_db_absent_removes_key(self):
        set_module_args(dict(state='absent',
                             table='Bridge', record='test-br',
                             col='other_config', key='disable-in-band',
                             value='true'))
        self.execute_module(
            changed=True,
            commands=['/usr/bin/ovs-vsctl -t 5 remove Bridge test-br other_config'
                      ' disable-in-band=true'],
            test_name='test_openvswitch_db_absent_removes_key')

    def test_openvswitch_db_present_idempotent(self):
        set_module_args(dict(state='present',
                             table='Bridge', record='test-br',
                             col='other_config', key='disable-in-band',
                             value='true'))
        self.execute_module(test_name='test_openvswitch_db_present_idempotent')

    @pytest.mark.usefixtures('patched_openvswitch_db')
    def test_openvswitch_db_present_idempotent_value(self):
        set_module_args({"col": "other_config",
                         "key": "pmd-cpu-mask",
                         "record": ".",
                         "table": "open_vswitch",
                         "value": "0xaaa00000000"})
        self.execute_module(test_name='test_openvswitch_db_present_idempotent_value')

    def test_openvswitch_db_present_adds_key(self):
        set_module_args(dict(state='present',
                             table='Bridge', record='test-br',
                             col='other_config', key='disable-in-band',
                             value='true'))
        self.execute_module(
            changed=True,
            commands=['/usr/bin/ovs-vsctl -t 5 set Bridge test-br other_config'
                      ':disable-in-band=true'],
            test_name='test_openvswitch_db_present_adds_key')

    def test_openvswitch_db_present_updates_key(self):
        set_module_args(dict(state='present',
                             table='Bridge', record='test-br',
                             col='other_config', key='disable-in-band',
                             value='false'))
        self.execute_module(
            changed=True,
            commands=['/usr/bin/ovs-vsctl -t 5 set Bridge test-br other_config'
                      ':disable-in-band=false'],
            test_name='test_openvswitch_db_present_updates_key')

    def test_openvswitch_db_present_missing_key_on_map(self):
        set_module_args(dict(state='present',
                             table='Bridge', record='test-br',
                             col='other_config',
                             value='false'))
        self.execute_module(
            failed=True,
            test_name='test_openvswitch_db_present_missing_key_on_map')

    def test_openvswitch_db_present_stp_enable(self):
        set_module_args(dict(state='present',
                             table='Bridge', record='test-br',
                             col='stp_enable',
                             value='true'))
        self.execute_module(changed=True,
                            test_name='test_openvswitch_db_present_stp_enable')
