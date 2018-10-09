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
    from ansible.modules.network.fortimanager import fmgr_fwobj_service
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


def test_fmgr_fwobj_service_custom(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51
    # sctp-portrange: 100
    ##################################################
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51
    # sctp-portrange: 100
    ##################################################
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51
    # sctp-portrange: 100
    ##################################################
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51
    # sctp-portrange: 100
    ##################################################
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51
    # sctp-portrange: 100
    ##################################################
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51
    # sctp-portrange: 100
    ##################################################
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
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
    # tcp-portrange: 443:2000-1000,80-82:10000-20000
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_serviceWithSource
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51:100-200,162:200-400
    # sctp-portrange: 100:2000-2500
    ##################################################
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
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
    # group-member: None
    # application: None
    # tcp-portrange: 443:2000-1000,80-82:10000-20000
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_serviceWithSource
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51:100-200,162:200-400
    # sctp-portrange: 100:2000-2500
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
    # tcp-portrange: 443:2000-1000,80-82:10000-20000
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_serviceWithSource
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
    # mode: add
    # tcp-halfopen-timer: 0
    # udp-portrange: 51:100-200,162:200-400
    # sctp-portrange: 100:2000-2500
    ##################################################
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
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
    # group-member: None
    # application: None
    # tcp-portrange: 443:2000-1000,80-82:10000-20000
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
    # tcp-portrange: 443:2000-1000,80-82:10000-20000
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
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
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
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
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
    # protocol: None
    # custom_type: icmp
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: 8
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
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
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
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
    # protocol: None
    # custom_type: icmp
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: 8
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
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
    # protocol-number: None
    # protocol: None
    # custom_type: icmp6
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: 5
    # iprange: 0.0.0.0
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
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
    # protocol: None
    # custom_type: ip
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: 12
    # udp-idle-timer: 0
    # explicit-proxy: disable
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
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
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
    # protocol: None
    # custom_type: icmp
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: 8
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
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
    # protocol-number: None
    # protocol: None
    # custom_type: icmp6
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: 5
    # iprange: 0.0.0.0
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
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
    # protocol: None
    # custom_type: ip
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: 12
    # udp-idle-timer: 0
    # explicit-proxy: disable
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
    # protocol-number: None
    # protocol: None
    # custom_type: all
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: www.ansible.com
    # category: None
    # explicit-proxy: enable
    # udp-idle-timer: 0
    # group-member: None
    # application: None
    # tcp-portrange: 443:2000-1000,80-82:10000-20000
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
    ##################################################
    # comment: None
    # protocol-number: None
    # protocol: None
    # custom_type: all
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
    # name: ansible_custom_service
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
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
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_icmp
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol-number: None
    # protocol: None
    # custom_type: all
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
    # name: ansible_custom_icmp6
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
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
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
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
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol-number: None
    # protocol: None
    # custom_type: all
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
    # name: ansible_custom_serviceWithSource
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
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
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: None
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
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
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
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
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
    # protocol: None
    # custom_type: icmp
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: 8
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
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
    # protocol-number: None
    # protocol: None
    # custom_type: icmp6
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: 5
    # iprange: 0.0.0.0
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
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
    # protocol: None
    # custom_type: ip
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: 12
    # udp-idle-timer: 0
    # explicit-proxy: disable
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
    # protocol-number: None
    # protocol: None
    # custom_type: all
    # color: 22
    # object_type: custom
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: www.ansible.com
    # category: None
    # explicit-proxy: enable
    # udp-idle-timer: 0
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
    ##################################################
    # comment: None
    # protocol: None
    # custom_type: all
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
    # tcp-portrange: None
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
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol-number: None
    # protocol: None
    # custom_type: all
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
    # name: ansible_custom_icmp
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
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
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: ansible_custom_icmp6
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol-number: None
    # protocol: None
    # custom_type: all
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
    # mode: delete
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
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: None
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
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol-number: None
    # protocol: None
    # custom_type: all
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
    # name: ansible_custom_proxy_all
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 2 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 3 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 4 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 5 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 6 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 7 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[6]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 8 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[7]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 9 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[8]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 10 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[9]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -9001
    # Test using fixture 11 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[10]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -9998
    # Test using fixture 12 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[11]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 13 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[12]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -9998
    # Test using fixture 14 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[13]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 15 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[14]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 16 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[15]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 17 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[16]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 18 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[17]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 19 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[18]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 20 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[19]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 21 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[20]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 22 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[21]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 23 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[22]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 24 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[23]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 25 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[24]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 26 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[25]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 27 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[26]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 28 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[27]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 29 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[28]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -9998
    # Test using fixture 30 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[29]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 31 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[30]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 32 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[31]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 33 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[32]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 34 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[33]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 35 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[34]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 36 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[35]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 37 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[36]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 38 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[37]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 39 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[38]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 40 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[39]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 41 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[40]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 42 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[41]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 43 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[42]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 44 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[43]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 45 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[44]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 46 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[45]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 47 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[46]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 48 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[47]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 49 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[48]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 50 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[49]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 51 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[50]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 52 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[51]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 53 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_custom(fmg_instance, fixture_data[52]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_fmgr_fwobj_service_group(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: created by ansible
    # protocol-number: None
    # protocol: None
    # custom_type: all
    # color: 10
    # object_type: group
    # group-name: ansibleTestGroup
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
    # group-member: ansible_custom_ip, ansible_custom_icmp, ansible_custom_service
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: None
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
    # comment: created by ansible
    # protocol: None
    # custom_type: all
    # color: 10
    # object_type: group
    # group-name: ansibleTestGroup
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: ansible_custom_ip, ansible_custom_icmp, ansible_custom_service
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: None
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
    # comment: created by ansible
    # protocol-number: None
    # protocol: None
    # custom_type: all
    # color: 10
    # object_type: group
    # group-name: ansibleTestGroup
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
    # group-member: ansible_custom_ip, ansible_custom_icmp, ansible_custom_service
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: None
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
    # comment: created by ansible
    # protocol: None
    # custom_type: all
    # color: 10
    # object_type: group
    # group-name: ansibleTestGroup
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: ansible_custom_ip, ansible_custom_icmp, ansible_custom_service
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: None
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
    # comment: created by ansible
    # protocol-number: None
    # protocol: None
    # custom_type: all
    # color: 10
    # object_type: group
    # group-name: ansibleTestGroup
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # explicit-proxy: disable
    # udp-idle-timer: 0
    # group-member: ansible_custom_ip, ansible_custom_icmp, ansible_custom_service
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: None
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
    # object_type: group
    # group-name: ansibleTestGroup
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: None
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: created by ansible
    # protocol: None
    # custom_type: all
    # color: 10
    # object_type: group
    # group-name: ansibleTestGroup
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: None
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: ansible_custom_ip, ansible_custom_icmp, ansible_custom_service
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: None
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
    # protocol-number: None
    # protocol: None
    # custom_type: all
    # color: 22
    # object_type: group
    # group-name: ansibleTestGroup
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
    # name: None
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_group(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10131
    # Test using fixture 2 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_group(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10131
    # Test using fixture 3 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_group(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10131
    # Test using fixture 4 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_group(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10131
    # Test using fixture 5 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_group(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 6 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_group(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 7 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_group(fmg_instance, fixture_data[6]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 8 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_group(fmg_instance, fixture_data[7]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0


def test_fmgr_fwobj_service_category(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: created by ansible
    # protocol-number: None
    # protocol: None
    # custom_type: all
    # color: 22
    # object_type: category
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: ansibleCategory5
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
    # name: None
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
    # mode: set
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
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
    # app-service-type: 0
    # fqdn:
    # app-category: None
    # check-reset-range: 3
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
    ##################################################
    # comment: None
    # protocol-number: None
    # protocol: None
    # custom_type: all
    # color: 22
    # object_type: category
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: ansibleCategory5
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
    # name: None
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol: None
    # custom_type: all
    # color: 22
    # object_type: category
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: ansibleCategory2
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: None
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol-number: None
    # protocol: None
    # custom_type: all
    # color: 22
    # object_type: category
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: ansibleCategory
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
    # name: None
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: created by ansible
    # protocol: None
    # custom_type: all
    # color: 22
    # object_type: category
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: ansibleCategory5
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: None
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: set
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
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
    # custom_type: all
    # color: 22
    # object_type: category
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: ansibleCategory5
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: None
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol-number: None
    # protocol: None
    # custom_type: all
    # color: 22
    # object_type: category
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: ansibleCategory2
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
    # name: None
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################
    ##################################################
    # comment: None
    # protocol: None
    # custom_type: all
    # color: 22
    # object_type: category
    # group-name: None
    # tcp-halfclose-timer: 0
    # icmp_type: None
    # iprange: 0.0.0.0
    # category: ansibleCategory
    # protocol-number: None
    # udp-idle-timer: 0
    # explicit-proxy: disable
    # group-member: None
    # application: None
    # tcp-portrange: None
    # icmp_code: None
    # session-ttl: 0
    # adom: ansible
    # visibility: enable
    # tcp-timewait-timer: 0
    # name: None
    # app-service-type: None
    # fqdn:
    # app-category: None
    # check-reset-range: None
    # mode: delete
    # tcp-halfopen-timer: 0
    # udp-portrange: None
    # sctp-portrange: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 3 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 4 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 5 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 6 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 7 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[6]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 8 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[7]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 9 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[8]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 10 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[9]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 11 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[10]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 12 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[11]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 13 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[12]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 14 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[13]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 15 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[14]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 16 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[15]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 17 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[16]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 18 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[17]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 19 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[18]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 20 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[19]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 21 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[20]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 22 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[21]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 23 #
    output = fmgr_fwobj_service.fmgr_fwobj_service_category(fmg_instance, fixture_data[22]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
