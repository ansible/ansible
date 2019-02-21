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
    from ansible.modules.network.fortimanager import fmgr_fwobj_ippool
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


def test_fmgr_fwobj_ippool_modify(fixture_data, mocker):
    mocker.patch("ansible.module_utils.network.fortimanager.fortimanager.FortiManagerHandler.process_request",
                 side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # source-endip: None
    # arp-intf: None
    # num-blocks-per-user: None
    # name: Ansible_pool4_overload
    # adom: ansible
    # startip: 10.10.10.10
    # comments: Created by ansible
    # permit-any-host: None
    # arp-reply: enable
    # pba-timeout: None
    # endip: 10.10.10.100
    # associated-interface: None
    # mode: add
    # source-startip: None
    # type: overload
    # block-size: None
    ##################################################
    ##################################################
    # permit-any-host: None
    # num-blocks-per-user: None
    # name: Ansible_pool4_121
    # adom: ansible
    # startip: 10.10.20.10
    # arp-intf: None
    # comments: Created by ansible
    # source-endip: None
    # arp-reply: enable
    # pba-timeout: None
    # endip: 10.10.20.100
    # associated-interface: None
    # mode: add
    # source-startip: None
    # type: one-to-one
    # block-size: None
    ##################################################
    ##################################################
    # source-endip: 192.168.20.20
    # arp-intf: None
    # num-blocks-per-user: None
    # name: Ansible_pool4_fixed_port
    # adom: ansible
    # startip: 10.10.40.10
    # comments: Created by ansible
    # permit-any-host: None
    # arp-reply: enable
    # pba-timeout: None
    # endip: 10.10.40.100
    # associated-interface: None
    # mode: add
    # source-startip: 192.168.20.1
    # type: fixed-port-range
    # block-size: None
    ##################################################
    ##################################################
    # permit-any-host: None
    # num-blocks-per-user: 1
    # name: Ansible_pool4_port_block_allocation
    # adom: ansible
    # startip: 10.10.30.10
    # arp-intf: None
    # comments: Created by ansible
    # source-endip: None
    # arp-reply: enable
    # pba-timeout: None
    # endip: 10.10.30.100
    # associated-interface: None
    # mode: add
    # source-startip: None
    # type: port-block-allocation
    # block-size: 128
    ##################################################
    ##################################################
    # source-endip: None
    # arp-intf: None
    # num-blocks-per-user: None
    # name: Ansible_pool4_overload
    # adom: ansible
    # startip: None
    # comments: Created by ansible
    # permit-any-host: None
    # arp-reply: None
    # pba-timeout: None
    # endip: None
    # associated-interface: None
    # mode: delete
    # source-startip: None
    # type: None
    # block-size: None
    ##################################################
    ##################################################
    # permit-any-host: None
    # num-blocks-per-user: None
    # name: Ansible_pool4_121
    # adom: ansible
    # startip: None
    # arp-intf: None
    # comments: Created by ansible
    # source-endip: None
    # arp-reply: None
    # pba-timeout: None
    # endip: None
    # associated-interface: None
    # mode: delete
    # source-startip: None
    # type: None
    # block-size: None
    ##################################################
    ##################################################
    # source-endip: None
    # arp-intf: None
    # num-blocks-per-user: None
    # name: Ansible_pool4_fixed_port
    # adom: ansible
    # startip: None
    # comments: Created by ansible
    # permit-any-host: None
    # arp-reply: None
    # pba-timeout: None
    # endip: None
    # associated-interface: None
    # mode: delete
    # source-startip: None
    # type: None
    # block-size: None
    ##################################################
    ##################################################
    # permit-any-host: None
    # num-blocks-per-user: None
    # name: Ansible_pool4_port_block_allocation
    # adom: ansible
    # startip: None
    # arp-intf: None
    # comments: Created by ansible
    # source-endip: None
    # arp-reply: None
    # pba-timeout: None
    # endip: None
    # associated-interface: None
    # mode: delete
    # source-startip: None
    # type: None
    # block-size: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_fwobj_ippool.fmgr_fwobj_ippool_modify(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_fwobj_ippool.fmgr_fwobj_ippool_modify(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 3 #
    output = fmgr_fwobj_ippool.fmgr_fwobj_ippool_modify(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 4 #
    output = fmgr_fwobj_ippool.fmgr_fwobj_ippool_modify(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 5 #
    output = fmgr_fwobj_ippool.fmgr_fwobj_ippool_modify(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 6 #
    output = fmgr_fwobj_ippool.fmgr_fwobj_ippool_modify(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 7 #
    output = fmgr_fwobj_ippool.fmgr_fwobj_ippool_modify(fmg_instance, fixture_data[6]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 8 #
    output = fmgr_fwobj_ippool.fmgr_fwobj_ippool_modify(fmg_instance, fixture_data[7]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
