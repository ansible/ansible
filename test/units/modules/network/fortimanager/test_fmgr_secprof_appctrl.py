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
    from ansible.modules.network.fortimanager import fmgr_secprof_appctrl
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


def test_fmgr_application_list_modify(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request", 
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: Created by Ansible Module TEST
    # other-application-log: None
    # replacemsg-group: None
    # adom: ansible
    # unknown-application-log: None
    # p2p-black-list: None
    # unknown-application-action: None
    # extended-log: None
    # deep-app-inspection: None
    # mode: delete
    # other-application-action: None
    # entries: {'behavior': None, 'rate-duration': None, 'sub-category': None, 'session-ttl': None, 'per-ip-shaper': None, 'category': None, 'log': None, 'parameters': {'value': None}, 'technology': None, 'quarantine-expiry': None, 'application': None, 'protocols': None, 'log-packet': None, 'quarantine-log': None, 'vendor': None, 'risk': None, 'rate-count': None, 'quarantine': None, 'popularity': None, 'shaper': None, 'shaper-reverse': None, 'rate-track': None, 'rate-mode': None, 'action': None}
    # options: None
    # app-replacemsg: None
    # name: Ansible_Application_Control_Profile
    ##################################################
    ##################################################
    # comment: Created by Ansible Module TEST
    # other-application-log: None
    # replacemsg-group: None
    # p2p-black-list: None
    # unknown-application-log: None
    # adom: ansible
    # unknown-application-action: None
    # extended-log: None
    # deep-app-inspection: None
    # mode: set
    # other-application-action: None
    # entries: [{'quarantine-log': 'enable', 'log': 'enable', 'quarantine': 'attacker', 'action': 'block', 'log-packet': 'enable', 'protocols': ['1']}, {'action': 'pass', 'category': ['2', '3', '4']}]
    # options: None
    # app-replacemsg: None
    # name: Ansible_Application_Control_Profile
    ##################################################
    ##################################################
    # comment: Created by Ansible Module TEST
    # other-application-log: None
    # replacemsg-group: None
    # adom: ansible
    # unknown-application-log: None
    # p2p-black-list: None
    # unknown-application-action: None
    # extended-log: None
    # options: None
    # deep-app-inspection: None
    # mode: delete
    # other-application-action: None
    # entries: {'behavior': None, 'rate-duration': None, 'sub-category': None, 'session-ttl': None, 'per-ip-shaper': None, 'category': None, 'log': None, 'parameters': {'value': None}, 'technology': None, 'quarantine-expiry': None, 'application': None, 'protocols': None, 'log-packet': None, 'quarantine-log': None, 'vendor': None, 'risk': None, 'rate-count': None, 'quarantine': None, 'popularity': None, 'shaper': None, 'shaper-reverse': None, 'rate-track': None, 'rate-mode': None, 'action': None}
    # app-replacemsg: None
    # name: Ansible_Application_Ctl_Profile2
    ##################################################
    ##################################################
    # comment: Created by Ansible Module TEST
    # adom: ansible
    # unknown-application-log: None
    # extended-log: None
    # other-application-action: None
    # entries: {'rate-duration': None, 'sub-category': None, 'vendor': None, 'technology': None, 'risk': None, 'category': None, 'log': 'enable', 'parameters': {'value': None}, 'per-ip-shaper': None, 'quarantine-expiry': None, 'application': None, 'protocols': "['1']", 'log-packet': 'enable', 'quarantine-log': 'enable', 'session-ttl': None, 'behavior': None, 'rate-count': None, 'quarantine': 'attacker', 'popularity': None, 'shaper': None, 'shaper-reverse': None, 'rate-track': None, 'rate-mode': None, 'action': 'pass'}
    # replacemsg-group: None
    # other-application-log: None
    # name: Ansible_Application_Ctl_Profile2
    # p2p-black-list: None
    # unknown-application-action: None
    # deep-app-inspection: None
    # mode: set
    # app-replacemsg: None
    # options: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_secprof_appctrl.fmgr_application_list_modify(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_secprof_appctrl.fmgr_application_list_modify(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 3 #
    output = fmgr_secprof_appctrl.fmgr_application_list_modify(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 4 #
    output = fmgr_secprof_appctrl.fmgr_application_list_modify(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
