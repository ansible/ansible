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
    from ansible.modules.network.fortimanager import fmgr_fwobj_address
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


def test_fmgr_fwobj_ipv4(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)

    paramgram_used = {'comment': 'Dev Example for Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, test123, test321',
                      'ipv4': 'fqdn', 'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': None, 'start-ip': None, 'name': 'Bluesnews', 'country': None,
                      'ipv4addr': None, 'fqdn': 'bluesnews.com', 'multicast': None, 'associated-interface': None,
                      'mode': 'add', 'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev Example for Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, test123, test321
    # ipv4: fqdn
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: Bluesnews
    # country: None
    # ipv4addr: None
    # fqdn: bluesnews.com
    # multicast: None
    # associated-interface: None
    # mode: add
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Dev Example for Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': '*.myds.com',
                      'tags': 'ansible, ipv4, test123, test321', 'ipv4': 'wildcard-fqdn', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'Synology myds DDNS service', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'add',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev Example for Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: *.myds.com
    # tags: ansible, ipv4, test123, test321
    # ipv4: wildcard-fqdn
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: Synology myds DDNS service
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: add
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Dev Example for Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ipv4, test123, test321',
                      'ipv4': 'geography', 'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': None, 'start-ip': None, 'name': 'ansible_geo', 'country': 'US',
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'add',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev Example for Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ipv4, test123, test321
    # ipv4: geography
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_geo
    # country: US
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: add
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Dev Example for Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, test123, test321',
                      'ipv4': 'wildcard', 'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_wildCard',
                      'country': None, 'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None,
                      'mode': 'add', 'wildcard': '10.7.220.0/24', 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev Example for Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, test123, test321
    # ipv4: wildcard
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_wildCard
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: add
    # wildcard: 10.7.220.0/24
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Ansible is fun! Paramgram!', 'obj-id': None, 'color': '26', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, object',
                      'ipv4': 'ipmask', 'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_ipMask2',
                      'country': None, 'ipv4addr': '10.7.220.30/32', 'fqdn': None, 'multicast': None,
                      'associated-interface': None, 'mode': 'delete', 'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Ansible is fun! Paramgram!
    # obj-id: None
    # color: 26
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, object
    # ipv4: ipmask
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_ipMask2
    # country: None
    # ipv4addr: 10.7.220.30/32
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == -3
    paramgram_used = {'comment': 'Ansible more options', 'obj-id': None, 'color': '6', 'group_name': None,
                      'allow-routing': 'enable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, object',
                      'ipv4': 'ipmask', 'ipv6': None, 'cache-ttl': '180', 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_MORE',
                      'country': None, 'ipv4addr': '10.7.220.41/32', 'fqdn': None, 'multicast': None,
                      'associated-interface': 'port1', 'mode': 'set', 'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Ansible more options
    # obj-id: None
    # color: 6
    # group_name: None
    # allow-routing: enable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, object
    # ipv4: ipmask
    # ipv6: None
    # cache-ttl: 180
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_MORE
    # country: None
    # ipv4addr: 10.7.220.41/32
    # fqdn: None
    # multicast: None
    # associated-interface: port1
    # mode: set
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Dev Example for Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, test123, test321',
                      'ipv4': 'iprange', 'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': '10.7.220.50', 'start-ip': '10.7.220.1',
                      'name': 'ansible_v4Obj_Range', 'country': None, 'ipv4addr': None, 'fqdn': None, 'multicast': None,
                      'associated-interface': None, 'mode': 'set', 'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev Example for Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, test123, test321
    # ipv4: iprange
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: 10.7.220.50
    # start-ip: 10.7.220.1
    # name: ansible_v4Obj_Range
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: set
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Dev Example for Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, test123, test321',
                      'ipv4': 'iprange', 'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': '10.7.220.150', 'start-ip': '10.7.220.100',
                      'name': 'ansible_v4Obj_Range2', 'country': None, 'ipv4addr': None, 'fqdn': None,
                      'multicast': None, 'associated-interface': None, 'mode': 'set', 'wildcard': None,
                      'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev Example for Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, test123, test321
    # ipv4: iprange
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: 10.7.220.150
    # start-ip: 10.7.220.100
    # name: ansible_v4Obj_Range2
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: set
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Dev Example for Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, test123, test321',
                      'ipv4': 'ipmask', 'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_Subnet1',
                      'country': None, 'ipv4addr': '10.7.220.0/25', 'fqdn': None, 'multicast': None,
                      'associated-interface': None, 'mode': 'add', 'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev Example for Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, test123, test321
    # ipv4: ipmask
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_Subnet1
    # country: None
    # ipv4addr: 10.7.220.0/25
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: add
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Dev Example for Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, test123, test321',
                      'ipv4': 'ipmask', 'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_Subnet2',
                      'country': None, 'ipv4addr': '10.7.220.128/255.255.255.128', 'fqdn': None, 'multicast': None,
                      'associated-interface': None, 'mode': 'add', 'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev Example for Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, test123, test321
    # ipv4: ipmask
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_Subnet2
    # country: None
    # ipv4addr: 10.7.220.128/255.255.255.128
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: add
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': '22', 'group_name': 'ansibleIPv4Group',
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'group', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': 'Bluesnews, ansible_v4Obj_Range',
                      'visibility': 'enable', 'end-ip': None, 'start-ip': None, 'name': None, 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'add',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: ansibleIPv4Group
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: group
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: Bluesnews, ansible_v4Obj_Range
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: None
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: add
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': 'ansibleIPv4Group',
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'group', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': None, 'country': None, 'ipv4addr': None, 'fqdn': None,
                      'multicast': None, 'associated-interface': None, 'mode': 'delete', 'wildcard': None,
                      'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: ansibleIPv4Group
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: group
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: None
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'iprange', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_Range', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: iprange
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_Range
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'iprange', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_MORE', 'country': None, 'ipv4addr': None,
                      'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete', 'wildcard': None,
                      'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: iprange
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_MORE
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'iprange', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_ipMask2', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: iprange
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_ipMask2
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == -3
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'iprange', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_Range2', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: iprange
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_Range2
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'ipmask', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_ipMask', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: ipmask
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_ipMask
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == -3
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'ipmask', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_Subnet2', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: ipmask
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_Subnet2
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'ipmask', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_Subnet1', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: ipmask
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_Subnet1
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'wildcard', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_v4Obj_wildCard', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: wildcard
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v4Obj_wildCard
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'wildcard-fqdn',
                      'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'Synology myds DDNS service', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: wildcard-fqdn
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: Synology myds DDNS service
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'fqdn', 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'Bluesnews', 'country': None, 'ipv4addr': None,
                      'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete', 'wildcard': None,
                      'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: fqdn
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: Bluesnews
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': 'geography',
                      'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_geo', 'country': None, 'ipv4addr': None,
                      'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete', 'wildcard': None,
                      'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv4(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: geography
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_geo
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0


def test_fmgr_fwobj_ipv6(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)

    paramgram_used = {'comment': 'Dev Example for Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, test123, test321',
                      'ipv4': None, 'ipv6': 'ip', 'cache-ttl': None, 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': None, 'start-ip': None, 'name': 'ansible_v6Obj',
                      'country': None, 'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None,
                      'mode': 'add', 'wildcard': None, 'ipv6addr': '2001:0db8:85a3:0000:0000:8a2e:0370:7334'}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv6(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev Example for Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, test123, test321
    # ipv4: None
    # ipv6: ip
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v6Obj
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: add
    # wildcard: None
    # ipv6addr: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Dev Example for Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, test123, test321',
                      'ipv4': None, 'ipv6': 'iprange', 'cache-ttl': None, 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': '2001:0db8:85a3:0000:0000:8a2e:0370:7446',
                      'start-ip': '2001:0db8:85a3:0000:0000:8a2e:0370:7334', 'name': 'ansible_v6Obj_Range',
                      'country': None, 'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None,
                      'mode': 'add', 'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv6(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev Example for Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, test123, test321
    # ipv4: None
    # ipv6: iprange
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: 2001:0db8:85a3:0000:0000:8a2e:0370:7446
    # start-ip: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
    # name: ansible_v6Obj_Range
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: add
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'test123 comment', 'obj-id': None, 'color': '22', 'group_name': 'ansibleIPv6Group',
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, test123, test321',
                      'ipv4': None, 'ipv6': 'group', 'cache-ttl': None, 'adom': 'ansible',
                      'group_members': 'ansible_v6Obj_Range, ansible_v6Obj', 'visibility': 'enable', 'end-ip': None,
                      'start-ip': None, 'name': None, 'country': None, 'ipv4addr': None, 'fqdn': None,
                      'multicast': None, 'associated-interface': None, 'mode': 'add', 'wildcard': None,
                      'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv6(fmg_instance, paramgram_used)
    ##################################################
    # comment: test123 comment
    # obj-id: None
    # color: 22
    # group_name: ansibleIPv6Group
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, test123, test321
    # ipv4: None
    # ipv6: group
    # cache-ttl: None
    # adom: ansible
    # group_members: ansible_v6Obj_Range, ansible_v6Obj
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: None
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: add
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': 'ansibleIPv6Group',
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': None, 'ipv6': 'group',
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': None, 'country': None, 'ipv4addr': None, 'fqdn': None,
                      'multicast': None, 'associated-interface': None, 'mode': 'delete', 'wildcard': None,
                      'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv6(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: ansibleIPv6Group
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: None
    # ipv6: group
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: None
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': None, 'ipv6': 'iprange',
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_v6Obj_Range', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete',
                      'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv6(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: None
    # ipv6: iprange
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v6Obj_Range
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': None, 'ipv6': 'ip',
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_v6Obj', 'country': None, 'ipv4addr': None,
                      'fqdn': None, 'multicast': None, 'associated-interface': None, 'mode': 'delete', 'wildcard': None,
                      'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_ipv6(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: None
    # ipv6: ip
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_v6Obj
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: None
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0


def test_fmgr_fwobj_multicast(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)

    paramgram_used = {'comment': 'Dev by Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'blahBlahBlah', 'ipv4': None,
                      'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': '224.0.0.251', 'start-ip': '224.0.0.251', 'name': 'ansible_multicastrange',
                      'country': None, 'ipv4addr': None, 'fqdn': None, 'multicast': 'multicastrange',
                      'associated-interface': None, 'mode': 'add', 'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_multicast(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: blahBlahBlah
    # ipv4: None
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: 224.0.0.251
    # start-ip: 224.0.0.251
    # name: ansible_multicastrange
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: multicastrange
    # associated-interface: None
    # mode: add
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Dev Example for Ansible', 'obj-id': None, 'color': '22', 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': 'ansible, ipv4, test123, test321',
                      'ipv4': None, 'ipv6': None, 'cache-ttl': None, 'adom': 'ansible', 'group_members': None,
                      'visibility': 'enable', 'end-ip': None, 'start-ip': None, 'name': 'ansible_broadcastSubnet',
                      'country': None, 'ipv4addr': '10.7.220.0/24', 'fqdn': None, 'multicast': 'broadcastmask',
                      'associated-interface': None, 'mode': 'add', 'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_multicast(fmg_instance, paramgram_used)
    ##################################################
    # comment: Dev Example for Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: ansible, ipv4, test123, test321
    # ipv4: None
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_broadcastSubnet
    # country: None
    # ipv4addr: 10.7.220.0/24
    # fqdn: None
    # multicast: broadcastmask
    # associated-interface: None
    # mode: add
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': None, 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_broadcastSubnet', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': 'broadcastmask', 'associated-interface': None,
                      'mode': 'delete', 'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_multicast(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: None
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_broadcastSubnet
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: broadcastmask
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
    paramgram_used = {'comment': 'Created by Ansible', 'obj-id': None, 'color': 22, 'group_name': None,
                      'allow-routing': 'disable', 'wildcard-fqdn': None, 'tags': None, 'ipv4': None, 'ipv6': None,
                      'cache-ttl': None, 'adom': 'ansible', 'group_members': None, 'visibility': 'enable',
                      'end-ip': None, 'start-ip': None, 'name': 'ansible_multicastrange', 'country': None,
                      'ipv4addr': None, 'fqdn': None, 'multicast': 'multicastrange', 'associated-interface': None,
                      'mode': 'delete', 'wildcard': None, 'ipv6addr': None}
    output = fmgr_fwobj_address.fmgr_fwobj_multicast(fmg_instance, paramgram_used)
    ##################################################
    # comment: Created by Ansible
    # obj-id: None
    # color: 22
    # group_name: None
    # allow-routing: disable
    # wildcard-fqdn: None
    # tags: None
    # ipv4: None
    # ipv6: None
    # cache-ttl: None
    # adom: ansible
    # group_members: None
    # visibility: enable
    # end-ip: None
    # start-ip: None
    # name: ansible_multicastrange
    # country: None
    # ipv4addr: None
    # fqdn: None
    # multicast: multicastrange
    # associated-interface: None
    # mode: delete
    # wildcard: None
    # ipv6addr: None
    ##################################################
    assert output['raw_response']['status']['code'] == 0
