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

DOCUMENTATION = '''
---

module: ce_bgp
version_added: "2.2"
short_description: Manages BGP configuration.
description:
    - Manages BGP configurations on cloudengine switches.
extends_documentation_fragment: cloudengine
author:
    - wangdezhuang (@CloudEngine-Ansible)
notes:
    - The server_type parameter is always required.
options:
    state:
        description:
            - Manage the state of the resource.
        required: true
        default: present
        choices: ['present','absent']
    as_number:
        description:
            - local AS number.
        default: None
    graceful_restart:
        description:
            - graceful restart.
        default: None
        choices: ['true','false']
    time_wait_for_rib:
        description:
            - time wait for rib.
        default: None
    as_path_limit:
        description:
            - max number of AS.
        default: None
    check_first_as:
        description:
            - check first AS.
        default: None
        choices: ['true','false']
    confed_id_number:
        description:
            - confederation id number.
        default: None
    confed_nonstanded:
        description:
            - confederation nonstanded.
        default: None
        choices: ['true','false']
    bgp_rid_auto_sel:
        description:
            - bgp rid auto select.
        default: None
        choices: ['true','false']
    keep_all_routes:
        description:
            - keep all routes.
        default: None
        choices: ['true','false']
    memory_limit:
        description:
            - memory limit.
        default: None
        choices: ['true','false']
    gr_peer_reset:
        description:
            - gr peer reset.
        default: None
        choices: ['true','false']
    is_shutdown:
        description:
            - is shutdown.
        default: None
        choices: ['true','false']
    suppress_interval:
        description:
            - suppress interval.
        default: None
    hold_interval:
        description:
            - hold interval.
        default: None
    clear_interval:
        description:
            - clear interval.
        default: None
    confed_peer_as_num:
        description:
            - confederation peer AS num.
        default: None
    vrf_name:
        description:
            - vrf name.
        default: None
    vrf_rid_auto_sel:
        description:
            - vrf rid auto select.
        default: None
        choices: ['true','false']
    router_id:
        description:
            - router id.
        default: None
    keepalive_time:
        description:
            - keepalive time.
        default: None
    hold_time:
        description:
            - hold time.
        default: None
    min_hold_time:
        description:
            - min hold time.
        default: None
    conn_retry_time:
        description:
            - conn retry time.
        default: None
    ebgp_if_sensitive:
        description:
            - ebgp if sensitive.
        default: None
    default_af_type:
        description:
            - default af type.
        default: None
'''

EXAMPLES = '''
# enable BGP
  - name: "enable BGP"
    ce_bgp:
        state:  present
        as_number:  100
        confed_id_number:  250
        host:  {{inventory_hostname}}
        username:  {{username}}
        password:  {{password}}
# create confederation peer AS num
  - name: "create confederation peer AS num"
    ce_bgp:
        state:  present
        confed_peer_as_num:  260
        host:  {{inventory_hostname}}
        username:  {{username}}
        password:  {{password}
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
    description:
        - k/v pairs of existing aaa server
    type: dict
    sample: {"bgp_enable": [["100"], ["true"]]}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"bgp_enable": [["100"], ["true"]]}
execute_time:
    description: the module execute time
    returned: always
    type: string
    sample: "0:00:03.380753"
'''

import re
import datetime
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf

HAS_NCCLIENT = False
try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


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


