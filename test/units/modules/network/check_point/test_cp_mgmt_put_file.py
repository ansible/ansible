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
from ansible.modules.network.check_point import cp_mgmt_put_file

PAYLOAD = {
    "targets": [
        "corporate-gateway"
    ],
    "file_path": "/home/admin/",
    "file_name": "vsx_conf",
    "file_content": "vs ip 192.0.2.1\nvs2 ip 192.0.2.2",
    "wait_for_task": False
}

RETURN_PAYLOAD = {
    "task-id": "53de74b7-8f19-4cbe-99fc-a81ef0759bad"
}

command = 'put-file'
failure_msg = '{command failed}'


class TestCheckpointPutFile(object):
    module = cp_mgmt_put_file

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)

    @pytest.fixture
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.module_utils.network.checkpoint.checkpoint.Connection')
        return connection_class_mock.return_value

    def test_command(self, mocker, connection_mock):
        connection_mock.send_request.return_value = (200, RETURN_PAYLOAD)
        result = self._run_module(PAYLOAD)

        assert result['changed']
        assert RETURN_PAYLOAD == result[command]

    def test_command_fail(self, mocker, connection_mock):
        connection_mock.send_request.return_value = (404, failure_msg)
        try:
            result = self._run_module(PAYLOAD)
        except Exception as e:
            result = e.args[0]

        assert 'Checkpoint device returned error 404 with message ' + failure_msg == result['msg']

    def _run_module(self, module_args):
        set_module_args(module_args)
        with pytest.raises(AnsibleExitJson) as ex:
            self.module.main()
        return ex.value.args[0]
