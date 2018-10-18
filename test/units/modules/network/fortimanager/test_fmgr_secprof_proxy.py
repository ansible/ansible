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
    from ansible.modules.network.fortimanager import fmgr_secprof_proxy
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)

fmg_instance = FortiManager("1.1.1.1", "admin", "")


def load_fixtures():
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        'fixtures') + "/{filename}.json".format(
        filename=os.path.splitext(
            os.path.basename(__file__))[0])
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


def test_fmgr_web_proxy_profile_addsetdelete(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # header-via-request: None
    # name: Ansible_Web_Filter_Profile
    # adom: root
    # log-header-change: None
    # header-front-end-https: None
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
    # header-via-request: None
    # name: Ansible_Web_Filter_Profile
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
    # header-via-request: None
    # name: Ansible_Web_Proxy_Profile
    # adom: root
    # log-header-change: None
    # header-front-end-https: None
    # headers: {'action': None, 'content': None, 'name': None}
    # mode: set
    # header-via-response: None
    # header-x-authenticated-user: None
    # strip-encoding: None
    # header-x-forwarded-for: None
    # header-x-authenticated-groups: None
    # header-client-ip: None
    ##################################################
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
    output = fmgr_secprof_proxy.fmgr_web_proxy_profile_addsetdelete(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 2 #
    output = fmgr_secprof_proxy.fmgr_web_proxy_profile_addsetdelete(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 3 #
    output = fmgr_secprof_proxy.fmgr_web_proxy_profile_addsetdelete(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 4 #
    output = fmgr_secprof_proxy.fmgr_web_proxy_profile_addsetdelete(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 5 #
    output = fmgr_secprof_proxy.fmgr_web_proxy_profile_addsetdelete(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0

