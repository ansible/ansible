#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ce_bgp
version_added: "2.4"
short_description: Manages BGP configuration on HUAWEI CloudEngine switches.
description:
    - Manages BGP configurations on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@CloudEngine-Ansible)
options:
    state:
        description:
            - Specify desired state of the resource.
        default: present
        choices: ['present','absent']
    as_number:
        description:
            - Local AS number.
              The value is a string of 1 to 11 characters.
    graceful_restart:
        description:
            - Enable GR of the BGP speaker in the specified address family, peer address, or peer group.
        default: no_use
        choices: ['no_use','true','false']
    time_wait_for_rib:
        description:
            - Period of waiting for the End-Of-RIB flag.
              The value is an integer ranging from 3 to 3000. The default value is 600.
    as_path_limit:
        description:
            - Maximum number of AS numbers in the AS_Path attribute. The default value is 255.
    check_first_as:
        description:
            - Check the first AS in the AS_Path of the update messages from EBGP peers.
        default: no_use
        choices: ['no_use','true','false']
    confed_id_number:
        description:
            - Confederation ID.
              The value is a string of 1 to 11 characters.
    confed_nonstanded:
        description:
            - Configure the device to be compatible with devices in a nonstandard confederation.
        default: no_use
        choices: ['no_use','true','false']
    bgp_rid_auto_sel:
        description:
            - The function to automatically select router IDs for all VPN BGP instances is enabled.
        default: no_use
        choices: ['no_use','true','false']
    keep_all_routes:
        description:
            - If the value is true, the system stores all route update messages received from all peers (groups) after
              BGP connection setup.
              If the value is false, the system stores only BGP update messages that are received from peers and pass
              the configured import policy.
        default: no_use
        choices: ['no_use','true','false']
    memory_limit:
        description:
            - Support BGP RIB memory protection.
        default: no_use
        choices: ['no_use','true','false']
    gr_peer_reset:
        description:
            - Peer disconnection through GR.
        default: no_use
        choices: ['no_use','true','false']
    is_shutdown:
        description:
            - Interrupt BGP all neighbor.
        default: no_use
        choices: ['no_use','true','false']
    suppress_interval:
        description:
            - Suppress interval.
    hold_interval:
        description:
            - Hold interval.
    clear_interval:
        description:
            - Clear interval.
    confed_peer_as_num:
        description:
            - Confederation AS number, in two-byte or four-byte format.
              The value is a string of 1 to 11 characters.
    vrf_name:
        description:
            - Name of a BGP instance. The name is a case-sensitive string of characters.
    vrf_rid_auto_sel:
        description:
            - If the value is true, VPN BGP instances are enabled to automatically select router IDs.
              If the value is false, VPN BGP instances are disabled from automatically selecting router IDs.
        default: no_use
        choices: ['no_use','true','false']
    router_id:
        description:
            - ID of a router that is in IPv4 address format.
    keepalive_time:
        description:
            - If the value of a timer changes, the BGP peer relationship between the routers is disconnected.
              The value is an integer ranging from 0 to 21845. The default value is 60.
    hold_time:
        description:
            - Hold time, in seconds. The value of the hold time can be 0 or range from 3 to 65535.
    min_hold_time:
        description:
            - Min hold time, in seconds. The value of the hold time can be 0 or range from 20 to 65535.
    conn_retry_time:
        description:
            - ConnectRetry interval. The value is an integer, in seconds. The default value is 32s.
    ebgp_if_sensitive:
        description:
            - If the value is true, After the fast EBGP interface awareness function is enabled, EBGP sessions on
              an interface are deleted immediately when the interface goes Down.
              If the value is  false, After the fast EBGP interface awareness function is enabled, EBGP sessions
              on an interface are not deleted immediately when the interface goes Down.
        default: no_use
        choices: ['no_use','true','false']
    default_af_type:
        description:
            - Type of a created address family, which can be IPv4 unicast or IPv6 unicast.
              The default type is IPv4 unicast.
        choices: ['ipv4uni','ipv6uni']
'''

EXAMPLES = '''

- name: CloudEngine BGP test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  - name: "Enable BGP"
    ce_bgp:
      state: present
      as_number: 100
      confed_id_number: 250
      provider: "{{ cli }}"

  - name: "Disable BGP"
    ce_bgp:
      state: absent
      as_number: 100
      confed_id_number: 250
      provider: "{{ cli }}"

  - name: "Create confederation peer AS num"
    ce_bgp:
      state: present
      confed_peer_as_num: 260
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"as_number": "100", state": "present"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"bgp_enable": [["100"], ["true"]]}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"bgp_enable": [["100"], ["true"]]}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["bgp 100"]
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec


SUCCESS = """success"""
FAILED = """failed"""


# get bgp enable
CE_GET_BGP_ENABLE = """
    <filter type="subtree">
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpSite>
            <bgpEnable></bgpEnable>
            <asNumber></asNumber>
          </bgpSite>
        </bgpcomm>
      </bgp>
    </filter>
"""

CE_GET_BGP_ENABLE_HEADER = """
    <filter type="subtree">
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpSite>
"""

CE_GET_BGP_ENABLE_TAIL = """
          </bgpSite>
        </bgpcomm>
      </bgp>
    </filter>
"""

# merge bgp enable
CE_MERGE_BGP_ENABLE_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpSite operation="merge">
"""
CE_MERGE_BGP_ENABLE_TAIL = """
          </bgpSite>
        </bgpcomm>
      </bgp>
    </config>
"""

# get bgp confederation peer as
CE_GET_BGP_CONFED_PEER_AS = """
    <filter type="subtree">
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpConfedPeerAss>
            <bgpConfedPeerAs>
              <confedPeerAsNum></confedPeerAsNum>
            </bgpConfedPeerAs>
          </bgpConfedPeerAss>
        </bgpcomm>
      </bgp>
    </filter>
"""

# merge bgp confederation peer as
CE_MERGE_BGP_CONFED_PEER_AS = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpConfedPeerAss>
            <bgpConfedPeerAs operation="merge">
              <confedPeerAsNum>%s</confedPeerAsNum>
            </bgpConfedPeerAs>
          </bgpConfedPeerAss>
        </bgpcomm>
      </bgp>
    </config>
"""

# create bgp confederation peer as
CE_CREATE_BGP_CONFED_PEER_AS = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpConfedPeerAss>
            <bgpConfedPeerAs operation="create">
              <confedPeerAsNum>%s</confedPeerAsNum>
            </bgpConfedPeerAs>
          </bgpConfedPeerAss>
        </bgpcomm>
      </bgp>
    </config>
"""

# delete bgp confederation peer as
CE_DELETE_BGP_CONFED_PEER_AS = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpConfedPeerAss>
            <bgpConfedPeerAs operation="delete">
              <confedPeerAsNum>%s</confedPeerAsNum>
            </bgpConfedPeerAs>
          </bgpConfedPeerAss>
        </bgpcomm>
      </bgp>
    </config>
"""

# get bgp instance
CE_GET_BGP_INSTANCE = """
    <filter type="subtree">
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName></vrfName>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </filter>
"""

