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
from ansible.module_utils.network.checkpoint.checkpoint import api_command
from ansible.modules.network.check_point import cp_mgmt_install_policy

function_path = 'ansible.modules.network.check_point.cp_mgmt_install_policy.api_command'
OBJECT = {'name': 'test_network', 'nat_settings': {'auto_rule': True,
                                                   'hide_behind': 'ip-address',
                                                   'ip_address': '192.168.1.111'},
          'subnet': '192.0.2.1', 'subnet_mask': '255.255.255.0', 'state': 'present'}

PAYLOAD = {
    "policy-package": "standard",
    "access": True,
    "threat-prevention": True,
    "targets": ["corporate-gateway"]
}

command = 'install-policy'


class TestCheckpointNetwork(object):
    module = cp_mgmt_install_policy

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)

    @pytest.fixture
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.module_utils.network.checkpoint.checkpoint.Connection')
        return connection_class_mock.return_value

    @pytest.fixture
    def get_network_404(self, mocker):
        mock_function = mocker.patch(function_path)
        mock_function.return_value = (404, 'Object not found')
        return mock_function.return_value

    def test_install_policy(self, mocker, connection_mock):
        mock_function = mocker.patch(function_path)
        mock_function.return_value = {'changed': True, command: OBJECT}
        connection_mock.api_call.return_value = {'changed': True, command: OBJECT}
        result = self._run_module(PAYLOAD)

        assert result['changed']
        assert command in result

    def _run_module(self, module_args):
        set_module_args(module_args)
        with pytest.raises(AnsibleExitJson) as ex:
            self.module.main()
        return ex.value.args[0]
