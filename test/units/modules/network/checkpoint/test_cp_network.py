# Copyright (c) 2019 Red Hat
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
#

from __future__ import absolute_import

import pytest
from units.modules.utils import set_module_args, exit_json, fail_json, AnsibleFailJson, AnsibleExitJson

from ansible.module_utils import basic
from ansible.module_utils.network.checkpoint.checkpoint import api_call
from ansible.modules.network.checkpoint import cp_network


OBJECT = {'name': 'test_network', 'nat_settings': {'auto-rule': True,
                                                   'hide-behind': 'ip-address',
                                                   'ip-address': '192.168.1.111'},
          'subnet': '192.0.2.1', 'subnet_mask': '255.255.255.0', 'state': 'present'}

CREATE_PAYLOAD = {'name': 'test_network', 'nat_settings': {'auto-rule': True,
                                                           'hide-behind': 'ip-address',
                                                           'ip-address': '192.168.1.111'},
                  'subnet': '192.168.1.0', 'subnet_mask': '255.255.255.0', 'state': 'present'}

UPDATE_PAYLOAD = {'name': 'test_new_network', 'nat_settings': {'auto-rule': True,
                                                               'hide-behind': 'ip-address',
                                                               'ip-address': '192.168.1.111'},
                  'subnet': '192.168.1.0', 'subnet_mask': '255.255.255.0', 'state': 'present'}

DELETE_PAYLOAD = {'name': 'test_new_network', 'state': 'absent'}


class TestCheckpointNetwork(object):
    module = cp_network

    checkpoint_argument_spec_for_objects = dict(
        auto_publish_session=dict(type='bool'),
        wait_for_task=dict(type='bool', default=True),
        state=dict(type='str', required=True, choices=['present', 'absent']),
        version=dict(type='str')
    )

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)

    @pytest.fixture
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.module_utils.network.checkpoint.checkpoint.Connection')
        return connection_class_mock.return_value

    @pytest.fixture
    def get_network_404(self, mocker):
        mock_function = mocker.patch('ansible.modules.network.checkpoint.cp_network.api_call')
        mock_function.return_value = (404, 'Object not found')
        return mock_function.return_value

    def test_network_create(self, mocker, connection_mock):
        mock_function = mocker.patch('ansible.modules.network.checkpoint.cp_network.api_call')
        mock_function.return_value = {'changed': True, 'network': OBJECT}
        connection_mock.api_call.return_value = {'changed': True, 'network': OBJECT}
        result = self._run_module(CREATE_PAYLOAD)

        assert result['changed']
        assert 'network' in result

    def test_network_create_idempotent(self, mocker, connection_mock):
        mock_function = mocker.patch('ansible.modules.network.checkpoint.cp_network.api_call')
        mock_function.return_value = {'changed': False, 'network': OBJECT}
        connection_mock.send_request.return_value = (200, OBJECT)
        result = self._run_module(CREATE_PAYLOAD)

        assert not result['changed']

    def test_network_update(self, mocker, connection_mock):
        mock_function = mocker.patch('ansible.modules.network.checkpoint.cp_network.api_call')
        mock_function.return_value = {'changed': True, 'network': OBJECT}
        connection_mock.send_request.return_value = (200, OBJECT)
        result = self._run_module(UPDATE_PAYLOAD)

        assert result['changed']

    def test_network_delete(self, mocker, connection_mock):
        mock_function = mocker.patch('ansible.modules.network.checkpoint.cp_network.api_call')
        mock_function.return_value = {'changed': True}
        connection_mock.send_request.return_value = (200, OBJECT)
        result = self._run_module(DELETE_PAYLOAD)

        assert result['changed']

    def test_network_delete_idempotent(self, mocker, connection_mock):
        mock_function = mocker.patch('ansible.modules.network.checkpoint.cp_network.api_call')
        mock_function.return_value = {'changed': False}
        connection_mock.send_request.return_value = (200, OBJECT)
        result = self._run_module(DELETE_PAYLOAD)

        assert not result['changed']

    def _run_module(self, module_args):
        set_module_args(module_args)
        with pytest.raises(AnsibleExitJson) as ex:
            self.module.main()
        return ex.value.args[0]

    def _run_module_with_fail_json(self, module_args):
        set_module_args(module_args)
        with pytest.raises(AnsibleFailJson) as exc:
            self.module.main()
        result = exc.value.args[0]
        return result
