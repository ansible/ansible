# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <https://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import pytest
from mock import ANY
from ansible.module_utils.network.fortios.fortios import FortiOSHandler

try:
    from ansible.modules.network.fortios import fortios_system_firmware_upgrade
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_system_firmware_upgrade.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_system_firmware_upgrade_execute(mocker):
    execute_method_result = {'status': 'success', 'http_method': 'POST', 'http_status': 200}
    execute_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.execute', return_value=execute_method_result)

    input_data = {
        'username': 'admin',
        'system_firmware': {
            'file_content': 'test_value_3',
            'filename': 'test_value_4',
            'format_partition': 'test_value_5',
            'source': 'upload'
        },
        'vdom': 'root'}

    is_error, changed, response = fortios_system_firmware_upgrade.fortios_system(input_data, fos_instance)

    expected_data = {
        'file-content': 'test_value_3',
        'filename': 'test_value_4',
        'format-partition': 'test_value_5',
        'source': 'upload'
    }

    execute_method_mock.assert_called_with('system', 'firmware/upgrade', data=ANY, vdom='root')
    assert not is_error
    assert changed
    assert response['status'] == 'success'
    assert response['http_status'] == 200