# get bgp instance
CE_GET_BGP_INSTANCE_HEADER = """
    <filter type="subtree">
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
"""
CE_GET_BGP_INSTANCE_TAIL = """
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </filter>
"""

# merge bgp instance
CE_MERGE_BGP_INSTANCE_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf operation="merge">
"""
CE_MERGE_BGP_INSTANCE_TAIL = """
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# create bgp instance
CE_CREATE_BGP_INSTANCE_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf operation="create">
"""
CE_CREATE_BGP_INSTANCE_TAIL = """
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# delete bgp instance
CE_DELETE_BGP_INSTANCE_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf operation="delete">
"""
CE_DELETE_BGP_INSTANCE_TAIL = """
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""


def check_ip_addr(**kwargs):
    """ check_ip_addr """

    ipaddr = kwargs["ipaddr"]

    addr = ipaddr.strip().split('.')

    if len(addr) != 4:
        return FAILED

    for i in range(4):
        addr[i] = int(addr[i])

        if addr[i] <= 255 and addr[i] >= 0:
            pass
        else:
            return FAILED
    return SUCCESS


def check_bgp_enable_args(**kwargs):
    """ check_bgp_enable_args """

    module = kwargs["module"]

    need_cfg = False

    as_number = module.params['as_number']
    if as_number:
        if len(as_number) > 11 or len(as_number) == 0:
            module.fail_json(
                msg='Error: The len of as_number %s is out of [1 - 11].' % as_number)
        else:
            need_cfg = True

    return need_cfg


def check_bgp_confed_args(**kwargs):
    """ check_bgp_confed_args """

    module = kwargs["module"]

    need_cfg = False

    confed_peer_as_num = module.params['confed_peer_as_num']
    if confed_peer_as_num:
        if len(confed_peer_as_num) > 11 or len(confed_peer_as_num) == 0:
            module.fail_json(
                msg='Error: The len of confed_peer_as_num %s is out of [1 - 11].' % confed_peer_as_num)
        else:
            need_cfg = True

    return need_cfg


