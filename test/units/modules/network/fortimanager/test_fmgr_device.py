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

import os
import json
from pyFMG.fortimgr import FortiManager
import pytest

try:
    from ansible.modules.network.fortimanager import fmgr_device
except ImportError:
    pytest.skip(
        "Could not load required modules for testing",
        allow_module_level=True)

fmg_instance = FortiManager("1.1.1.1", "admin", "")


def load_fixtures():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures') + "/{filename}.json".format(
        filename=os.path.splitext(os.path.basename(__file__))[0])
    try:
        with open(fixture_path, "r") as fixture_file:
            fixture_data = json.load(fixture_file)
    except IOError:
        return []
    return [fixture_data]


@pytest.fixture(scope="function", params=load_fixtures())
def fixture_data(request):
    func_name = request.function.__name__.replace("test_", "")
    return request.param.get(func_name, None)


def test_discover_device(fixture_data, mocker):
    mocker.patch(
        "pyFMG.fortimgr.FortiManager._post_request",
        side_effect=fixture_data)
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.151', 'state': 'present',
        'device_unique_name': 'FGT1', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.discover_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.151
    # state: present
    # device_unique_name: FGT1
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert isinstance(output['raw_response'], dict) is True
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.152', 'state': 'present',
        'device_unique_name': 'FGT2', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.discover_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.152
    # state: present
    # device_unique_name: FGT2
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert isinstance(output['raw_response'], dict) is True
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.153', 'state': 'present',
        'device_unique_name': 'FGT3', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.discover_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.153
    # state: present
    # device_unique_name: FGT3
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert output['raw_response']['status']['code'] == -20042
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.151', 'state': 'present',
        'device_unique_name': 'FGT1', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.discover_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.151
    # state: present
    # device_unique_name: FGT1
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert isinstance(output['raw_response'], dict) is True
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.152', 'state': 'present',
        'device_unique_name': 'FGT2', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.discover_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.152
    # state: present
    # device_unique_name: FGT2
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert isinstance(output['raw_response'], dict) is True
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.153', 'state': 'present',
        'device_unique_name': 'FGT3', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.discover_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.153
    # state: present
    # device_unique_name: FGT3
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert isinstance(output['raw_response'], dict) is True


def test_add_device(fixture_data, mocker):
    mocker.patch(
        "pyFMG.fortimgr.FortiManager._post_request",
        side_effect=fixture_data)
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.151', 'state': 'present',
        'device_unique_name': 'FGT1', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.add_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.151
    # state: present
    # device_unique_name: FGT1
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert isinstance(output['raw_response'], dict) is True
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.152', 'state': 'present',
        'device_unique_name': 'FGT2', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.add_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.152
    # state: present
    # device_unique_name: FGT2
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert isinstance(output['raw_response'], dict) is True
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.151', 'state': 'present',
        'device_unique_name': 'FGT1', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.add_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.151
    # state: present
    # device_unique_name: FGT1
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert output['raw_response']['status']['code'] == -20010
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.152', 'state': 'present',
        'device_unique_name': 'FGT2', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.add_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.152
    # state: present
    # device_unique_name: FGT2
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert output['raw_response']['status']['code'] == -20010
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.153', 'state': 'present',
        'device_unique_name': 'FGT3', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.add_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.153
    # state: present
    # device_unique_name: FGT3
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert isinstance(output['raw_response'], dict) is True


def test_delete_device(fixture_data, mocker):
    mocker.patch(
        "pyFMG.fortimgr.FortiManager._post_request",
        side_effect=fixture_data)
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.151', 'state': 'absent',
        'device_unique_name': 'FGT1', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.delete_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.151
    # state: absent
    # device_unique_name: FGT1
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.152', 'state': 'absent',
        'device_unique_name': 'FGT2', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.delete_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.152
    # state: absent
    # device_unique_name: FGT2
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {
        'device_username': 'admin', 'adom': 'ansible',
        'device_ip': '10.7.220.153', 'state': 'absent',
        'device_unique_name': 'FGT3', 'device_serial':
        None, 'device_password': 'fortinet',
        'mode': 'execute'}
    output = fmgr_device.delete_device(fmg_instance, paramgram_used)
    #
    # device_username: admin
    # adom: ansible
    # device_ip: 10.7.220.153
    # state: absent
    # device_unique_name: FGT3
    # device_serial: None
    # device_password: fortinet
    # mode: execute
    #
    assert output['raw_response']['status']['code'] == 0
