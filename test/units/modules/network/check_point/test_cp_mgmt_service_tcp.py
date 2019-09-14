# Ansible module to manage CheckPoint Firewall (c) 2019
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from units.modules.utils import set_module_args, exit_json, fail_json, AnsibleExitJson

from ansible.module_utils import basic
from ansible.modules.network.check_point import cp_mgmt_service_tcp

OBJECT = {
    "name": "New_TCP_Service_1",
    "port": 5669,
    "keep_connections_open_after_policy_installation": False,
    "session_timeout": 0,
    "match_for_any": True,
    "sync_connections_on_cluster": True,
    "aggressive_aging": {
        "enable": True,
        "timeout": 360,
        "use_default_timeout": False
    }
}

CREATE_PAYLOAD = {
    "name": "New_TCP_Service_1",
    "port": 5669,
    "keep_connections_open_after_policy_installation": False,
    "session_timeout": 0,
    "match_for_any": True,
    "sync_connections_on_cluster": True,
    "aggressive_aging": {
        "enable": True,
        "timeout": 360,
        "use_default_timeout": False
    }
}

UPDATE_PAYLOAD = {
    "name": "New_TCP_Service_1",
    "color": "blue",
    "port": 5656,
    "aggressive_aging": {
        "default_timeout": 3600
    }
}

OBJECT_AFTER_UPDATE = UPDATE_PAYLOAD

DELETE_PAYLOAD = {
    "name": "New_TCP_Service_1",
    "state": "absent"
}

function_path = 'ansible.modules.network.check_point.cp_mgmt_service_tcp.api_call'
api_call_object = 'service-tcp'


class TestCheckpointServiceTcp(object):
    module = cp_mgmt_service_tcp

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)

    @pytest.fixture
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.module_utils.network.checkpoint.checkpoint.Connection')
        return connection_class_mock.return_value

    def test_create(self, mocker, connection_mock):
        mock_function = mocker.patch(function_path)
        mock_function.return_value = {'changed': True, api_call_object: OBJECT}
        result = self._run_module(CREATE_PAYLOAD)

        assert result['changed']
        assert OBJECT.items() == result[api_call_object].items()

    def test_create_idempotent(self, mocker, connection_mock):
        mock_function = mocker.patch(function_path)
        mock_function.return_value = {'changed': False, api_call_object: OBJECT}
        result = self._run_module(CREATE_PAYLOAD)

        assert not result['changed']

    def test_update(self, mocker, connection_mock):
        mock_function = mocker.patch(function_path)
        mock_function.return_value = {'changed': True, api_call_object: OBJECT_AFTER_UPDATE}
        result = self._run_module(UPDATE_PAYLOAD)

        assert result['changed']
        assert OBJECT_AFTER_UPDATE.items() == result[api_call_object].items()

    def test_update_idempotent(self, mocker, connection_mock):
        mock_function = mocker.patch(function_path)
        mock_function.return_value = {'changed': False, api_call_object: OBJECT_AFTER_UPDATE}
        result = self._run_module(UPDATE_PAYLOAD)

        assert not result['changed']

    def test_delete(self, mocker, connection_mock):
        mock_function = mocker.patch(function_path)
        mock_function.return_value = {'changed': True}
        result = self._run_module(DELETE_PAYLOAD)

        assert result['changed']

    def test_delete_idempotent(self, mocker, connection_mock):
        mock_function = mocker.patch(function_path)
        mock_function.return_value = {'changed': False}
        result = self._run_module(DELETE_PAYLOAD)

        assert not result['changed']

    def _run_module(self, module_args):
        set_module_args(module_args)
        with pytest.raises(AnsibleExitJson) as ex:
            self.module.main()
        return ex.value.args[0]
