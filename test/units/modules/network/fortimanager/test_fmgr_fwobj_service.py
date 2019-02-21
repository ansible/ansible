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
    from ansible.modules.network.fortimanager import fmgr_fwobj_service
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


def test_fmgr_fwobj_service_custom(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request", 
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: None
    # protocol-number: None
    # protocol: None
    # custom_type: tcp_udp_sctp
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: ansibleCategoryTest
    # explicit-proxy: disable
    # udp-idle-timer: 0
    # group-member: None
    # application: None
    # tcp-portrange: 443
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_service
    # app-service-type: None
    # fqdn: 
    # app-category: None
    # check-reset-range: None
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51
    # sctp-portrange: 100
    ##################################################
    ##################################################
    # comment: None
    # protocol: None
    # custom_type: tcp_udp_sctp
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: 443:1000-2000,80-82:10000-20000
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_serviceWithSource
    # app-service-type: None
    # fqdn: 
    # app-category: None
    # check-reset-range: None
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51:100-200,162:200-400
    # sctp-portrange: 100:2000-2500
    ##################################################
    ##################################################
    # comment: None
    # protocol-number: None
    # protocol: None
    # custom_type: icmp
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: 8
    # iprange: 0.0.0.0
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
    # group-member: None
    # application: None
    # tcp-portrange: None
    # icmp_code: 3
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_icmp
    # app-service-type: None
    # fqdn: 
    # app-category: None
    # check-reset-range: None
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol: None
    # custom_type: icmp6
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: 5
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: None
    # icmp_code: 1
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_icmp6
    # app-service-type: None
    # fqdn: 
    # app-category: None
    # check-reset-range: None
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol-number: 12
    # protocol: None
    # custom_type: ip
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
    # group-member: None
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_ip
    # app-service-type: None
    # fqdn: 
    # app-category: None
    # check-reset-range: None
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol: None
    # custom_type: all
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: www.ansible.com
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: enable
    # group-member: None
    # application: None
    # tcp-portrange: 443:1000-2000,80-82:10000-20000
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_proxy_all
    # app-service-type: None
    # fqdn: 
    # app-category: None
    # check-reset-range: None
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 3 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 4 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 5 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 6 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_fmgr_fwobj_service_category(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request", 
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: None
    # protocol: None
    # custom_type: tcp_udp_sctp
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: ansibleCategoryTest
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: 443
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_service
    # app-service-type: None
    # fqdn: 
    # app-category: None
    # check-reset-range: None
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51
    # sctp-portrange: 100
    ##################################################

    # Test using fixture 1 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