class ce_bgp(object):
    """ Manages BGP configuration """

    def __init__(self, **kwargs):
        """ __init__ """

        self.netconf = get_netconf(**kwargs)

    def netconf_get_config(self, **kwargs):
        """ netconf_get_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        try:
            con_obj = self.netconf.get_config(filter=conf_str)
        except RPCError as err:
            module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def netconf_set_config(self, **kwargs):
        """ netconf_set_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        try:
            con_obj = self.netconf.set_config(config=conf_str)
        except RPCError as err:
            module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def check_ip_addr(self, **kwargs):
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

    def check_bgp_enable_args(self, **kwargs):
        """check_bgp_enable_args"""

        module = kwargs["module"]

        need_cfg = False

        as_number = module.params['as_number']
        if as_number:
            if len(as_number) > 11 or len(as_number) == 0:
                module.fail_json(
                    msg='the len of as_number %s is out of [1 - 11].' % as_number)
            else:
                need_cfg = True

        return need_cfg

    def check_bgp_enable_other_args(self, **kwargs):
        """check_bgp_enable_other_args"""

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        graceful_restart = module.params['graceful_restart']
        if graceful_restart:

            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<gracefulRestart></gracefulRestart>" + CE_GET_BGP_ENABLE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<gracefulRestart>(.*)</gracefulRestart>.*', con_obj.xml)

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
                    msg='time_wait_for_rib %s is out of [3 - 3000].' % time_wait_for_rib)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<timeWaitForRib></timeWaitForRib>" + CE_GET_BGP_ENABLE_TAIL
                con_obj = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<timeWaitForRib>(.*)</timeWaitForRib>.*', con_obj.xml)

                    if re_find:
                        result["time_wait_for_rib"] = re_find
                        if re_find[0] != time_wait_for_rib:
                            need_cfg = True
                    else:
                        need_cfg = True

        as_path_limit = module.params['as_path_limit']
        if as_path_limit:
            if int(as_path_limit) > 2000 or int(as_path_limit) < 1:
                module.fail_json(
                    msg='as_path_limit %s is out of [1 - 2000].' % as_path_limit)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<asPathLimit></asPathLimit>" + CE_GET_BGP_ENABLE_TAIL
                con_obj = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<asPathLimit>(.*)</asPathLimit>.*', con_obj.xml)

                    if re_find:
                        result["as_path_limit"] = re_find
                        if re_find[0] != as_path_limit:
                            need_cfg = True
                    else:
                        need_cfg = True

        check_first_as = module.params['check_first_as']
        if check_first_as:
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<checkFirstAs></checkFirstAs>" + CE_GET_BGP_ENABLE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<checkFirstAs>(.*)</checkFirstAs>.*', con_obj.xml)

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
                    msg='the len of confed_id_number %s is out of [1 - 11].' % confed_id_number)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<confedIdNumber></confedIdNumber>" + CE_GET_BGP_ENABLE_TAIL
                con_obj = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<confedIdNumber>(.*)</confedIdNumber>.*', con_obj.xml)

                    if re_find:
                        result["confed_id_number"] = re_find
                        if re_find[0] != confed_id_number:
                            need_cfg = True
                    else:
                        need_cfg = True

        confed_nonstanded = module.params['confed_nonstanded']
        if confed_nonstanded:
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<confedNonstanded></confedNonstanded>" + CE_GET_BGP_ENABLE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<confedNonstanded>(.*)</confedNonstanded>.*', con_obj.xml)

                if re_find:
                    result["confed_nonstanded"] = re_find
                    if re_find[0] != confed_nonstanded:
                        need_cfg = True
                else:
                    need_cfg = True

        bgp_rid_auto_sel = module.params['bgp_rid_auto_sel']
        if bgp_rid_auto_sel:
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<bgpRidAutoSel></bgpRidAutoSel>" + CE_GET_BGP_ENABLE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<bgpRidAutoSel>(.*)</bgpRidAutoSel>.*', con_obj.xml)

                if re_find:
                    result["bgp_rid_auto_sel"] = re_find
                    if re_find[0] != bgp_rid_auto_sel:
                        need_cfg = True
                else:
                    need_cfg = True

        keep_all_routes = module.params['keep_all_routes']
        if keep_all_routes:
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<keepAllRoutes></keepAllRoutes>" + CE_GET_BGP_ENABLE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<keepAllRoutes>(.*)</keepAllRoutes>.*', con_obj.xml)

                if re_find:
                    result["keep_all_routes"] = re_find
                    if re_find[0] != keep_all_routes:
                        need_cfg = True
                else:
                    need_cfg = True

        memory_limit = module.params['memory_limit']
        if memory_limit:
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<memoryLimit></memoryLimit>" + CE_GET_BGP_ENABLE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<memoryLimit>(.*)</memoryLimit>.*', con_obj.xml)

                if re_find:
                    result["memory_limit"] = re_find
                    if re_find[0] != memory_limit:
                        need_cfg = True
                else:
                    need_cfg = True

        gr_peer_reset = module.params['gr_peer_reset']
        if gr_peer_reset:
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<grPeerReset></grPeerReset>" + CE_GET_BGP_ENABLE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<grPeerReset>(.*)</grPeerReset>.*', con_obj.xml)

                if re_find:
                    result["gr_peer_reset"] = re_find
                    if re_find[0] != gr_peer_reset:
                        need_cfg = True
                else:
                    need_cfg = True

        is_shutdown = module.params['is_shutdown']
        if is_shutdown:
            conf_str = CE_GET_BGP_ENABLE_HEADER + \
                "<isShutdown></isShutdown>" + CE_GET_BGP_ENABLE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<isShutdown>(.*)</isShutdown>.*', con_obj.xml)

                if re_find:
                    result["is_shutdown"] = re_find
                    if re_find[0] != is_shutdown:
                        need_cfg = True
                else:
                    need_cfg = True

        suppress_interval = module.params['suppress_interval']
        if suppress_interval:
            if int(suppress_interval) > 65535 or int(suppress_interval) < 1:
                module.fail_json(
                    msg='suppress_interval %s is out of [1 - 65535].' % suppress_interval)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<suppressInterval></suppressInterval>" + CE_GET_BGP_ENABLE_TAIL
                con_obj = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<suppressInterval>(.*)</suppressInterval>.*', con_obj.xml)

                    if re_find:
                        result["suppress_interval"] = re_find
                        if re_find[0] != suppress_interval:
                            need_cfg = True
                    else:
                        need_cfg = True

        hold_interval = module.params['hold_interval']
        if hold_interval:
            if int(hold_interval) > 65535 or int(hold_interval) < 1:
                module.fail_json(
                    msg='hold_interval %s is out of [1 - 65535].' % hold_interval)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<holdInterval></holdInterval>" + CE_GET_BGP_ENABLE_TAIL
                con_obj = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<holdInterval>(.*)</holdInterval>.*', con_obj.xml)

                    if re_find:
                        result["hold_interval"] = re_find
                        if re_find[0] != hold_interval:
                            need_cfg = True
                    else:
                        need_cfg = True

        clear_interval = module.params['clear_interval']
        if clear_interval:
            if int(clear_interval) > 65535 or int(clear_interval) < 1:
                module.fail_json(
                    msg='clear_interval %s is out of [1 - 65535].' % clear_interval)
            else:
                conf_str = CE_GET_BGP_ENABLE_HEADER + \
                    "<clearInterval></clearInterval>" + CE_GET_BGP_ENABLE_TAIL
                con_obj = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<clearInterval>(.*)</clearInterval>.*', con_obj.xml)

                    if re_find:
                        result["clear_interval"] = re_find
                        if re_find[0] != clear_interval:
                            need_cfg = True
                    else:
                        need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_bgp_confed_args(self, **kwargs):
        """check_bgp_confed_args"""

        module = kwargs["module"]

        need_cfg = False

        confed_peer_as_num = module.params['confed_peer_as_num']
        if confed_peer_as_num:
            if len(confed_peer_as_num) > 11 or len(confed_peer_as_num) == 0:
                module.fail_json(
                    msg='the len of confed_peer_as_num %s is out of [1 - 11].' % confed_peer_as_num)
            else:
                need_cfg = True

        return need_cfg

    def check_bgp_instance_args(self, **kwargs):
        """check_bgp_instance_args"""

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
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<vrfName>(.*)</vrfName>.*', con_obj.xml)

                    if re_find:
                        if (vrf_name) not in re_find:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in con_obj.xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<vrfName>(.*)</vrfName>.*', con_obj.xml)

                    if re_find:
                        if (vrf_name) in re_find:
                            need_cfg = True
                    else:
                        pass

        return need_cfg

    def check_bgp_instance_other_args(self, **kwargs):
        """check_bgp_instance_other_args"""

        module = kwargs["module"]
        state = module.params['state']
        result = dict()
        need_cfg = False

        router_id = module.params['router_id']
        if router_id:
            if self.check_ip_addr(ipaddr=router_id) == FAILED:
                module.fail_json(
                    msg='the router_id %s is invalid.' % router_id)

            conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                "<routerId></routerId>" + CE_GET_BGP_INSTANCE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<routerId>(.*)</routerId>.*', con_obj.xml)

                    if re_find:
                        result["router_id"] = re_find
                        if re_find[0] != router_id:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in con_obj.xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<routerId>(.*)</routerId>.*', con_obj.xml)

                    if re_find:
                        result["router_id"] = re_find
                        if re_find[0] == router_id:
                            need_cfg = True
                    else:
                        pass

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel:
            conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                "<vrfRidAutoSel></vrfRidAutoSel>" + CE_GET_BGP_INSTANCE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<vrfRidAutoSel>(.*)</vrfRidAutoSel>.*', con_obj.xml)

                    if re_find:
                        result["vrf_rid_auto_sel"] = re_find

                        if re_find[0] != vrf_rid_auto_sel:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                pass

        keepalive_time = module.params['keepalive_time']
        if keepalive_time:
            if int(keepalive_time) > 21845 or int(keepalive_time) < 0:
                module.fail_json(
                    msg='keepalive_time %s is out of [0 - 21845].' % keepalive_time)
            else:
                conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                    "<keepaliveTime></keepaliveTime>" + CE_GET_BGP_INSTANCE_TAIL
                con_obj = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in con_obj.xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<keepaliveTime>(.*)</keepaliveTime>.*', con_obj.xml)

                        if re_find:
                            result["keepalive_time"] = re_find
                            if re_find[0] != keepalive_time:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in con_obj.xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<keepaliveTime>(.*)</keepaliveTime>.*', con_obj.xml)

                        if re_find:
                            result["keepalive_time"] = re_find
                            if re_find[0] == keepalive_time:
                                need_cfg = True
                        else:
                            pass

        hold_time = module.params['hold_time']
        if hold_time:
            if int(hold_time) > 65535 or int(hold_time) < 3:
                module.fail_json(
                    msg='hold_time %s is out of [3 - 65535].' % hold_time)
            else:
                conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                    "<holdTime></holdTime>" + CE_GET_BGP_INSTANCE_TAIL
                con_obj = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in con_obj.xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<holdTime>(.*)</holdTime>.*', con_obj.xml)

                        if re_find:
                            result["hold_time"] = re_find
                            if re_find[0] != hold_time:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in con_obj.xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<holdTime>(.*)</holdTime>.*', con_obj.xml)

                        if re_find:
                            result["hold_time"] = re_find
                            if re_find[0] == hold_time:
                                need_cfg = True
                        else:
                            pass

        min_hold_time = module.params['min_hold_time']
        if min_hold_time:
            if int(min_hold_time) != 0 and (int(min_hold_time) > 65535 or int(min_hold_time) < 20):
                module.fail_json(
                    msg='min_hold_time %s is out of [0, or 20 - 65535].' % min_hold_time)
            else:
                conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                    "<minHoldTime></minHoldTime>" + CE_GET_BGP_INSTANCE_TAIL
                con_obj = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in con_obj.xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<minHoldTime>(.*)</minHoldTime>.*', con_obj.xml)

                        if re_find:
                            result["min_hold_time"] = re_find
                            if re_find[0] != min_hold_time:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in con_obj.xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<minHoldTime>(.*)</minHoldTime>.*', con_obj.xml)

                        if re_find:
                            result["min_hold_time"] = re_find
                            if re_find[0] == min_hold_time:
                                need_cfg = True
                        else:
                            pass

        conn_retry_time = module.params['conn_retry_time']
        if conn_retry_time:
            if int(conn_retry_time) > 65535 or int(conn_retry_time) < 1:
                module.fail_json(
                    msg='conn_retry_time %s is out of [1 - 65535].' % conn_retry_time)
            else:
                conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                    "<connRetryTime></connRetryTime>" + CE_GET_BGP_INSTANCE_TAIL
                con_obj = self.netconf_get_config(
                    module=module, conf_str=conf_str)

                if state == "present":
                    if "<data/>" in con_obj.xml:
                        need_cfg = True
                    else:
                        re_find = re.findall(
                            r'.*<connRetryTime>(.*)</connRetryTime>.*', con_obj.xml)

                        if re_find:
                            result["conn_retry_time"] = re_find
                            if re_find[0] != conn_retry_time:
                                need_cfg = True
                        else:
                            need_cfg = True
                else:
                    if "<data/>" in con_obj.xml:
                        pass
                    else:
                        re_find = re.findall(
                            r'.*<connRetryTime>(.*)</connRetryTime>.*', con_obj.xml)

                        if re_find:
                            result["conn_retry_time"] = re_find
                            if re_find[0] == conn_retry_time:
                                need_cfg = True
                        else:
                            pass

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive:
            conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                "<ebgpIfSensitive></ebgpIfSensitive>" + CE_GET_BGP_INSTANCE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<ebgpIfSensitive>(.*)</ebgpIfSensitive>.*', con_obj.xml)

                    if re_find:
                        result["ebgp_if_sensitive"] = re_find
                        if re_find[0] != ebgp_if_sensitive:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in con_obj.xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<ebgpIfSensitive>(.*)</ebgpIfSensitive>.*', con_obj.xml)

                    if re_find:
                        result["ebgp_if_sensitive"] = re_find
                        if re_find[0] == ebgp_if_sensitive:
                            need_cfg = True
                    else:
                        pass

        default_af_type = module.params['default_af_type']
        if default_af_type:
            conf_str = CE_GET_BGP_INSTANCE_HEADER + \
                "<defaultAfType></defaultAfType>" + CE_GET_BGP_INSTANCE_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<defaultAfType>(.*)</defaultAfType>.*', con_obj.xml)

                    if re_find:
                        result["default_af_type"] = re_find
                        if re_find[0] != default_af_type:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in con_obj.xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<defaultAfType>(.*)</defaultAfType>.*', con_obj.xml)

                    if re_find:
                        result["default_af_type"] = re_find
                        if re_find[0] == default_af_type:
                            need_cfg = True
                    else:
                        pass

        result["need_cfg"] = need_cfg
        return result

    def get_bgp_enable(self, **kwargs):
        """get_bgp_enable"""

        module = kwargs["module"]

        conf_str = CE_GET_BGP_ENABLE

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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
        """merge_bgp_enable"""

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

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp enable failed.')

        return SUCCESS

    def merge_bgp_enable_other(self, **kwargs):
        """merge_bgp_enable_other"""

        module = kwargs["module"]
        conf_str = CE_MERGE_BGP_ENABLE_HEADER

        graceful_restart = module.params['graceful_restart']
        if graceful_restart:
            conf_str += "<gracefulRestart>%s</gracefulRestart>" % graceful_restart

        time_wait_for_rib = module.params['time_wait_for_rib']
        if time_wait_for_rib:
            conf_str += "<timeWaitForRib>%s</timeWaitForRib>" % time_wait_for_rib

        as_path_limit = module.params['as_path_limit']
        if as_path_limit:
            conf_str += "<asPathLimit>%s</asPathLimit>" % as_path_limit

        check_first_as = module.params['check_first_as']
        if check_first_as:
            conf_str += "<checkFirstAs>%s</checkFirstAs>" % check_first_as

        confed_id_number = module.params['confed_id_number']
        if confed_id_number:
            conf_str += "<confedIdNumber>%s</confedIdNumber>" % confed_id_number

        confed_nonstanded = module.params['confed_nonstanded']
        if confed_nonstanded:
            conf_str += "<confedNonstanded>%s</confedNonstanded>" % confed_nonstanded

        bgp_rid_auto_sel = module.params['bgp_rid_auto_sel']
        if bgp_rid_auto_sel:
            conf_str += "<bgpRidAutoSel>%s</bgpRidAutoSel>" % bgp_rid_auto_sel

        keep_all_routes = module.params['keep_all_routes']
        if keep_all_routes:
            conf_str += "<keepAllRoutes>%s</keepAllRoutes>" % keep_all_routes

        memory_limit = module.params['memory_limit']
        if memory_limit:
            conf_str += "<memoryLimit>%s</memoryLimit>" % memory_limit

        gr_peer_reset = module.params['gr_peer_reset']
        if gr_peer_reset:
            conf_str += "<grPeerReset>%s</grPeerReset>" % gr_peer_reset

        is_shutdown = module.params['is_shutdown']
        if is_shutdown:
            conf_str += "<isShutdown>%s</isShutdown>" % is_shutdown

        suppress_interval = module.params['suppress_interval']
        if suppress_interval:
            conf_str += "<suppressInterval>%s</suppressInterval>" % suppress_interval

        hold_interval = module.params['hold_interval']
        if hold_interval:
            conf_str += "<holdInterval>%s</holdInterval>" % hold_interval

        clear_interval = module.params['clear_interval']
        if clear_interval:
            conf_str += "<clearInterval>%s</clearInterval>" % clear_interval

        conf_str += CE_MERGE_BGP_ENABLE_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp enable failed.')

        return SUCCESS

    def get_bgp_confed_peer_as(self, **kwargs):
        """get_bgp_confed_peer_as"""

        module = kwargs["module"]

        conf_str = CE_GET_BGP_CONFED_PEER_AS

        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp confed peer as failed.')

        return SUCCESS

    def create_bgp_confed_peer_as(self, **kwargs):
        """ create_bgp_confed_peer_as """

        module = kwargs["module"]
        confed_peer_as_num = module.params['confed_peer_as_num']

        conf_str = CE_CREATE_BGP_CONFED_PEER_AS % confed_peer_as_num

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create bgp confed peer as failed.')

        return SUCCESS

    def delete_bgp_confed_peer_as(self, **kwargs):
        """ delete_bgp_confed_peer_as """

        module = kwargs["module"]
        confed_peer_as_num = module.params['confed_peer_as_num']

        conf_str = CE_DELETE_BGP_CONFED_PEER_AS % confed_peer_as_num

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete bgp confed peer as failed.')

        return SUCCESS

    def get_bgp_instance(self, **kwargs):
        """get_bgp_instance"""

        module = kwargs["module"]
        conf_str = CE_GET_BGP_INSTANCE
        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        xml_str = con_obj.xml
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
        """merge_bgp_instance"""

        module = kwargs["module"]
        conf_str = CE_MERGE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        conf_str += "<vrfName>%s</vrfName>" % vrf_name

        conf_str += CE_MERGE_BGP_INSTANCE_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp instance failed.')

        return SUCCESS

    def create_bgp_instance(self, **kwargs):
        """create_bgp_instance"""

        module = kwargs["module"]
        conf_str = CE_CREATE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        conf_str += CE_CREATE_BGP_INSTANCE_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create bgp instance failed.')

        return SUCCESS

    def delete_bgp_instance(self, **kwargs):
        """delete_bgp_instance"""

        module = kwargs["module"]
        conf_str = CE_DELETE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        conf_str += CE_DELETE_BGP_INSTANCE_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete bgp instance failed.')

        return SUCCESS

    def merge_bgp_instance_other(self, **kwargs):
        """merge_bgp_instance_other"""

        module = kwargs["module"]
        conf_str = CE_MERGE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        conf_str += "<vrfName>%s</vrfName>" % vrf_name

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel:
            conf_str += "<vrfRidAutoSel>%s</vrfRidAutoSel>" % vrf_rid_auto_sel

        router_id = module.params['router_id']
        if router_id:
            conf_str += "<routerId>%s</routerId>" % router_id

        keepalive_time = module.params['keepalive_time']
        if keepalive_time:
            conf_str += "<keepaliveTime>%s</keepaliveTime>" % keepalive_time

        hold_time = module.params['hold_time']
        if hold_time:
            conf_str += "<holdTime>%s</holdTime>" % hold_time

        min_hold_time = module.params['min_hold_time']
        if min_hold_time:
            conf_str += "<minHoldTime>%s</minHoldTime>" % min_hold_time

        conn_retry_time = module.params['conn_retry_time']
        if conn_retry_time:
            conf_str += "<connRetryTime>%s</connRetryTime>" % conn_retry_time

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive:
            conf_str += "<ebgpIfSensitive>%s</ebgpIfSensitive>" % ebgp_if_sensitive

        default_af_type = module.params['default_af_type']
        if default_af_type:
            conf_str += "<defaultAfType>%s</defaultAfType>" % default_af_type

        conf_str += CE_MERGE_BGP_INSTANCE_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp instance other failed.')

        return SUCCESS

    def delete_bgp_instance_other_comm(self, **kwargs):
        """delete_bgp_instance_other_comm"""

        module = kwargs["module"]
        conf_str = CE_DELETE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        conf_str += "<vrfName>%s</vrfName>" % vrf_name

        router_id = module.params['router_id']
        if router_id:
            conf_str += "<routerId>%s</routerId>" % router_id

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel:
            conf_str += "<vrfRidAutoSel>%s</vrfRidAutoSel>" % vrf_rid_auto_sel

        keepalive_time = module.params['keepalive_time']
        if keepalive_time:
            conf_str += "<keepaliveTime>%s</keepaliveTime>" % keepalive_time

        hold_time = module.params['hold_time']
        if hold_time:
            conf_str += "<holdTime>%s</holdTime>" % hold_time

        min_hold_time = module.params['min_hold_time']
        if min_hold_time:
            conf_str += "<minHoldTime>%s</minHoldTime>" % min_hold_time

        conn_retry_time = module.params['conn_retry_time']
        if conn_retry_time:
            conf_str += "<connRetryTime>%s</connRetryTime>" % conn_retry_time

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive:
            conf_str += "<ebgpIfSensitive>%s</ebgpIfSensitive>" % ebgp_if_sensitive

        default_af_type = module.params['default_af_type']
        if default_af_type:
            conf_str += "<defaultAfType>%s</defaultAfType>" % default_af_type

        conf_str += CE_DELETE_BGP_INSTANCE_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(
                msg='delete common vpn bgp instance other args failed.')

        return SUCCESS

    def delete_bgp_instance_other_public(self, **kwargs):
        """delete_bgp_instance_other_public"""

        module = kwargs["module"]
        conf_str = CE_MERGE_BGP_INSTANCE_HEADER

        vrf_name = module.params['vrf_name']
        conf_str += "<vrfName>%s</vrfName>" % vrf_name

        router_id = module.params['router_id']
        if router_id:
            conf_str += "<routerId></routerId>"

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel:
            conf_str += "<vrfRidAutoSel>%s</vrfRidAutoSel>" % vrf_rid_auto_sel

        keepalive_time = module.params['keepalive_time']
        if keepalive_time:
            conf_str += "<keepaliveTime>%s</keepaliveTime>" % "60"

        hold_time = module.params['hold_time']
        if hold_time:
            conf_str += "<holdTime>%s</holdTime>" % "180"

        min_hold_time = module.params['min_hold_time']
        if min_hold_time:
            conf_str += "<minHoldTime>%s</minHoldTime>" % "0"

        conn_retry_time = module.params['conn_retry_time']
        if conn_retry_time:
            conf_str += "<connRetryTime>%s</connRetryTime>" % "32"

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive:
            conf_str += "<ebgpIfSensitive>%s</ebgpIfSensitive>" % "true"

        default_af_type = module.params['default_af_type']
        if default_af_type:
            conf_str += "<defaultAfType>%s</defaultAfType>" % "ipv4uni"

        conf_str += CE_MERGE_BGP_INSTANCE_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(
                msg='delete default vpn bgp instance other args failed.')

        return SUCCESS


