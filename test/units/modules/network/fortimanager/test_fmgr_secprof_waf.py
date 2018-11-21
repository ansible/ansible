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
    from ansible.modules.network.fortimanager import fmgr_secprof_waf
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


def test_fmgr_waf_profile_addsetdelete(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: Created by Ansible Module TEST
    # name: Ansible_WAF_Profile
    # adom: root
    # address-list: {'blocked-address': None, 'status': None, 'severity': None, 'blocked-log': None,
    # 'trusted-address': None}
    # constraint: {'header-length': {'action': None, 'status': None, 'length': None, 'log': None, 'severity': None},
    #  'content-length': {'action': None, 'status': None, 'length': None, 'log': None, 'severity': None},
    #  'max-cookie': {'action': None, 'status': None, 'max-cookie': None, 'log': None, 'severity': None},
    #  'url-param-length': {'action': None, 'status': None, 'length': None, 'log': None, 'severity': None},
    #  'hostname': {'action': None, 'status': None, 'log': None, 'severity': None},
    #  'line-length': {'action': None, 'status': None, 'length': None, 'log': None, 'severity': None},
    # 'exception': {'regex': None, 'header-length': None, 'content-length': None, 'max-cookie': None, 'pattern': None,
    #  'hostname': None, 'line-length': None, 'max-range-segment': None, 'url-param-length': None, 'version': None,
    #  'param-length': None, 'malformed': None, 'address': None, 'max-url-param': None, 'max-header-line': None,
    #  'method': None}, 'max-range-segment': {'action': None, 'status': None, 'max-range-segment': None,
    #  'severity': None, 'log': None}, 'version': {'action': None, 'status': None, 'log': None, 'severity': None},
    #  'param-length': {'action': None, 'status': None, 'length': None, 'log': None, 'severity': None},
    #  'malformed': {'action': None, 'status': None, 'log': None, 'severity': None}, 'max-url-param': {'action': None,
    #  'status': None, 'max-url-param': None, 'log': None, 'severity': None}, 'max-header-line': {'action': None,
    #  'status': None, 'max-header-line': None, 'log': None, 'severity': None}, 'method': {'action': None,
    # 'status': None, 'log': None, 'severity': None}}
    # extended-log: None
    # url-access: {'action': None, 'address': None, 'severity': None, 'access-pattern': {'negate': None,
    #  'pattern': None, 'srcaddr': None, 'regex': None}, 'log': None}
    # external: None
    # signature: {'custom-signature': {'status': None, 'direction': None, 'target': None, 'severity': None,
    #  'case-sensitivity': None, 'name': None, 'pattern': None, 'action': None, 'log': None},
    #  'credit-card-detection-threshold': None, 'main-class': {'action': None, 'status': None, 'log': None,
    #  'severity': None}, 'disabled-signature': None, 'disabled-sub-class': None}
    # method: {'status': None, 'severity': None, 'default-allowed-methods': None, 'log': None,
    #  'method-policy': {'regex': None, 'pattern': None, 'allowed-methods': None, 'address': None}}
    # mode: delete
    ##################################################
    ##################################################
    # comment: Created by Ansible Module TEST
    # adom: root
    # address-list: {'blocked-address': None, 'status': None, 'severity': None, 'blocked-log': None,
    #  'trusted-address': None}
    # extended-log: None
    # url-access: {'action': None, 'severity': None, 'log': None, 'access-pattern': {'negate': None, 'pattern': None,
    #  'srcaddr': None, 'regex': None}, 'address': None}
    # external: None
    # name: Ansible_WAF_Profile
    # constraint: {'content-length': {'action': None, 'status': None, 'length': None, 'log': None, 'severity': None},
    # 'max-cookie': {'action': None, 'status': None, 'max-cookie': None, 'log': None, 'severity': None},
    #  'line-length': {'action': None, 'status': None, 'length': None, 'log': None, 'severity': None},
    #  'max-range-segment': {'action': None, 'severity': None, 'status': None, 'log': None, 'max-range-segment': None},
    #  'param-length': {'action': None, 'status': None, 'length': None, 'log': None, 'severity': None},
    #  'malformed': {'action': None, 'status': None, 'log': None, 'severity': None}, 'max-url-param': {'action': None,
    #  'status': None, 'max-url-param': None, 'log': None, 'severity': None}, 'header-length': {'action': None,
    #  'status': None, 'length': None, 'log': None, 'severity': None}, 'exception': {'regex': None,
    #  'header-length': None, 'content-length': None, 'max-cookie': None, 'pattern': None, 'hostname': None,
    #  'line-length': None, 'max-range-segment': None, 'url-param-length': None, 'version': None, 'param-length': None,
    #  'malformed': None, 'address': None, 'max-url-param': None, 'max-header-line': None, 'method': None},
    #  'hostname': {'action': None, 'status': None, 'log': None, 'severity': None},
    #  'url-param-length': {'action': None, 'status': None, 'length': None, 'log': None, 'severity': None},
    #  'version': {'action': None, 'status': None, 'log': None, 'severity': None}, 'max-header-line': {'action': None,
    #  'status': None, 'max-header-line': None, 'log': None, 'severity': None}, 'method': {'action': None,
    #  'status': None, 'log': None, 'severity': None}}
    # mode: set
    # signature: {'custom-signature': {'status': None, 'direction': None, 'log': None, 'severity': None, 'target': None,
    #  'action': None, 'pattern': None, 'case-sensitivity': None, 'name': None},
    #  'credit-card-detection-threshold': None, 'main-class': {'action': None, 'status': None, 'log': None,
    #  'severity': None}, 'disabled-signature': None, 'disabled-sub-class': None}
    # method: {'status': None, 'default-allowed-methods': None, 'method-policy': {'regex': None, 'pattern': None,
    #  'allowed-methods': None, 'address': None}, 'log': None, 'severity': None}
    ##################################################

    # Test using fixture 1 #
    output = fmgr_secprof_waf.fmgr_waf_profile_addsetdelete(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_secprof_waf.fmgr_waf_profile_addsetdelete(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
