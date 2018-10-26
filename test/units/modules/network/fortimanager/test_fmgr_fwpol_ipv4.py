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
    from ansible.modules.network.fortimanager import fmgr_fwpol_ipv4
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)

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


def test_fmgr_firewall_policy_addsetdelete(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)

    # Test using fixture 1 #
    output = fmgr_fwpol_ipv4.fmgr_firewall_policy_addsetdelete(fmg_instance, fixture_data[0]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 2 #
    output = fmgr_fwpol_ipv4.fmgr_firewall_policy_addsetdelete(fmg_instance, fixture_data[1]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 3 #
    output = fmgr_fwpol_ipv4.fmgr_firewall_policy_addsetdelete(fmg_instance, fixture_data[2]['paramgram_used'])
    assert isinstance(output['raw_response'], dict) is True
    # Test using fixture 4 #
    output = fmgr_fwpol_ipv4.fmgr_firewall_policy_addsetdelete(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 5 #
    output = fmgr_fwpol_ipv4.fmgr_firewall_policy_addsetdelete(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 6 #
    output = fmgr_fwpol_ipv4.fmgr_firewall_policy_addsetdelete(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