def main():
    """ main """

    start_time = datetime.datetime.now()

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        host=dict(required=True),
        username=dict(required=True),
        password=dict(required=True),
        as_number=dict(type='str'),
        graceful_restart=dict(type='str', choices=['true', 'false']),
        time_wait_for_rib=dict(type='str'),
        as_path_limit=dict(type='str'),
        check_first_as=dict(type='str', choices=['true', 'false']),
        confed_id_number=dict(type='str'),
        confed_nonstanded=dict(type='str', choices=['true', 'false']),
        bgp_rid_auto_sel=dict(type='str', choices=['true', 'false']),
        keep_all_routes=dict(type='str', choices=['true', 'false']),
        memory_limit=dict(type='str', choices=['true', 'false']),
        gr_peer_reset=dict(type='str', choices=['true', 'false']),
        is_shutdown=dict(type='str', choices=['true', 'false']),
        suppress_interval=dict(type='str'),
        hold_interval=dict(type='str'),
        clear_interval=dict(type='str'),
        confed_peer_as_num=dict(type='str'),
        vrf_name=dict(type='str', default='_public_'),
        vrf_rid_auto_sel=dict(type='str', choices=['true', 'false']),
        router_id=dict(type='str'),
        keepalive_time=dict(type='str'),
        hold_time=dict(type='str'),
        min_hold_time=dict(type='str'),
        conn_retry_time=dict(type='str'),
        ebgp_if_sensitive=dict(type='str', choices=['true', 'false']),
        default_af_type=dict(type='str', choices=['ipv4uni', 'ipv6uni'])
    )

    if not HAS_NCCLIENT:
        raise Exception("the ncclient library is required")

    module = NetworkModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    state = module.params['state']
    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
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

    ce_bgp_obj = ce_bgp(host=host, port=port,
                        username=username, password=password)

    if not ce_bgp_obj:
        module.fail_json(msg='init module failed.')

    need_bgp_enable = ce_bgp_obj.check_bgp_enable_args(module=module)
    need_bgp_enable_other_rst = ce_bgp_obj.check_bgp_enable_other_args(
        module=module)
    need_bgp_confed = ce_bgp_obj.check_bgp_confed_args(module=module)
    need_bgp_instance = ce_bgp_obj.check_bgp_instance_args(module=module)
    need_bgp_instance_other_rst = ce_bgp_obj.check_bgp_instance_other_args(
        module=module)

    args = dict(state=state,
                as_number=as_number,
                graceful_restart=graceful_restart,
                time_wait_for_rib=time_wait_for_rib,
                as_path_limit=as_path_limit,
                check_first_as=check_first_as,
                confed_id_number=confed_id_number,
                confed_nonstanded=confed_nonstanded,
                bgp_rid_auto_sel=bgp_rid_auto_sel,
                keep_all_routes=keep_all_routes,
                memory_limit=memory_limit,
                gr_peer_reset=gr_peer_reset,
                is_shutdown=is_shutdown,
                suppress_interval=suppress_interval,
                hold_interval=hold_interval,
                clear_interval=clear_interval,
                confed_peer_as_num=confed_peer_as_num,
                router_id=router_id,
                vrf_name=vrf_name,
                vrf_rid_auto_sel=vrf_rid_auto_sel,
                keepalive_time=keepalive_time,
                hold_time=hold_time,
                min_hold_time=min_hold_time,
                conn_retry_time=conn_retry_time,
                ebgp_if_sensitive=ebgp_if_sensitive,
                default_af_type=default_af_type)

    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    existing = dict()
    end_state = dict()

    if state == "absent" and vrf_name == "_public_":
        if not confed_peer_as_num and not router_id and not keepalive_time and not hold_time and not min_hold_time and not conn_retry_time and not ebgp_if_sensitive and not default_af_type:
            module.fail_json(
                msg='there is no config to abdent.')

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
                    msg='BGP is already running. The AS is %s.' % asnumber_exist)
            else:
                ce_bgp_obj.merge_bgp_enable(module=module)
                changed = True

        else:
            if bgpenable_exist == "false":
                pass
            elif bgpenable_exist == "true" and asnumber_exist == as_number:
                ce_bgp_obj.merge_bgp_enable(module=module)
                changed = True

            else:
                module.fail_json(
                    msg='BGP is already running. The AS is %s.' % asnumber_exist)

        bgp_enable_end = ce_bgp_obj.get_bgp_enable(module=module)
        end_state["bgp enable"] = bgp_enable_end

    # bgp enable/disable other args
    exist_tmp = dict(
        (k, v) for k, v in need_bgp_enable_other_rst.iteritems() if k is not "need_cfg")
    if exist_tmp:
        existing["bgp enable other"] = exist_tmp

    if need_bgp_enable_other_rst["need_cfg"]:
        if state == "present":
            ce_bgp_obj.merge_bgp_enable_other(module=module)
            changed = True
        else:
            pass

    need_bgp_enable_other_rst = ce_bgp_obj.check_bgp_enable_other_args(
        module=module)
    end_tmp = dict(
        (k, v) for k, v in need_bgp_enable_other_rst.iteritems() if k is not "need_cfg")
    if end_tmp:
        end_state["bgp enable other"] = end_tmp

    # bgp confederation peer as
    if need_bgp_confed:
        confed_exist = ce_bgp_obj.get_bgp_confed_peer_as(module=module)
        existing["confederation peer as"] = confed_exist
        confed_new = (confed_peer_as_num)

        if state == "present":
            if len(confed_exist) == 0:
                ce_bgp_obj.create_bgp_confed_peer_as(module=module)
                changed = True

            elif confed_new not in confed_exist:
                ce_bgp_obj.merge_bgp_confed_peer_as(module=module)
                changed = True

            else:
                pass

        else:
            if len(confed_exist) == 0:
                pass

            elif confed_new not in confed_exist:
                pass

            else:
                ce_bgp_obj.delete_bgp_confed_peer_as(module=module)
                changed = True

        confed_end = ce_bgp_obj.get_bgp_confed_peer_as(module=module)
        end_state["confederation peer as"] = confed_end

    # bgp instance
    router_id_exist = ce_bgp_obj.get_bgp_instance(module=module)
    existing["bgp instance"] = router_id_exist
    if need_bgp_instance:
        router_id_new = (vrf_name)

        if state == "present":
            if len(router_id_exist) == 0:
                ce_bgp_obj.create_bgp_instance(module=module)
                changed = True
            elif router_id_new not in router_id_exist:
                ce_bgp_obj.merge_bgp_instance(module=module)
                changed = True
            else:
                pass

        else:
            if not need_bgp_instance_other_rst["need_cfg"]:
                if vrf_name != "_public_":
                    if len(router_id_exist) == 0:
                        pass
                    elif router_id_new not in router_id_exist:
                        pass
                    else:
                        ce_bgp_obj.delete_bgp_instance(module=module)
                        changed = True

    router_id_end = ce_bgp_obj.get_bgp_instance(module=module)
    end_state["bgp instance"] = router_id_end

    # bgp instance other
    exist_tmp = dict(
        (k, v) for k, v in need_bgp_instance_other_rst.iteritems() if k is not "need_cfg")
    if exist_tmp:
        existing["bgp instance other"] = exist_tmp

    if need_bgp_instance_other_rst["need_cfg"]:
        if state == "present":
            ce_bgp_obj.merge_bgp_instance_other(module=module)
            changed = True

        else:
            if vrf_name == "_public_":
                ce_bgp_obj.delete_bgp_instance_other_public(module=module)
                changed = True
            else:
                ce_bgp_obj.delete_bgp_instance_other_comm(module=module)
                changed = True

    need_bgp_instance_other_rst = ce_bgp_obj.check_bgp_instance_other_args(
        module=module)
    end_tmp = dict(
        (k, v) for k, v in need_bgp_instance_other_rst.iteritems() if k is not "need_cfg")
    if end_tmp:
        end_state["bgp instance other"] = end_tmp

    results = dict()
    results['proposed'] = proposed
    results['existing'] = existing
    results['changed'] = changed
    results['end_state'] = end_state

    end_time = datetime.datetime.now()
    results['execute_time'] = str(end_time - start_time)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
