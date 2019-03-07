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
    from ansible.modules.network.fortimanager import fmgr_ha
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
    connection_class_mock = mocker.patch('ansible.modules.network.fortimanager.fmgr_ha.Connection')
    return connection_class_mock


@pytest.fixture(scope="function", params=load_fixtures())
def fixture_data(request):
    func_name = request.function.__name__.replace("test_", "")
    return request.param.get(func_name, None)


fmg_instance = FortiManagerHandler(connection_mock, module_mock)


def test_fmgr_set_ha_mode(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # fmgr_ha_peer_sn: None
    # fmgr_ha_hb_threshold: 10
    # fmgr_ha_cluster_pw: fortinet
    # fmgr_ha_peer_ipv6: None
    # fmgr_ha_peer_status: None
    # fmgr_ha_file_quota: 2048
    # fmgr_ha_cluster_id: 2
    # fmgr_ha_peer_ipv4: None
    # fmgr_ha_hb_interval: 15
    # fmgr_ha_mode: master
    # mode: set
    ##################################################
    ##################################################
    # fmgr_ha_peer_sn: None
    # fmgr_ha_hb_threshold: 3
    # fmgr_ha_cluster_pw: fortinet
    # fmgr_ha_hb_interval: 5
    # fmgr_ha_cluster_id: 2
    # fmgr_ha_file_quota: 4096
    # fmgr_ha_peer_status: None
    # fmgr_ha_peer_ipv4: None
    # fmgr_ha_peer_ipv6: None
    # fmgr_ha_mode: slave
    # mode: set
    ##################################################
    ##################################################
    # fmgr_ha_peer_sn: FMG-VMTM18001881
    # fmgr_ha_hb_threshold: 3
    # fmgr_ha_cluster_pw: fortinet
    # fmgr_ha_peer_ipv6: None
    # fmgr_ha_peer_status: enable
    # fmgr_ha_file_quota: 4096
    # fmgr_ha_cluster_id: 2
    # fmgr_ha_peer_ipv4: 10.7.220.35
    # fmgr_ha_hb_interval: 5
    # fmgr_ha_mode: slave
    # mode: set
    ##################################################
    ##################################################
    # fmgr_ha_file_quota: 4096
    # fmgr_ha_cluster_pw: None
    # fmgr_ha_peer_sn: None
    # fmgr_ha_hb_interval: 5
    # fmgr_ha_cluster_id: 1
    # fmgr_ha_mode: standalone
    # fmgr_ha_peer_status: None
    # fmgr_ha_hb_threshold: 3
    # fmgr_ha_peer_ipv4: None
    # fmgr_ha_peer_ipv6: None
    # mode: set
    ##################################################

    # Test using fixture 1 #
    output = fmgr_ha.fmgr_set_ha_mode(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_ha.fmgr_set_ha_mode(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 3 #
    output = fmgr_ha.fmgr_set_ha_mode(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 4 #
    output = fmgr_ha.fmgr_set_ha_mode(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_fmgr_get_ha_peer_list(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # fmgr_ha_peer_sn: FMG-VMTM18001882
    # fmgr_ha_hb_threshold: 3
    # fmgr_ha_cluster_pw: None
    # fmgr_ha_peer_ipv6: None
    # fmgr_ha_peer_status: enable
    # fmgr_ha_file_quota: 4096
    # fmgr_ha_cluster_id: 1
    # fmgr_ha_peer_ipv4: 10.7.220.36
    # fmgr_ha_hb_interval: 5
    # fmgr_ha_mode: None
    # mode: get
    ##################################################
    ##################################################
    # fmgr_ha_peer_sn: FMG-VMTM18001881
    # fmgr_ha_hb_threshold: 3
    # fmgr_ha_cluster_pw: fortinet
    # fmgr_ha_hb_interval: 5
    # fmgr_ha_cluster_id: 2
    # fmgr_ha_file_quota: 4096
    # fmgr_ha_peer_status: enable
    # fmgr_ha_peer_ipv4: 10.7.220.35
    # fmgr_ha_peer_ipv6: None
    # fmgr_ha_mode: slave
    # mode: get
    ##################################################

    # Test using fixture 1 #
    output = fmgr_ha.fmgr_get_ha_peer_list(fmg_instance)
    assert isinstance(output['raw_response'], list) is True
    # Test using fixture 2 #
    output = fmgr_ha.fmgr_get_ha_peer_list(fmg_instance)
    assert isinstance(output['raw_response'], list) is True


def test_fmgr_set_ha_peer(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # fmgr_ha_peer_sn: FMG-VMTM18001882
    # next_peer_id: 2
    # fmgr_ha_hb_threshold: 3
    # fmgr_ha_cluster_pw: None
    # fmgr_ha_peer_ipv6: None
    # fmgr_ha_peer_status: enable
    # fmgr_ha_file_quota: 4096
    # fmgr_ha_cluster_id: 1
    # peer_id: 1
    # fmgr_ha_peer_ipv4: 10.7.220.36
    # fmgr_ha_hb_interval: 5
    # fmgr_ha_mode: None
    # mode: set
    ##################################################
    ##################################################
    # fmgr_ha_peer_sn: FMG-VMTM18001881
    # next_peer_id: 1
    # fmgr_ha_hb_threshold: 3
    # fmgr_ha_cluster_pw: fortinet
    # fmgr_ha_hb_interval: 5
    # fmgr_ha_cluster_id: 2
    # fmgr_ha_file_quota: 4096
    # fmgr_ha_peer_status: enable
    # peer_id: 1
    # fmgr_ha_peer_ipv4: 10.7.220.35
    # fmgr_ha_peer_ipv6: None
    # fmgr_ha_mode: slave
    # mode: set
    ##################################################

    # Test using fixture 1 #
    output = fmgr_ha.fmgr_set_ha_peer(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_ha.fmgr_set_ha_peer(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
