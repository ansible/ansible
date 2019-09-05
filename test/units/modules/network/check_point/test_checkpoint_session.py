# Copyright (c) 2018 Red Hat
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
from ansible.modules.network.check_point import checkpoint_session

OBJECT = {'uid': '1234'}
PAYLOAD = {}


class TestCheckpointAccessRule(object):
    module = checkpoint_session

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        return mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)

    @pytest.fixture
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.modules.network.check_point.checkpoint_session.Connection')
        return connection_class_mock.return_value

    @pytest.fixture
    def get_session_200(self, mocker):
        mock_function = mocker.patch('ansible.modules.network.check_point.checkpoint_session.get_session')
        mock_function.return_value = (200, OBJECT)
        return mock_function.return_value

    def test_publish(self, get_session_200, connection_mock):
        connection_mock.send_request.return_value = (200, OBJECT)
        result = self._run_module(PAYLOAD)

        assert result['changed']
        assert 'checkpoint_session' in result

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
