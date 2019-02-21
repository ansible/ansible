# Copyright 2018 Fortinet, Inc.
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
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
import pytest

try:
    from ansible.modules.network.fortimanager import fmgr_device
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)


def load_fixtures():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures') + "/{filename}.json".format(
        filename=os.path.splitext(os.path.basename(__file__))[0])
    try:
        with open(fixture_path, "r") as fixture_file:
            fixture_data = json.load(fixture_file)
    except IOError:
        return []
    return [fixture_data]


@pytest.fixture(autouse=True)
def module_mock(mocker):
    connection_class_mock = mocker.patch('ansible.module_utils.basic.AnsibleModule')
    return connection_class_mock


@pytest.fixture(autouse=True)
def connection_mock(mocker):
    connection_class_mock = mocker.patch('ansible.modules.network.fortimanager.fmgr_device.Connection')
    return connection_class_mock


@pytest.fixture(scope="function", params=load_fixtures())
def fixture_data(request):
    func_name = request.function.__name__.replace("test_", "")
    return request.param.get(func_name, None)


fmg_instance = FortiManagerHandler(connection_mock, module_mock)


def test_discover_device(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.151
    # device_unique_name: FGT1
    # mode: exec
    # device_serial: None
    # device_password: fortinet
    ##################################################
    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.152
    # device_unique_name: FGT2
    # mode: exec
    # device_serial: None
    # device_password: fortinet
    ##################################################
    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.153
    # device_unique_name: FGT3
    # mode: exec
    # device_serial: None
    # device_password: fortinet
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device.discover_device(fmg_instance, fixture_data[0]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 2 #
    output = fmgr_device.discover_device(fmg_instance, fixture_data[1]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 3 #
    output = fmgr_device.discover_device(fmg_instance, fixture_data[2]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True


def test_add_device(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.151
    # device_unique_name: FGT1
    # mode: exec
    # device_serial: None
    # device_password: fortinet
    ##################################################
    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.152
    # device_unique_name: FGT2
    # mode: exec
    # device_serial: None
    # device_password: fortinet
    ##################################################
    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.153
    # device_unique_name: FGT3
    # mode: exec
    # device_serial: None
    # device_password: fortinet
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device.add_device(fmg_instance, fixture_data[0]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 2 #
    output = fmgr_device.add_device(fmg_instance, fixture_data[1]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 3 #
    output = fmgr_device.add_device(fmg_instance, fixture_data[2]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True


def test_delete_device(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # device_username: admin
    # adom: root
    # device_ip: 10.7.220.151
    # device_unique_name: FGT1
    # mode: exec
    # device_serial: None
    # device_password: fortinet
    ##################################################
    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.152
    # device_unique_name: FGT2
    # mode: exec
    # device_serial: None
    # device_password: fortinet
    ##################################################
    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.153
    # device_unique_name: FGT3
    # mode: exec
    # device_serial: None
    # device_password: fortinet
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device.delete_device(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_device.delete_device(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 3 #
    output = fmgr_device.delete_device(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_get_device(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.151
    # device_unique_name: FGT1
    # mode: get
    # device_serial: None
    # device_password: fortinet
    ##################################################
    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.152
    # device_unique_name: FGT2
    # mode: get
    # device_serial: None
    # device_password: fortinet
    ##################################################
    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.153
    # device_unique_name: FGT3
    # mode: get
    # device_serial: None
    # device_password: fortinet
    ##################################################
    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.151
    # device_unique_name: FGT1
    # mode: get
    # device_serial: None
    # device_password: fortinet
    ##################################################
    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.152
    # device_unique_name: FGT2
    # mode: get
    # device_serial: None
    # device_password: fortinet
    ##################################################
    ##################################################
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.153
    # device_unique_name: FGT3
    # mode: get
    # device_serial: None
    # device_password: fortinet
    ##################################################

    # Test using fixture 1 #
    output = fmgr_device.get_device(fmg_instance, fixture_data[0]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 2 #
    output = fmgr_device.get_device(fmg_instance, fixture_data[1]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 3 #
    output = fmgr_device.get_device(fmg_instance, fixture_data[2]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 4 #
    output = fmgr_device.get_device(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 5 #
    output = fmgr_device.get_device(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 6 #
    output = fmgr_device.get_device(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
