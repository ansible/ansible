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
from units.modules.utils import exit_json, fail_json
from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils.network.fortios.fortios import FortiOSHandler

try:
    from ansible.module_utils.network.fortios.facts.facts import Facts
    from ansible.modules.network.fortios import fortios_facts
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortios.fortios_facts.Connection')
    return connection_class_mock


fos_instance = FortiOSHandler(connection_mock)


def test_facts_get(mocker):
    monitor_method_result = {'status': 'success', 'http_method': 'GET', 'http_status': 200}
    monitor_method_mock = mocker.patch('ansible.module_utils.network.fortios.fortios.FortiOSHandler.monitor', return_value=monitor_method_result)
    mock_module = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
    mock_module._connection = connection_mock

    # test case 01, args with single gather_subset
    args = {
        'vdom': 'root',
        'gather_subset': [
            {'fact': 'system_status_select'},
        ]
    }
    mock_module.params = args

    response, ignore = Facts(mock_module, fos_instance).get_facts()

    monitor_method_mock.assert_called_with('system', 'status/select', vdom='root')
    assert response['ansible_network_resources']['system_status_select']['status'] == 'success'
    assert response['ansible_network_resources']['system_status_select']['http_status'] == 200

    # test case 02, args with single gather_subset with filters
    args = {
        'vdom': 'root',
        'gather_subset': [
            {'fact': 'system_interface_select', 'filters': [{'include_vlan': 'true'}, {'interface_name': 'port3'}]},
        ]
    }

    mock_module.params = args

    response, ignore = Facts(mock_module, fos_instance).get_facts()

    monitor_method_mock.assert_called_with('system', 'interface/select?vdom=root&include_vlan=true&interface_name=port3', vdom=None)
    assert response['ansible_network_resources']['system_interface_select']['status'] == 'success'
    assert response['ansible_network_resources']['system_interface_select']['http_status'] == 200

    # test case 03, args with multiple gather_subset
    args = {
        'vdom': 'root',
        'gather_subset': [
            {'fact': 'system_current-admins_select'},
            {'fact': 'system_firmware_select'},
            {'fact': 'system_fortimanager_status'},
            {'fact': 'system_ha-checksums_select'},
        ]
    }

    mock_module.params = args

    response, ignore = Facts(mock_module, fos_instance).get_facts()

    monitor_method_mock.assert_any_call('system', 'current-admins/select', vdom='root')
    monitor_method_mock.assert_any_call('system', 'firmware/select', vdom='root')
    monitor_method_mock.assert_any_call('system', 'fortimanager/status', vdom='root')
    monitor_method_mock.assert_any_call('system', 'ha-checksums/select', vdom='root')
    assert response['ansible_network_resources']['system_ha-checksums_select']['status'] == 'success'
    assert response['ansible_network_resources']['system_ha-checksums_select']['http_status'] == 200
