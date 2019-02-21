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
    from ansible.modules.network.fortimanager import fmgr_secprof_proxy
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


def test_fmgr_web_proxy_profile_modify(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request", 
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # header-via-request: None
    # name: Ansible_Web_Proxy_Profile
    # header-front-end-https: None
    # log-header-change: None
    # adom: root
    # headers: {'action': None, 'content': None, 'name': None}
    # mode: delete
    # header-via-response: None
    # header-x-authenticated-user: None
    # strip-encoding: None
    # header-x-forwarded-for: None
    # header-x-authenticated-groups: None
    # header-client-ip: None
    ##################################################
    ##################################################
    # header-via-request: remove
    # header-client-ip: pass
    # header-front-end-https: add
    # header-x-authenticated-groups: add
    # name: Ansible_Web_Proxy_Profile
    # log-header-change: enable
    # adom: root
    # headers: {'action': 'add-to-request', 'content': 'test', 'name': 'test_header'}
    # mode: set
    # header-via-response: pass
    # header-x-authenticated-user: remove
    # strip-encoding: enable
    # header-x-forwarded-for: pass
    ##################################################

    # Test using fixture 1 #
    output = fmgr_secprof_proxy.fmgr_web_proxy_profile_modify(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_secprof_proxy.fmgr_web_proxy_profile_modify(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
