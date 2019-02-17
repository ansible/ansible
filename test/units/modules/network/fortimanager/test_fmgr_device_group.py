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
from pyFMG.fortimgr import FortiManager
import pytest

try:
    from ansible.modules.network.fortimanager import fmgr_device_group
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


def test_add_device_group(fixture_data, mocker):
    mocker.patch(
        "pyFMG.fortimgr.FortiManager._post_request",
        side_effect=fixture_data)

    paramgram_used = {
        'grp_desc': 'CreatedbyAnsible',
        'adom': 'ansible',
        'grp_members': None,
        'state': 'present',
        'grp_name': 'TestGroup',
        'vdom': 'root',
        'mode': 'add'}
    output = fmgr_device_group.add_device_group(fmg_instance, paramgram_used)
    #
    # grp_desc: CreatedbyAnsible
    # adom: ansible
    # grp_members: None
    # state: present
    # grp_name: TestGroup
    # vdom: root
    # mode: add
    #
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {
        'grp_desc': 'CreatedbyAnsible',
        'adom': 'ansible',
        'grp_members': None,
        'state': 'present',
        'grp_name': 'testtest',
        'vdom': 'root',
        'mode': 'add'}
    output = fmgr_device_group.add_device_group(fmg_instance, paramgram_used)
    #
    # grp_desc: CreatedbyAnsible
    # adom: ansible
    # grp_members: None
    # state: present
    # grp_name: testtest
    # vdom: root
    # mode: add
    #
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {
        'grp_desc': None,
        'adom': 'ansible',
        'grp_members': 'FGT1,FGT2',
        'state': 'present',
        'grp_name': 'TestGroup',
        'vdom': 'root',
        'mode': 'add'}
    output = fmgr_device_group.add_device_group(fmg_instance, paramgram_used)
    #
    # grp_desc: None
    # adom: ansible
    # grp_members: FGT1,FGT2
    # state: present
    # grp_name: TestGroup
    # vdom: root
    # mode: add
    #
    assert output['raw_response']['status']['code'] == -2
    paramgram_used = {
        'grp_desc': None,
        'adom': 'ansible',
        'grp_members': 'FGT3',
        'state': 'present',
        'grp_name': 'testtest',
        'vdom': 'root',
        'mode': 'add'}
    output = fmgr_device_group.add_device_group(fmg_instance, paramgram_used)
    #
    # grp_desc: None
    # adom: ansible
    # grp_members: FGT3
    # state: present
    # grp_name: testtest
    # vdom: root
    # mode: add
    #
    assert output['raw_response']['status']['code'] == -2


def test_delete_device_group(fixture_data, mocker):
    mocker.patch(
        "pyFMG.fortimgr.FortiManager._post_request",
        side_effect=fixture_data)

    paramgram_used = {
        'grp_desc': 'CreatedbyAnsible',
        'adom': 'ansible',
        'grp_members': None,
        'state': 'absent',
        'grp_name': 'TestGroup',
        'vdom': 'root',
        'mode': 'delete'}
    output = fmgr_device_group.delete_device_group(
        fmg_instance, paramgram_used)
    #
    # grp_desc: CreatedbyAnsible
    # adom: ansible
    # grp_members: None
    # state: absent
    # grp_name: TestGroup
    # vdom: root
    # mode: delete
    #
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {
        'grp_desc': 'CreatedbyAnsible',
        'adom': 'ansible',
        'grp_members': None,
        'state': 'absent',
        'grp_name': 'testtest',
        'vdom': 'root',
        'mode': 'delete'}
    output = fmgr_device_group.delete_device_group(
        fmg_instance, paramgram_used)
    #
    # grp_desc: CreatedbyAnsible
    # adom: ansible
    # grp_members: None
    # state: absent
    # grp_name: testtest
    # vdom: root
    # mode: delete
    #
    assert output['raw_response']['status']['code'] == 0


def test_add_group_member(fixture_data, mocker):
    mocker.patch(
        "pyFMG.fortimgr.FortiManager._post_request",
        side_effect=fixture_data)

    paramgram_used = {
        'grp_desc': None,
        'adom': 'ansible',
        'grp_members': 'FGT1,FGT2',
        'state': 'present',
        'grp_name': 'TestGroup',
        'vdom': 'root',
        'mode': 'add'}
    output = fmgr_device_group.add_group_member(fmg_instance, paramgram_used)
    #
    # grp_desc: None
    # adom: ansible
    # grp_members: FGT1,FGT2
    # state: present
    # grp_name: TestGroup
    # vdom: root
    # mode: add
    #

    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {
        'grp_desc': None,
        'adom': 'ansible',
        'grp_members': 'FGT3',
        'state': 'present',
        'grp_name': 'testtest',
        'vdom': 'root',
        'mode': 'add'}
    output = fmgr_device_group.add_group_member(fmg_instance, paramgram_used)
    #
    # grp_desc: None
    # adom: ansible
    # grp_members: FGT3
    # state: present
    # grp_name: testtest
    # vdom: root
    # mode: add
    #
    assert output['raw_response']['status']['code'] == 0


def test_delete_group_member(fixture_data, mocker):
    mocker.patch(
        "pyFMG.fortimgr.FortiManager._post_request",
        side_effect=fixture_data)

    paramgram_used = {
        'grp_desc': None,
        'adom': 'ansible',
        'grp_members': 'FGT3',
        'state': 'absent',
        'grp_name': 'testtest',
        'vdom': 'root',
        'mode': 'delete'}
    output = fmgr_device_group.delete_group_member(
        fmg_instance, paramgram_used)
    #
    # grp_desc: None
    # adom: ansible
    # grp_members: FGT3
    # state: absent
    # grp_name: testtest
    # vdom: root
    # mode: delete
    #
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {
        'grp_desc': None,
        'adom': 'ansible',
        'grp_members': 'FGT1,FGT2',
        'state': 'absent',
        'grp_name': 'TestGroup',
        'vdom': 'root',
        'mode': 'delete'}
    output = fmgr_device_group.delete_group_member(
        fmg_instance, paramgram_used)
    #
    # grp_desc: None
    # adom: ansible
    # grp_members: FGT1,FGT2
    # state: absent
    # grp_name: TestGroup
    # vdom: root
    # mode: delete
    #