class Bgp(object):
    """ Manages BGP configuration """

    def netconf_get_config(self, **kwargs):
        """ netconf_get_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        xml_str = get_nc_config(module, conf_str)

        return xml_str

    def netconf_set_config(self, **kwargs):
        """ netconf_set_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        xml_str = set_nc_config(module, conf_str)

        return xml_str

    def check_bgp_enable_other_args(self, **kwargs):
        """ check_bgp_enable_other_args """

        module = kwargs["module"]
        state = module.params['state']
        result = dict()
        need_cfg = False

        graceful_restart = module.params['graceful_restart']
        if graceful_restart != 'no_use':

            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<gracefulRestart></gracefulRestart>" + CE_GET_BGP_ENABLE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<gracefulRestart>(.*)</gracefulRestart>.*', recv_xml)

                if re_find:
                    result["graceful_restart"] = re_find
                    if re_find[0] != graceful_restart:
                        need_cfg = True
                else:
                    need_cfg = True

        time_wait_for_rib = module.params['time_wait_for_rib']
        if time_wait_for_rib:
            if int(time_wait_for_rib) > 3000 or int(time_wait_for_rib) < 3:
                module.fail_json(
                    msg='Error: The time_wait_for_rib %s is out of [3 - 3000].' % time_wait_for_rib)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<timeWaitForRib></timeWaitForRib>" + CE_GET_BGP_ENABLE_TAIL
                recv_xml = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in recv_xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<timeWaitForRib>(.*)</timeWaitForRib>.*', recv_xml)

                        if re_find:
                            result["time_wait_for_rib"] = re_find
                            if re_find[0] != time_wait_for_rib:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in recv_xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<timeWaitForRib>(.*)</timeWaitForRib>.*', recv_xml)

                        if re_find:
                            result["time_wait_for_rib"] = re_find
                            if re_find[0] == time_wait_for_rib:
                                need_cfg = True

        as_path_limit = module.params['as_path_limit']
        if as_path_limit:
            if int(as_path_limit) > 2000 or int(as_path_limit) < 1:
                module.fail_json(
                    msg='Error: The as_path_limit %s is out of [1 - 2000].' % as_path_limit)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<asPathLimit></asPathLimit>" + CE_GET_BGP_ENABLE_TAIL
                recv_xml = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in recv_xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<asPathLimit>(.*)</asPathLimit>.*', recv_xml)

                        if re_find:
                            result["as_path_limit"] = re_find
                            if re_find[0] != as_path_limit:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in recv_xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<asPathLimit>(.*)</asPathLimit>.*', recv_xml)

                        if re_find:
                            result["as_path_limit"] = re_find
                            if re_find[0] == as_path_limit:
                                need_cfg = True

        check_first_as = module.params['check_first_as']
        if check_first_as != 'no_use':
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<checkFirstAs></checkFirstAs>" + CE_GET_BGP_ENABLE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<checkFirstAs>(.*)</checkFirstAs>.*', recv_xml)

                if re_find:
                    result["check_first_as"] = re_find
                    if re_find[0] != check_first_as:
                        need_cfg = True
                else:
                    need_cfg = True

        confed_id_number = module.params['confed_id_number']
        if confed_id_number:
            if len(confed_id_number) > 11 or len(confed_id_number) == 0:
                module.fail_json(
                    msg='Error: The len of confed_id_number %s is out of [1 - 11].' % confed_id_number)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<confedIdNumber></confedIdNumber>" + CE_GET_BGP_ENABLE_TAIL
                recv_xml = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in recv_xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<confedIdNumber>(.*)</confedIdNumber>.*', recv_xml)

                        if re_find:
                            result["confed_id_number"] = re_find
                            if re_find[0] != confed_id_number:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in recv_xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<confedIdNumber>(.*)</confedIdNumber>.*', recv_xml)

                        if re_find:
                            result["confed_id_number"] = re_find
                            if re_find[0] == confed_id_number:
                                need_cfg = True

        confed_nonstanded = module.params['confed_nonstanded']
        if confed_nonstanded != 'no_use':
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<confedNonstanded></confedNonstanded>" + CE_GET_BGP_ENABLE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<confedNonstanded>(.*)</confedNonstanded>.*', recv_xml)

                if re_find:
                    result["confed_nonstanded"] = re_find
                    if re_find[0] != confed_nonstanded:
                        need_cfg = True
                else:
                    need_cfg = True

        bgp_rid_auto_sel = module.params['bgp_rid_auto_sel']
        if bgp_rid_auto_sel != 'no_use':
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<bgpRidAutoSel></bgpRidAutoSel>" + CE_GET_BGP_ENABLE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<bgpRidAutoSel>(.*)</bgpRidAutoSel>.*', recv_xml)

                if re_find:
                    result["bgp_rid_auto_sel"] = re_find
                    if re_find[0] != bgp_rid_auto_sel:
                        need_cfg = True
                else:
                    need_cfg = True

        keep_all_routes = module.params['keep_all_routes']
        if keep_all_routes != 'no_use':
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<keepAllRoutes></keepAllRoutes>" + CE_GET_BGP_ENABLE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<keepAllRoutes>(.*)</keepAllRoutes>.*', recv_xml)

                if re_find:
                    result["keep_all_routes"] = re_find
                    if re_find[0] != keep_all_routes:
                        need_cfg = True
                else:
                    need_cfg = True

        memory_limit = module.params['memory_limit']
        if memory_limit != 'no_use':
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<memoryLimit></memoryLimit>" + CE_GET_BGP_ENABLE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<memoryLimit>(.*)</memoryLimit>.*', recv_xml)

                if re_find:
                    result["memory_limit"] = re_find
                    if re_find[0] != memory_limit:
                        need_cfg = True
                else:
                    need_cfg = True

        gr_peer_reset = module.params['gr_peer_reset']
        if gr_peer_reset != 'no_use':
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<grPeerReset></grPeerReset>" + CE_GET_BGP_ENABLE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<grPeerReset>(.*)</grPeerReset>.*', recv_xml)

                if re_find:
                    result["gr_peer_reset"] = re_find
                    if re_find[0] != gr_peer_reset:
                        need_cfg = True
                else:
                    need_cfg = True

        is_shutdown = module.params['is_shutdown']
        if is_shutdown != 'no_use':
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<isShutdown></isShutdown>" + CE_GET_BGP_ENABLE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isShutdown>(.*)</isShutdown>.*', recv_xml)

                if re_find:
                    result["is_shutdown"] = re_find
                    if re_find[0] != is_shutdown:
                        need_cfg = True
                else:
                    need_cfg = True

        suppress_interval = module.params['suppress_interval']
        hold_interval = module.params['hold_interval']
        clear_interval = module.params['clear_interval']
        if suppress_interval:

            if not hold_interval or not clear_interval:
                module.fail_json(
                    msg='Error: Please input suppress_interval hold_interval clear_interval at the same time.')

            if int(suppress_interval) > 65535 or int(suppress_interval) < 1:
                module.fail_json(
                    msg='Error: The suppress_interval %s is out of [1 - 65535].' % suppress_interval)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<suppressInterval></suppressInterval>" + CE_GET_BGP_ENABLE_TAIL
                recv_xml = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in recv_xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<suppressInterval>(.*)</suppressInterval>.*', recv_xml)

                        if re_find:
                            result["suppress_interval"] = re_find
                            if re_find[0] != suppress_interval:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in recv_xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<suppressInterval>(.*)</suppressInterval>.*', recv_xml)

                        if re_find:
                            result["suppress_interval"] = re_find
                            if re_find[0] == suppress_interval:
                                need_cfg = True

        if hold_interval:

            if not suppress_interval or not clear_interval:
                module.fail_json(
                    msg='Error: Please input suppress_interval hold_interval clear_interval at the same time.')

            if int(hold_interval) > 65535 or int(hold_interval) < 1:
                module.fail_json(
                    msg='Error: The hold_interval %s is out of [1 - 65535].' % hold_interval)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<holdInterval></holdInterval>" + CE_GET_BGP_ENABLE_TAIL
                recv_xml = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in recv_xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<holdInterval>(.*)</holdInterval>.*', recv_xml)

                        if re_find:
                            result["hold_interval"] = re_find
                            if re_find[0] != hold_interval:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in recv_xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<holdInterval>(.*)</holdInterval>.*', recv_xml)

                        if re_find:
                            result["hold_interval"] = re_find
                            if re_find[0] == hold_interval:
                                need_cfg = True

        if clear_interval:

            if not suppress_interval or not hold_interval:
                module.fail_json(
                    msg='Error: Please input suppress_interval hold_interval clear_interval at the same time.')

            if int(clear_interval) > 65535 or int(clear_interval) < 1:
                module.fail_json(
                    msg='Error: The clear_interval %s is out of [1 - 65535].' % clear_interval)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<clearInterval></clearInterval>" + CE_GET_BGP_ENABLE_TAIL
                recv_xml = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in recv_xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<clearInterval>(.*)</clearInterval>.*', recv_xml)

                        if re_find:
                            result["clear_interval"] = re_find
                            if re_find[0] != clear_interval:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in recv_xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<clearInterval>(.*)</clearInterval>.*', recv_xml)

                        if re_find:
                            result["clear_interval"] = re_find
                            if re_find[0] == clear_interval:
                                need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_bgp_instance_args(self, **kwargs):
        """ check_bgp_instance_args """

        module = kwargs["module"]
        state = module.params['state']
        need_cfg = False

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='the len of vrf_name %s is out of [1 - 31].' % vrf_name)
            conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                "<vrfName></vrfName>" + CE_GET_BGP_INSTANCE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            check_vrf_name = (vrf_name)

            if state == "present":
                if "<data/>" in recv_xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<vrfName>(.*)</vrfName>.*', recv_xml)

                    if re_find:
                        if check_vrf_name not in re_find:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in recv_xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<vrfName>(.*)</vrfName>.*', recv_xml)

                    if re_find:
                        if check_vrf_name in re_find:
                            need_cfg = True

        return need_cfg

    def check_bgp_instance_other_args(self, **kwargs):
        """ check_bgp_instance_other_args """

        module = kwargs["module"]
        state = module.params['state']
        result = dict()
        need_cfg = False

        vrf_name = module.params['vrf_name']

        router_id = module.params['router_id']
        if router_id:

            if not vrf_name:
                module.fail_json(
                    msg='Error: Please input vrf_name.')

            if check_ip_addr(ipaddr=router_id) == FAILED:
                module.fail_json(
                    msg='Error: The router_id %s is invalid.' % router_id)

            conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                "<routerId></routerId>" + CE_GET_BGP_INSTANCE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in recv_xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<routerId>(.*)</routerId>.*', recv_xml)

                    if re_find:
                        result["router_id"] = re_find
                        if re_find[0] != router_id:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in recv_xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<routerId>(.*)</routerId>.*', recv_xml)

                    if re_find:
                        result["router_id"] = re_find
                        if re_find[0] == router_id:
                            need_cfg = True

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel != 'no_use':

            if not vrf_name:
                module.fail_json(
                    msg='Error: Please input vrf_name.')

            conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                "<vrfRidAutoSel></vrfRidAutoSel>" + CE_GET_BGP_INSTANCE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in recv_xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<vrfRidAutoSel>(.*)</vrfRidAutoSel>.*', recv_xml)

                    if re_find:
                        result["vrf_rid_auto_sel"] = re_find

                        if re_find[0] != vrf_rid_auto_sel:
                            need_cfg = True
                    else:
                        need_cfg = True

        keepalive_time = module.params['keepalive_time']
        if keepalive_time:

            if not vrf_name:
                module.fail_json(
                    msg='Error: Please input vrf_name.')

            if int(keepalive_time) > 21845 or int(keepalive_time) < 0:
                module.fail_json(
                    msg='keepalive_time %s is out of [0 - 21845].' % keepalive_time)
            else:
                conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                    "<keepaliveTime></keepaliveTime>" + CE_GET_BGP_INSTANCE_TAIL
                recv_xml = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in recv_xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<keepaliveTime>(.*)</keepaliveTime>.*', recv_xml)

                        if re_find:
                            result["keepalive_time"] = re_find
                            if re_find[0] != keepalive_time:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in recv_xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<keepaliveTime>(.*)</keepaliveTime>.*', recv_xml)

                        if re_find:
                            result["keepalive_time"] = re_find
                            if re_find[0] == keepalive_time:
                                need_cfg = True

        hold_time = module.params['hold_time']
        if hold_time:

            if not vrf_name:
                module.fail_json(
                    msg='Error: Please input vrf_name.')

            if int(hold_time) > 65535 or int(hold_time) < 3:
                module.fail_json(
                    msg='hold_time %s is out of [3 - 65535].' % hold_time)
            else:
                conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                    "<holdTime></holdTime>" + CE_GET_BGP_INSTANCE_TAIL
                recv_xml = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in recv_xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<holdTime>(.*)</holdTime>.*', recv_xml)

                        if re_find:
                            result["hold_time"] = re_find
                            if re_find[0] != hold_time:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in recv_xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<holdTime>(.*)</holdTime>.*', recv_xml)

                        if re_find:
                            result["hold_time"] = re_find
                            if re_find[0] == hold_time:
                                need_cfg = True

        min_hold_time = module.params['min_hold_time']
        if min_hold_time:

            if not vrf_name:
                module.fail_json(
                    msg='Error: Please input vrf_name.')

            if int(min_hold_time) != 0 and (int(min_hold_time) > 65535 or int(min_hold_time) < 20):
                module.fail_json(
                    msg='min_hold_time %s is out of [0, or 20 - 65535].' % min_hold_time)
            else:
                conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                    "<minHoldTime></minHoldTime>" + CE_GET_BGP_INSTANCE_TAIL
                recv_xml = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in recv_xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<minHoldTime>(.*)</minHoldTime>.*', recv_xml)

                        if re_find:
                            result["min_hold_time"] = re_find
                            if re_find[0] != min_hold_time:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in recv_xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<minHoldTime>(.*)</minHoldTime>.*', recv_xml)

                        if re_find:
                            result["min_hold_time"] = re_find
                            if re_find[0] == min_hold_time:
                                need_cfg = True

        conn_retry_time = module.params['conn_retry_time']
        if conn_retry_time:

            if not vrf_name:
                module.fail_json(
                    msg='Error: Please input vrf_name.')

            if int(conn_retry_time) > 65535 or int(conn_retry_time) < 1:
                module.fail_json(
                    msg='conn_retry_time %s is out of [1 - 65535].' % conn_retry_time)
            else:
                conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                    "<connRetryTime></connRetryTime>" + CE_GET_BGP_INSTANCE_TAIL
                recv_xml = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in recv_xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<connRetryTime>(.*)</connRetryTime>.*', recv_xml)

                        if re_find:
                            result["conn_retry_time"] = re_find
                            if re_find[0] != conn_retry_time:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in recv_xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<connRetryTime>(.*)</connRetryTime>.*', recv_xml)

                        if re_find:
                            result["conn_retry_time"] = re_find
                            if re_find[0] == conn_retry_time:
                                need_cfg = True
                        else:
                            pass

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive != 'no_use':

            if not vrf_name:
                module.fail_json(
                    msg='Error: Please input vrf_name.')

            conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                "<ebgpIfSensitive></ebgpIfSensitive>" + CE_GET_BGP_INSTANCE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in recv_xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<ebgpIfSensitive>(.*)</ebgpIfSensitive>.*', recv_xml)

                    if re_find:
                        result["ebgp_if_sensitive"] = re_find
                        if re_find[0] != ebgp_if_sensitive:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in recv_xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<ebgpIfSensitive>(.*)</ebgpIfSensitive>.*', recv_xml)

                    if re_find:
                        result["ebgp_if_sensitive"] = re_find
                        if re_find[0] == ebgp_if_sensitive:
                            need_cfg = True
                    else:
                        pass

        default_af_type = module.params['default_af_type']
        if default_af_type:

            if not vrf_name:
                module.fail_json(
                    msg='Error: Please input vrf_name.')

            conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                "<defaultAfType></defaultAfType>" + CE_GET_BGP_INSTANCE_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in recv_xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<defaultAfType>(.*)</defaultAfType>.*', recv_xml)

                    if re_find:
                        result["default_af_type"] = re_find
                        if re_find[0] != default_af_type:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in recv_xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<defaultAfType>(.*)</defaultAfType>.*', recv_xml)

                    if re_find:
                        result["default_af_type"] = re_find
                        if re_find[0] == default_af_type:
                            need_cfg = True
                    else:
                        pass

        result["need_cfg"] = need_cfg
        return result

    def get_bgp_enable(self, **kwargs):
        """ get_bgp_enable """

        module = kwargs["module"]

        conf_str = CE_GET_BGP_ENABLE

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<asNumber>(.*)</asNumber>.*\s*<bgpEnable>(.*)</bgpEnable>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_bgp_enable(self, **kwargs):
        """ merge_bgp_enable """

        module = kwargs["module"]
        conf_str = CE_MERGE_BGP_ENABLE_HEADER

        state = module.params['state']

        if state == "present":
            conf_str += "<bgpEnable>true</bgpEnable>"
        else:
            conf_str += "<bgpEnable>false</bgpEnable>"

        as_number = module.params['as_number']
        if as_number:
            conf_str += "<asNumber>%s</asNumber>" % as_number

        conf_str += CE_MERGE_BGP_ENABLE_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp enable failed.')

        cmds = []
        if state == "present":
            cmd = "bgp %s" % as_number
        else:
            cmd = "undo bgp %s" % as_number
        cmds.append(cmd)

        return cmds

    def merge_bgp_enable_other(self, **kwargs):
        """ merge_bgp_enable_other """

        module = kwargs["module"]
        conf_str = CE_MERGE_BGP_ENABLE_HEADER

        cmds = []

        graceful_restart = module.params['graceful_restart']
        if graceful_restart != 'no_use':
            conf_str += "<gracefulRestart>%s</gracefulRestart>" % graceful_restart

            if graceful_restart == "true":
                cmd = "graceful-restart"
            else:
                cmd = "undo graceful-restart"
            cmds.append(cmd)

        time_wait_for_rib = module.params['time_wait_for_rib']
        if time_wait_for_rib:
            conf_str += "<timeWaitForRib>%s</timeWaitForRib>" % time_wait_for_rib

            cmd = "graceful-restart timer wait-for-rib %s" % time_wait_for_rib
            cmds.append(cmd)

        as_path_limit = module.params['as_path_limit']
        if as_path_limit:
            conf_str += "<asPathLimit>%s</asPathLimit>" % as_path_limit

            cmd = "as-path-limit %s" % as_path_limit
            cmds.append(cmd)

        check_first_as = module.params['check_first_as']
        if check_first_as != 'no_use':
            conf_str += "<checkFirstAs>%s</checkFirstAs>" % check_first_as

            if check_first_as == "true":
                cmd = "check-first-as"
            else:
                cmd = "undo check-first-as"
            cmds.append(cmd)

        confed_id_number = module.params['confed_id_number']
        if confed_id_number:
            conf_str += "<confedIdNumber>%s</confedIdNumber>" % confed_id_number

            cmd = "confederation id %s" % confed_id_number
            cmds.append(cmd)

        confed_nonstanded = module.params['confed_nonstanded']
        if confed_nonstanded != 'no_use':
            conf_str += "<confedNonstanded>%s</confedNonstanded>" % confed_nonstanded

            if confed_nonstanded == "true":
                cmd = "confederation nonstandard"
            else:
                cmd = "undo confederation nonstandard"
            cmds.append(cmd)

        bgp_rid_auto_sel = module.params['bgp_rid_auto_sel']
        if bgp_rid_auto_sel != 'no_use':
            conf_str += "<bgpRidAutoSel>%s</bgpRidAutoSel>" % bgp_rid_auto_sel

            if bgp_rid_auto_sel == "true":
                cmd = "router-id vpn-instance auto-select"
            else:
                cmd = "undo router-id"
            cmds.append(cmd)

        keep_all_routes = module.params['keep_all_routes']
        if keep_all_routes != 'no_use':
            conf_str += "<keepAllRoutes>%s</keepAllRoutes>" % keep_all_routes

            if keep_all_routes == "true":
                cmd = "keep-all-routes"
            else:
                cmd = "undo keep-all-routes"
            cmds.append(cmd)

        memory_limit = module.params['memory_limit']
        if memory_limit != 'no_use':
            conf_str += "<memoryLimit>%s</memoryLimit>" % memory_limit

            if memory_limit == "true":
                cmd = "prefix memory-limit"
            else:
                cmd = "undo prefix memory-limit"
            cmds.append(cmd)

        gr_peer_reset = module.params['gr_peer_reset']
        if gr_peer_reset != 'no_use':
            conf_str += "<grPeerReset>%s</grPeerReset>" % gr_peer_reset

            if gr_peer_reset == "true":
                cmd = "graceful-restart peer-reset"
            else:
                cmd = "undo graceful-restart peer-reset"
            cmds.append(cmd)

        is_shutdown = module.params['is_shutdown']
        if is_shutdown != 'no_use':
            conf_str += "<isShutdown>%s</isShutdown>" % is_shutdown

            if is_shutdown == "true":
                cmd = "shutdown"
            else:
                cmd = "undo shutdown"
            cmds.append(cmd)

        suppress_interval = module.params['suppress_interval']
        hold_interval = module.params['hold_interval']
        clear_interval = module.params['clear_interval']
        if suppress_interval:
            conf_str += "<suppressInterval>%s</suppressInterval>" % suppress_interval

            cmd = "nexthop recursive-lookup restrain suppress-interval %s hold-interval %s " \
                  "clear-interval %s" % (suppress_interval, hold_interval, clear_interval)
            cmds.append(cmd)

        if hold_interval:
            conf_str += "<holdInterval>%s</holdInterval>" % hold_interval

        if clear_interval:
            conf_str += "<clearInterval>%s</clearInterval>" % clear_interval

        conf_str += CE_MERGE_BGP_ENABLE_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp enable failed.')

        return cmds

    def delete_bgp_enable_other(self, **kwargs):
        """ delete bgp enable other args """

        module = kwargs["module"]
        conf_str = CE_MERGE_BGP_ENABLE_HEADER

        cmds = []

        graceful_restart = module.params['graceful_restart']
        if graceful_restart != 'no_use':
            conf_str += "<gracefulRestart>%s</gracefulRestart>" % graceful_restart

            if graceful_restart == "true":
                cmd = "graceful-restart"
            else:
                cmd = "undo graceful-restart"
            cmds.append(cmd)

        time_wait_for_rib = module.params['time_wait_for_rib']
        if time_wait_for_rib:
            conf_str += "<timeWaitForRib>600</timeWaitForRib>"

            cmd = "undo graceful-restart timer wait-for-rib"
            cmds.append(cmd)

        as_path_limit = module.params['as_path_limit']
        if as_path_limit:
            conf_str += "<asPathLimit>255</asPathLimit>"

            cmd = "undo as-path-limit"
            cmds.append(cmd)

        check_first_as = module.params['check_first_as']
        if check_first_as != 'no_use':
            conf_str += "<checkFirstAs>%s</checkFirstAs>" % check_first_as

            if check_first_as == "true":
                cmd = "check-first-as"
            else:
                cmd = "undo check-first-as"
            cmds.append(cmd)

        confed_id_number = module.params['confed_id_number']
        if confed_id_number:
            conf_str += "<confedIdNumber></confedIdNumber>"

            cmd = "undo confederation id"
            cmds.append(cmd)

        confed_nonstanded = module.params['confed_nonstanded']
        if confed_nonstanded != 'no_use':
            conf_str += "<confedNonstanded>%s</confedNonstanded>" % confed_nonstanded

            if confed_nonstanded == "true":
                cmd = "confederation nonstandard"
            else:
                cmd = "undo confederation nonstandard"
            cmds.append(cmd)

        bgp_rid_auto_sel = module.params['bgp_rid_auto_sel']
        if bgp_rid_auto_sel != 'no_use':
            conf_str += "<bgpRidAutoSel>%s</bgpRidAutoSel>" % bgp_rid_auto_sel

            if bgp_rid_auto_sel == "true":
                cmd = "router-id vpn-instance auto-select"
            else:
                cmd = "undo router-id"
            cmds.append(cmd)

        keep_all_routes = module.params['keep_all_routes']
        if keep_all_routes != 'no_use':
            conf_str += "<keepAllRoutes>%s</keepAllRoutes>" % keep_all_routes

            if keep_all_routes == "true":
                cmd = "keep-all-routes"
            else:
                cmd = "undo keep-all-routes"
            cmds.append(cmd)

        memory_limit = module.params['memory_limit']
        if memory_limit != 'no_use':
            conf_str += "<memoryLimit>%s</memoryLimit>" % memory_limit

            if memory_limit == "true":
                cmd = "prefix memory-limit"
            else:
                cmd = "undo prefix memory-limit"
            cmds.append(cmd)

        gr_peer_reset = module.params['gr_peer_reset']
        if gr_peer_reset != 'no_use':
            conf_str += "<grPeerReset>%s</grPeerReset>" % gr_peer_reset

            if gr_peer_reset == "true":
                cmd = "graceful-restart peer-reset"
            else:
                cmd = "undo graceful-restart peer-reset"
            cmds.append(cmd)

        is_shutdown = module.params['is_shutdown']
        if is_shutdown != 'no_use':
            conf_str += "<isShutdown>%s</isShutdown>" % is_shutdown

            if is_shutdown == "true":
                cmd = "shutdown"
            else:
                cmd = "undo shutdown"
            cmds.append(cmd)

        suppress_interval = module.params['suppress_interval']
        hold_interval = module.params['hold_interval']
        clear_interval = module.params['clear_interval']
        if suppress_interval:
            conf_str += "<suppressInterval>60</suppressInterval>"

            cmd = "nexthop recursive-lookup restrain suppress-interval %s hold-interval %s " \
                  "clear-interval %s" % (suppress_interval, hold_interval, clear_interval)
            cmds.append(cmd)

        if hold_interval:
            conf_str += "<holdInterval>120</holdInterval>"

        if clear_interval:
            conf_str += "<clearInterval>600</clearInterval>"

        conf_str += CE_MERGE_BGP_ENABLE_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Delete bgp enable failed.')

        return cmds

    def get_bgp_confed_peer_as(self, **kwargs):
        """ get_bgp_confed_peer_as """

        module = kwargs["module"]

        conf_str = CE_GET_BGP_CONFED_PEER_AS

        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<confedPeerAsNum>(.*)</confedPeerAsNum>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_bgp_confed_peer_as(self, **kwargs):
        """ merge_bgp_confed_peer_as """

        module = kwargs["module"]
        confed_peer_as_num = module.params['confed_peer_as_num']

        conf_str = CE_MERGE_BGP_CONFED_PEER_AS % confed_peer_as_num

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp confed peer as failed.')

        cmds = []
        cmd = "confederation peer-as %s" % confed_peer_as_num
        cmds.append(cmd)

        return cmds

    def create_bgp_confed_peer_as(self, **kwargs):
        """ create_bgp_confed_peer_as """

        module = kwargs["module"]
        confed_peer_as_num = module.params['confed_peer_as_num']

        conf_str = CE_CREATE_BGP_CONFED_PEER_AS % confed_peer_as_num

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Create bgp confed peer as failed.')

        cmds = []
        cmd = "confederation peer-as %s" % confed_peer_as_num
        cmds.append(cmd)

        return cmds

    def delete_bgp_confed_peer_as(self, **kwargs):
        """ delete_bgp_confed_peer_as """

        module = kwargs["module"]
        confed_peer_as_num = module.params['confed_peer_as_num']

        conf_str = CE_DELETE_BGP_CONFED_PEER_AS % confed_peer_as_num

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Delete bgp confed peer as failed.')

        cmds = []
        cmd = "undo confederation peer-as %s" % confed_peer_as_num
        cmds.append(cmd)

        return cmds

    def get_bgp_instance(self, **kwargs):
        """ get_bgp_instance """

        module = kwargs["module"]
        conf_str = CE_GET_BGP_INSTANCE
        xml_str = self.netconf_get_config(module=module, conf_str=conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<vrfName>(.*)</vrfName>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_bgp_instance(self, **kwargs):
        """ merge_bgp_instance """

        module = kwargs["module"]
        conf_str = CE_MERGE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        conf_str += "<vrfName>%s</vrfName>" % vrf_name

        conf_str += CE_MERGE_BGP_INSTANCE_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp instance failed.')

    def create_bgp_instance(self, **kwargs):
        """ create_bgp_instance """

        module = kwargs["module"]
        conf_str = CE_CREATE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        conf_str += CE_CREATE_BGP_INSTANCE_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Create bgp instance failed.')

        cmds = []

        if vrf_name != "_public_":
            cmd = "ipv4-family vpn-instance %s" % vrf_name
            cmds.append(cmd)

        return cmds

    def delete_bgp_instance(self, **kwargs):
        """ delete_bgp_instance """

        module = kwargs["module"]
        conf_str = CE_DELETE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        conf_str += CE_DELETE_BGP_INSTANCE_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Delete bgp instance failed.')

        cmds = []
        if vrf_name != "_public_":
            cmd = "undo ipv4-family vpn-instance %s" % vrf_name
            cmds.append(cmd)

        return cmds

    def merge_bgp_instance_other(self, **kwargs):
        """ merge_bgp_instance_other """

        module = kwargs["module"]
        conf_str = CE_MERGE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        conf_str += "<vrfName>%s</vrfName>" % vrf_name

        cmds = []

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel != 'no_use':
            conf_str += "<vrfRidAutoSel>%s</vrfRidAutoSel>" % vrf_rid_auto_sel

            if vrf_rid_auto_sel == "true":
                cmd = "router-id vpn-instance auto-select"
            else:
                cmd = "undo router-id vpn-instance auto-select"
            cmds.append(cmd)

        router_id = module.params['router_id']
        if router_id:
            conf_str += "<routerId>%s</routerId>" % router_id

            cmd = "router-id %s" % router_id
            cmds.append(cmd)

        keepalive_time = module.params['keepalive_time']
        if keepalive_time:
            conf_str += "<keepaliveTime>%s</keepaliveTime>" % keepalive_time

            cmd = "timer keepalive %s" % keepalive_time
            cmds.append(cmd)

        hold_time = module.params['hold_time']
        if hold_time:
            conf_str += "<holdTime>%s</holdTime>" % hold_time

            cmd = "timer hold %s" % hold_time
            cmds.append(cmd)

        min_hold_time = module.params['min_hold_time']
        if min_hold_time:
            conf_str += "<minHoldTime>%s</minHoldTime>" % min_hold_time

            cmd = "timer min-holdtime %s" % min_hold_time
            cmds.append(cmd)

        conn_retry_time = module.params['conn_retry_time']
        if conn_retry_time:
            conf_str += "<connRetryTime>%s</connRetryTime>" % conn_retry_time

            cmd = "timer connect-retry %s" % conn_retry_time
            cmds.append(cmd)

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive != 'no_use':
            conf_str += "<ebgpIfSensitive>%s</ebgpIfSensitive>" % ebgp_if_sensitive

            if ebgp_if_sensitive == "true":
                cmd = "ebgp-interface-sensitive"
            else:
                cmd = "undo ebgp-interface-sensitive"
            cmds.append(cmd)

        default_af_type = module.params['default_af_type']
        if default_af_type:
            conf_str += "<defaultAfType>%s</defaultAfType>" % default_af_type

            if vrf_name != "_public_":
                if default_af_type == "ipv6uni":
                    cmd = "ipv6-family vpn-instance %s" % vrf_name
                    cmds.append(cmd)
                else:
                    cmd = "ipv4-family vpn-instance %s" % vrf_name
                    cmds.append(cmd)
        else:
            if vrf_name != "_public_":
                cmd = "ipv4-family vpn-instance %s" % vrf_name
                cmds.append(cmd)

        conf_str += CE_MERGE_BGP_INSTANCE_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp instance other failed.')

        return cmds

    def delete_bgp_instance_other_comm(self, **kwargs):
        """ delete_bgp_instance_other_comm """

        module = kwargs["module"]
        conf_str = CE_DELETE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        conf_str += "<vrfName>%s</vrfName>" % vrf_name

        cmds = []

        router_id = module.params['router_id']
        if router_id:
            conf_str += "<routerId>%s</routerId>" % router_id

            cmd = "undo router-id"
            cmds.append(cmd)

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel != 'no_use':
            conf_str += "<vrfRidAutoSel>%s</vrfRidAutoSel>" % vrf_rid_auto_sel

            cmd = "undo router-id vpn-instance auto-select"
            cmds.append(cmd)

        keepalive_time = module.params['keepalive_time']
        if keepalive_time:
            conf_str += "<keepaliveTime>%s</keepaliveTime>" % keepalive_time

            cmd = "undo timer keepalive"
            cmds.append(cmd)

        hold_time = module.params['hold_time']
        if hold_time:
            conf_str += "<holdTime>%s</holdTime>" % hold_time

            cmd = "undo timer hold"
            cmds.append(cmd)

        min_hold_time = module.params['min_hold_time']
        if min_hold_time:
            conf_str += "<minHoldTime>%s</minHoldTime>" % min_hold_time

            cmd = "undo timer min-holdtime"
            cmds.append(cmd)

        conn_retry_time = module.params['conn_retry_time']
        if conn_retry_time:
            conf_str += "<connRetryTime>%s</connRetryTime>" % conn_retry_time

            cmd = "undo timer connect-retry"
            cmds.append(cmd)

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive != 'no_use':
            conf_str += "<ebgpIfSensitive>%s</ebgpIfSensitive>" % ebgp_if_sensitive

            cmd = "undo ebgp-interface-sensitive"
            cmds.append(cmd)

        default_af_type = module.params['default_af_type']
        if default_af_type:
            conf_str += "<defaultAfType>%s</defaultAfType>" % default_af_type

            if vrf_name != "_public_":
                if default_af_type == "ipv6uni":
                    cmd = "undo ipv6-family vpn-instance %s" % vrf_name
                    cmds.append(cmd)
                else:
                    cmd = "undo ipv4-family vpn-instance %s" % vrf_name
                    cmds.append(cmd)
        else:
            if vrf_name != "_public_":
                cmd = "undo ipv4-family vpn-instance %s" % vrf_name
                cmds.append(cmd)

        conf_str += CE_DELETE_BGP_INSTANCE_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Delete common vpn bgp instance other args failed.')

        return cmds

    def delete_instance_other_public(self, **kwargs):
        """ delete_instance_other_public """

        module = kwargs["module"]
        conf_str = CE_MERGE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        conf_str += "<vrfName>%s</vrfName>" % vrf_name

        cmds = []

        router_id = module.params['router_id']
        if router_id:
            conf_str += "<routerId></routerId>"

            cmd = "undo router-id"
            cmds.append(cmd)

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel != 'no_use':
            conf_str += "<vrfRidAutoSel>%s</vrfRidAutoSel>" % vrf_rid_auto_sel

            cmd = "undo router-id vpn-instance auto-select"
            cmds.append(cmd)

        keepalive_time = module.params['keepalive_time']
        if keepalive_time:
            conf_str += "<keepaliveTime>%s</keepaliveTime>" % "60"

            cmd = "undo timer keepalive"
            cmds.append(cmd)

        hold_time = module.params['hold_time']
        if hold_time:
            conf_str += "<holdTime>%s</holdTime>" % "180"

            cmd = "undo timer hold"
            cmds.append(cmd)

        min_hold_time = module.params['min_hold_time']
        if min_hold_time:
            conf_str += "<minHoldTime>%s</minHoldTime>" % "0"

            cmd = "undo timer min-holdtime"
            cmds.append(cmd)

        conn_retry_time = module.params['conn_retry_time']
        if conn_retry_time:
            conf_str += "<connRetryTime>%s</connRetryTime>" % "32"

            cmd = "undo timer connect-retry"
            cmds.append(cmd)

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive != 'no_use':
            conf_str += "<ebgpIfSensitive>%s</ebgpIfSensitive>" % "true"

            cmd = "undo ebgp-interface-sensitive"
            cmds.append(cmd)

        default_af_type = module.params['default_af_type']
        if default_af_type:
            conf_str += "<defaultAfType>%s</defaultAfType>" % "ipv4uni"

            if vrf_name != "_public_":
                if default_af_type == "ipv6uni":
                    cmd = "undo ipv6-family vpn-instance %s" % vrf_name
                    cmds.append(cmd)
                else:
                    cmd = "undo ipv4-family vpn-instance %s" % vrf_name
                    cmds.append(cmd)
        else:
            if vrf_name != "_public_":
                cmd = "undo ipv4-family vpn-instance %s" % vrf_name
                cmds.append(cmd)

        conf_str += CE_MERGE_BGP_INSTANCE_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Delete default vpn bgp instance other args failed.')

        return cmds


def main():
    """ main """

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        as_number=dict(type='str'),
        graceful_restart=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        time_wait_for_rib=dict(type='str'),
        as_path_limit=dict(type='str'),
        check_first_as=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        confed_id_number=dict(type='str'),
        confed_nonstanded=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        bgp_rid_auto_sel=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        keep_all_routes=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        memory_limit=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        gr_peer_reset=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        is_shutdown=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        suppress_interval=dict(type='str'),
        hold_interval=dict(type='str'),
        clear_interval=dict(type='str'),
        confed_peer_as_num=dict(type='str'),
        vrf_name=dict(type='str'),
        vrf_rid_auto_sel=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        router_id=dict(type='str'),
        keepalive_time=dict(type='str'),
        hold_time=dict(type='str'),
        min_hold_time=dict(type='str'),
        conn_retry_time=dict(type='str'),
        ebgp_if_sensitive=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        default_af_type=dict(type='str', choices=['ipv4uni', 'ipv6uni'])
    )

    argument_spec.update(ce_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    changed = False
    proposed = dict()
    existing = dict()
    end_state = dict()
    updates = []

    state = module.params['state']
    as_number = module.params['as_number']
    graceful_restart = module.params['graceful_restart']
    time_wait_for_rib = module.params['time_wait_for_rib']
    as_path_limit = module.params['as_path_limit']
    check_first_as = module.params['check_first_as']
    confed_id_number = module.params['confed_id_number']
    confed_nonstanded = module.params['confed_nonstanded']
    bgp_rid_auto_sel = module.params['bgp_rid_auto_sel']
    keep_all_routes = module.params['keep_all_routes']
    memory_limit = module.params['memory_limit']
    gr_peer_reset = module.params['gr_peer_reset']
    is_shutdown = module.params['is_shutdown']
    suppress_interval = module.params['suppress_interval']
    hold_interval = module.params['hold_interval']
    clear_interval = module.params['clear_interval']
    confed_peer_as_num = module.params['confed_peer_as_num']
    router_id = module.params['router_id']
    vrf_name = module.params['vrf_name']
    vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
    keepalive_time = module.params['keepalive_time']
    hold_time = module.params['hold_time']
    min_hold_time = module.params['min_hold_time']
    conn_retry_time = module.params['conn_retry_time']
    ebgp_if_sensitive = module.params['ebgp_if_sensitive']
    default_af_type = module.params['default_af_type']

    ce_bgp_obj = Bgp()

    if not ce_bgp_obj:
        module.fail_json(msg='Error: Init module failed.')

    # get proposed
    proposed["state"] = state
    if as_number:
        proposed["as_number"] = as_number
    if graceful_restart != 'no_use':
        proposed["graceful_restart"] = graceful_restart
    if time_wait_for_rib:
        proposed["time_wait_for_rib"] = time_wait_for_rib
    if as_path_limit:
        proposed["as_path_limit"] = as_path_limit
    if check_first_as != 'no_use':
        proposed["check_first_as"] = check_first_as
    if confed_id_number:
        proposed["confed_id_number"] = confed_id_number
    if confed_nonstanded != 'no_use':
        proposed["confed_nonstanded"] = confed_nonstanded
    if bgp_rid_auto_sel != 'no_use':
        proposed["bgp_rid_auto_sel"] = bgp_rid_auto_sel
    if keep_all_routes != 'no_use':
        proposed["keep_all_routes"] = keep_all_routes
    if memory_limit != 'no_use':
        proposed["memory_limit"] = memory_limit
    if gr_peer_reset != 'no_use':
        proposed["gr_peer_reset"] = gr_peer_reset
    if is_shutdown != 'no_use':
        proposed["is_shutdown"] = is_shutdown
    if suppress_interval:
        proposed["suppress_interval"] = suppress_interval
    if hold_interval:
        proposed["hold_interval"] = hold_interval
    if clear_interval:
        proposed["clear_interval"] = clear_interval
    if confed_peer_as_num:
        proposed["confed_peer_as_num"] = confed_peer_as_num
    if router_id:
        proposed["router_id"] = router_id
    if vrf_name:
        proposed["vrf_name"] = vrf_name
    if vrf_rid_auto_sel != 'no_use':
        proposed["vrf_rid_auto_sel"] = vrf_rid_auto_sel
    if keepalive_time:
        proposed["keepalive_time"] = keepalive_time
    if hold_time:
        proposed["hold_time"] = hold_time
    if min_hold_time:
        proposed["min_hold_time"] = min_hold_time
    if conn_retry_time:
        proposed["conn_retry_time"] = conn_retry_time
    if ebgp_if_sensitive != 'no_use':
        proposed["ebgp_if_sensitive"] = ebgp_if_sensitive
    if default_af_type:
        proposed["default_af_type"] = default_af_type

    need_bgp_enable = check_bgp_enable_args(module=module)
    need_bgp_enable_other_rst = ce_bgp_obj.check_bgp_enable_other_args(
        module=module)
    need_bgp_confed = check_bgp_confed_args(module=module)
    need_bgp_instance = ce_bgp_obj.check_bgp_instance_args(module=module)
    need_bgp_instance_other_rst = ce_bgp_obj.check_bgp_instance_other_args(
        module=module)

    # bgp enable/disable
    if need_bgp_enable:

        bgp_enable_exist = ce_bgp_obj.get_bgp_enable(module=module)
        existing["bgp enable"] = bgp_enable_exist

        asnumber_exist = bgp_enable_exist[0][0]
        bgpenable_exist = bgp_enable_exist[0][1]

        if state == "present":
            bgp_enable_new = (as_number, "true")

            if bgp_enable_new in bgp_enable_exist:
                pass
            elif bgpenable_exist == "true" and asnumber_exist != as_number:
                module.fail_json(
                    msg='Error: BGP is already running. The AS is %s.' % asnumber_exist)
            else:
                cmd = ce_bgp_obj.merge_bgp_enable(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)

        else:
            if need_bgp_enable_other_rst["need_cfg"] or need_bgp_confed or need_bgp_instance_other_rst["need_cfg"]:
                pass
            elif bgpenable_exist == "false":
                pass
            elif bgpenable_exist == "true" and asnumber_exist == as_number:
                cmd = ce_bgp_obj.merge_bgp_enable(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)

            else:
                module.fail_json(
                    msg='Error: BGP is already running. The AS is %s.' % asnumber_exist)

        bgp_enable_end = ce_bgp_obj.get_bgp_enable(module=module)
        end_state["bgp enable"] = bgp_enable_end

    # bgp enable/disable other args
    exist_tmp = dict()
    for item in need_bgp_enable_other_rst:
        if item != "need_cfg":
            exist_tmp[item] = need_bgp_enable_other_rst[item]

    if exist_tmp:
        existing["bgp enable other"] = exist_tmp

    if need_bgp_enable_other_rst["need_cfg"]:
        if state == "present":
            cmd = ce_bgp_obj.merge_bgp_enable_other(module=module)
            changed = True
            for item in cmd:
                updates.append(item)
        else:
            cmd = ce_bgp_obj.delete_bgp_enable_other(module=module)
            changed = True
            for item in cmd:
                updates.append(item)

    need_bgp_enable_other_rst = ce_bgp_obj.check_bgp_enable_other_args(
        module=module)

    end_tmp = dict()
    for item in need_bgp_enable_other_rst:
        if item != "need_cfg":
            end_tmp[item] = need_bgp_enable_other_rst[item]

    if end_tmp:
        end_state["bgp enable other"] = end_tmp

    # bgp confederation peer as
    if need_bgp_confed:
        confed_exist = ce_bgp_obj.get_bgp_confed_peer_as(module=module)
        existing["confederation peer as"] = confed_exist
        confed_new = (confed_peer_as_num)

        if state == "present":
            if len(confed_exist) == 0:
                cmd = ce_bgp_obj.create_bgp_confed_peer_as(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)

            elif confed_new not in confed_exist:
                cmd = ce_bgp_obj.merge_bgp_confed_peer_as(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)

        else:
            if len(confed_exist) == 0:
                pass

            elif confed_new not in confed_exist:
                pass

            else:
                cmd = ce_bgp_obj.delete_bgp_confed_peer_as(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)

        confed_end = ce_bgp_obj.get_bgp_confed_peer_as(module=module)
        end_state["confederation peer as"] = confed_end

    # bgp instance
    router_id_exist = ce_bgp_obj.get_bgp_instance(module=module)
    existing["bgp instance"] = router_id_exist
    if need_bgp_instance:
        router_id_new = (vrf_name)

        if state == "present":
            if len(router_id_exist) == 0:
                cmd = ce_bgp_obj.create_bgp_instance(module=module)
                changed = True
                updates.append(cmd)
            elif router_id_new not in router_id_exist:
                ce_bgp_obj.merge_bgp_instance(module=module)
                changed = True

        else:
            if not need_bgp_instance_other_rst["need_cfg"]:
                if vrf_name != "_public_":
                    if len(router_id_exist) == 0:
                        pass
                    elif router_id_new not in router_id_exist:
                        pass
                    else:
                        cmd = ce_bgp_obj.delete_bgp_instance(module=module)
                        changed = True
                        for item in cmd:
                            updates.append(item)

    router_id_end = ce_bgp_obj.get_bgp_instance(module=module)
    end_state["bgp instance"] = router_id_end

    # bgp instance other
    exist_tmp = dict()
    for item in need_bgp_instance_other_rst:
        if item != "need_cfg":
            exist_tmp[item] = need_bgp_instance_other_rst[item]

    if exist_tmp:
        existing["bgp instance other"] = exist_tmp

    if need_bgp_instance_other_rst["need_cfg"]:
        if state == "present":
            cmd = ce_bgp_obj.merge_bgp_instance_other(module=module)
            changed = True
            for item in cmd:
                updates.append(item)

        else:
            if vrf_name == "_public_":
                cmd = ce_bgp_obj.delete_instance_other_public(
                    module=module)
                changed = True
                for item in cmd:
                    updates.append(item)
            else:
                cmd = ce_bgp_obj.delete_bgp_instance_other_comm(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)

    need_bgp_instance_other_rst = ce_bgp_obj.check_bgp_instance_other_args(
        module=module)

    end_tmp = dict()
    for item in need_bgp_instance_other_rst:
        if item != "need_cfg":
            end_tmp[item] = need_bgp_instance_other_rst[item]

    if end_tmp:
        end_state["bgp instance other"] = end_tmp

    results = dict()
    results['proposed'] = proposed
    results['existing'] = existing
    results['changed'] = changed
    results['end_state'] = end_state
    results['updates'] = updates

    module.exit_json(**results)


if __name__ == '__main__':
    main()
