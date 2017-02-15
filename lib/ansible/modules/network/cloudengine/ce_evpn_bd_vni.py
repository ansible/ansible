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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: ce_evpn_bd_vni
version_added: "2.3"
short_description: Manages Huawei EVPN VXLAN Network Identifier (VNI).
extends_documentation_fragment: cloudengine
description:
    - Manages Huawei Ethernet Virtual Private Network (EVPN) VXLAN Network
      Identifier (VNI) configurations.
author: Zhijin Zhou (@CloudEngine-Ansible)
notes:
    - Ensure that EVPN has been configured to serve as the VXLAN control plane when state is present.
    - Ensure that a bridge domain (BD) has existed when state is present.
    - Ensure that a VNI has been created and associated with a broadcast domain (BD) when state is present.
    - If you configure evpn:false to delete an EVPN instance, all configurations in the EVPN instance are deleted.
    - After an EVPN instance has been created in the BD view, you can configure an RD using route_distinguisher
      parameter in BD-EVPN instance view.
    - Before configuring VPN targets for a BD EVPN instance, ensure that an RD has been configured
      for the BD EVPN instance
    - If you unconfigure route_distinguisher, all VPN target attributes for the BD EVPN instance will be removed at the same time.
    - When using state:absent, evpn is not supported and it will be ignored.
    - When using state:absent to delete VPN target attributes, ensure the configuration of VPN target attributes has
      existed and otherwise it will report an error.
options:
    bridge_domain_id:
        description:
            - specify an existed bridge domain (BD).The value is an integer ranging from 1 to 16777215.
        required: true
    evpn:
        description:
            - create or delete an EVPN instance for a VXLAN in BD view
        required: false
        choices: ['true','false']
        default: 'true'
    route_distinguisher:
        description:
            - Configures a route distinguisher (RD) for a BD EVPN instance.
              The format of an RD can be as follows
               1) 2-byte AS number:4-byte user-defined number, for example, 1:3. An AS number is an integer ranging from
               0 to 65535, and a user-defined number is an integer ranging from 0 to 4294967295. The AS and user-defined
               numbers cannot be both 0s. This means that an RD cannot be 0:0.
               2) Integral 4-byte AS number:2-byte user-defined number, for example, 65537:3. An AS number is an integer
               ranging from 65536 to 4294967295, and a user-defined number is an integer ranging from 0 to 65535.
               3) 4-byte AS number in dotted notation:2-byte user-defined number, for example, 0.0:3 or 0.1:0. A 4-byte
               AS number in dotted notation is in the format of x.y, where x and y are integers ranging from 0 to 65535.
               4) A user-defined number is an integer ranging from 0 to 65535. The AS and user-defined numbers cannot be
               both 0s. This means that an RD cannot be 0.0:0.
               5) 32-bit IP address:2-byte user-defined number. For example, 192.168.122.15:1. An IP address ranges from
               0.0.0.0 to 255.255.255.255, and a user-defined number is an integer ranging from 0 to 65535.
               6) 'auto' specifies the RD that is automatically generated.
        required: false
        default: null
    vpn_target_both:
        description:
            - add VPN targets to both the import and export VPN target lists of a BD EVPN instance
            - the format is the same as route_distinguisher
        required: false
        default: null
    vpn_target_import:
        description:
            - add VPN targets to the import VPN target list of a BD EVPN instance
            - the format is the same as route_distinguisher
        required: true
    vpn_target_export:
        description:
            - add VPN targets to the export VPN target list of a BD EVPN instance
            - the format is the same as route_distinguisher
        required: false
        default: null
    state:
        description:
            - manage the state of the resource
        required: false
        choices: ['present','absent']
        default: 'present'
'''

EXAMPLES = '''
# Configure an EVPN instance for a VXLAN in BD view
- ce_evpn_bd_vni:
    evpn: true
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
# Configure a route distinguisher (RD) for a BD EVPN instance
- ce_evpn_bd_vni:
    route_distinguisher: 22:22
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
# Configure VPN targets to both the import and export VPN target lists of a BD EVPN instance
- ce_evpn_bd_vni:
    vpn_target_both: 22:100,22:101
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
# Configure VPN targets to the import VPN target list of a BD EVPN instance
- ce_evpn_bd_vni:
    vpn_target_import: 22:22,22:23
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
# Configure VPN targets to the export VPN target list of a BD EVPN instance
- ce_evpn_bd_vni:
    vpn_target_export: 22:38,22:39
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
# Unconfigure VPN targets to both the import and export VPN target lists of a BD EVPN instance
- ce_evpn_bd_vni:
    vpn_target_both: 22:100
    state: absent
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
# Unconfigure VPN targets to the import VPN target list of a BD EVPN instance
- ce_evpn_bd_vni:
    vpn_target_import: 22:22
    state: absent
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
# Unconfigure VPN targets to the export VPN target list of a BD EVPN instance
- ce_evpn_bd_vni:
    vpn_target_export: 22:38
    state: absent
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
# Unconfigure a route distinguisher (RD) of a BD EVPN instance
- ce_evpn_bd_vni:
    route_distinguisher: 22:22
    state: absent
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
# Unconfigure an EVPN instance for a VXLAN in BD view
- ce_evpn_bd_vni:
    evpn: false
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
                "bridge_domain_id": "2",
                "evpn": "true",
                "route_distinguisher": "22:22",
                "state": "present",
                "vpn_target_both": [
                    "22:100",
                    "22:101"
                ],
                "vpn_target_export": [
                    "22:38",
                    "22:39"
                ],
                "vpn_target_import": [
                    "22:22",
                    "22:23"
                ]
            }
existing:
    description: k/v pairs of existing attributes on the device
    type: dict
    sample: {
                "bridge_domain_id": "2",
                "evpn": "false",
                "route_distinguisher": null,
                "vpn_target_both": [],
                "vpn_target_export": [],
                "vpn_target_import": []
            }
end_state:
    description: k/v pairs of end attributes on the device
    returned: always
    type: dict or null
    sample: {
                "bridge_domain_id": "2",
                "evpn": "true",
                "route_distinguisher": "22:22",
                "vpn_target_both": [
                    "22:100",
                    "22:101"
                ],
                "vpn_target_export": [
                    "22:38",
                    "22:39"
                ],
                "vpn_target_import": [
                    "22:22",
                    "22:23"
                ]
            }
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: [
                "bridge-domain 2",
                "  evpn",
                "    route-distinguisher 22:22",
                "    vpn-target 22:38 export-extcommunity",
                "    vpn-target 22:39 export-extcommunity",
                "    vpn-target 22:100 export-extcommunity",
                "    vpn-target 22:101 export-extcommunity",
                "    vpn-target 22:22 import-extcommunity",
                "    vpn-target 22:23 import-extcommunity",
                "    vpn-target 22:100 import-extcommunity",
                "    vpn-target 22:101 import-extcommunity"
            ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import sys
import copy
from xml.etree import ElementTree
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf

try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False

CE_NC_GET_VNI_BD = """
<filter type="subtree">
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Vni2Bds>
      <nvo3Vni2Bd>
        <vniId></vniId>
        <bdId>%s</bdId>
      </nvo3Vni2Bd>
    </nvo3Vni2Bds>
  </nvo3>
</filter>
"""

CE_NC_GET_EVPN_CONFIG = """
<filter type="subtree">
  <evpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <evpnInstances>
      <evpnInstance>
        <evpnName>%s</evpnName>
        <bdId>%s</bdId>
        <evpnAutoRD></evpnAutoRD>
        <evpnRD></evpnRD>
        <evpnRTs>
          <evpnRT>
            <vrfRTType></vrfRTType>
            <vrfRTValue></vrfRTValue>
          </evpnRT>
        </evpnRTs>
        <evpnAutoRTs>
          <evpnAutoRT>
            <vrfRTType></vrfRTType>
          </evpnAutoRT>
        </evpnAutoRTs>
      </evpnInstance>
    </evpnInstances>
  </evpn>
</filter>
"""

CE_NC_DELETE_EVPN_CONFIG = """
<config>
  <evpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <evpnInstances>
      <evpnInstance operation="delete">
        <evpnName>%s</evpnName>
        <bdId>%s</bdId>
      </evpnInstance>
    </evpnInstances>
  </evpn>
</config>
"""

CE_NC_DELETE_EVPN_CONFIG_HEAD = """
<config>
  <evpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <evpnInstances>
      <evpnInstance operation="delete">
        <evpnName>%s</evpnName>
        <bdId>%s</bdId>
"""

CE_NC_MERGE_EVPN_CONFIG_HEAD = """
<config>
  <evpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <evpnInstances>
      <evpnInstance operation="merge">
        <evpnName>%s</evpnName>
        <bdId>%s</bdId>
"""

CE_NC_MERGE_EVPN_AUTORTS_HEAD = """
<evpnAutoRTs>
"""

CE_NC_MERGE_EVPN_AUTORTS_TAIL = """
</evpnAutoRTs>
"""

CE_NC_DELETE_EVPN_AUTORTS_CONTEXT = """
  <evpnAutoRT operation="delete">
    <vrfRTType>%s</vrfRTType>
  </evpnAutoRT>
"""

CE_NC_MERGE_EVPN_AUTORTS_CONTEXT = """
<evpnAutoRT>
  <vrfRTType>%s</vrfRTType>
</evpnAutoRT>
"""

CE_NC_MERGE_EVPN_RTS_HEAD = """
<evpnRTs>
"""

CE_NC_MERGE_EVPN_RTS_TAIL = """
</evpnRTs>
"""

CE_NC_DELETE_EVPN_RTS_CONTEXT = """
  <evpnRT operation="delete">
    <vrfRTType>%s</vrfRTType>
    <vrfRTValue>%s</vrfRTValue>
  </evpnRT>
"""

CE_NC_MERGE_EVPN_RTS_CONTEXT = """
<evpnRT>
  <vrfRTType>%s</vrfRTType>
  <vrfRTValue>%s</vrfRTValue>
</evpnRT>
"""

CE_NC_MERGE_EVPN_CONFIG_TAIL = """
      </evpnInstance>
    </evpnInstances>
  </evpn>
</config>
"""


def is_valid_value(vrf_targe_value):
    """check whether VPN target value is valid"""

    each_num = None
    if len(vrf_targe_value) > 21 or len(vrf_targe_value) < 3:
        return False
    if vrf_targe_value.find(':') == -1:
        return False
    elif vrf_targe_value == '0:0':
        return False
    elif vrf_targe_value == '0.0:0':
        return False
    else:
        value_list = vrf_targe_value.split(':')
        if value_list[0].find('.') != -1:
            if not value_list[1].isdigit():
                return False
            if int(value_list[1]) > 65535:
                return False
            value = value_list[0].split('.')
            if len(value) == 4:
                for each_num in value:
                    if not each_num.isdigit():
                        return False
                if int(each_num) > 255:
                    return False
                return True
            elif len(value) == 2:
                for each_num in value:
                    if not each_num.isdigit():
                        return False
                if int(each_num) > 65535:
                    return False
                return True
            else:
                return False
        elif not value_list[0].isdigit():
            return False
        elif not value_list[1].isdigit():
            return False
        elif int(value_list[0]) < 65536 and int(value_list[1]) < 4294967296:
            return True
        elif int(value_list[0]) > 65535 and int(value_list[0]) < 4294967296:
            return bool(int(value_list[1]) < 65536)
        else:
            return False


class EvpnBd(object):
    """Manange evpn instance in BD view"""

    def __init__(self, argument_spec, ):
        self.spec = argument_spec
        self.module = None
        self.__init_module__()

        # EVPN instance info
        self.bridge_domain_id = self.module.params['bridge_domain_id']
        self.evpn = self.module.params['evpn']
        self.route_distinguisher = self.module.params['route_distinguisher']
        self.vpn_target_both = self.module.params['vpn_target_both'] or list()
        self.vpn_target_import = self.module.params[
            'vpn_target_import'] or list()
        self.vpn_target_export = self.module.params[
            'vpn_target_export'] or list()
        self.state = self.module.params['state']
        self.__string_to_lowercase__()

        self.commands = list()
        self.evpn_info = dict()
        self.conf_exist = False

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.password = self.module.params['password']
        self.port = self.module.params['port']

        self.netconf = None
        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

        self.__init_netconf__()

    def __init_module__(self):
        """init module"""

        self.module = NetworkModule(
            argument_spec=self.spec, connect_on_load=False, supports_check_mode=True)

    def __init_netconf__(self):
        """ init netconf interface"""

        if HAS_NCCLIENT:
            self.netconf = get_netconf(host=self.host, port=self.port,
                                       username=self.username,
                                       password=self.module.params['password'])
            if not self.netconf:
                self.module.fail_json(msg='Error: netconf init failed')
        else:
            self.module.fail_json(
                msg='Error: No ncclient package, please install it.')

    def __check_response__(self, con_obj, xml_name):
        """Check if response message is already succeed."""

        xml_str = con_obj.xml
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def __netconf_get_config__(self, xml_str):
        """ netconf get config """

        try:
            con_obj = self.netconf.get_config(filter=xml_str)
        except RPCError:
            err = sys.exc_info()[1]
            self.module.fail_json(msg='Error: %s' %
                                  err.message.replace("\r\n", ""))

        return con_obj

    def __netconf_set_config__(self, xml_str, xml_name):
        """ netconf set config """

        try:
            con_obj = self.netconf.set_config(config=xml_str)
            self.__check_response__(con_obj, xml_name)
        except RPCError:
            err = sys.exc_info()[1]
            self.module.fail_json(msg='Error: %s' %
                                  err.message.replace("\r\n", ""))

        return con_obj

    def __string_to_lowercase__(self):
        """convert string to lowercase"""

        if self.route_distinguisher:
            self.route_distinguisher = self.route_distinguisher.lower()

        if self.vpn_target_export:
            for index, ele in enumerate(self.vpn_target_export):
                self.vpn_target_export[index] = ele.lower()

        if self.vpn_target_import:
            for index, ele in enumerate(self.vpn_target_import):
                self.vpn_target_import[index] = ele.lower()

        if self.vpn_target_both:
            for index, ele in enumerate(self.vpn_target_both):
                self.vpn_target_both[index] = ele.lower()

    def get_all_evpn_rts(self, evpn_rts):
        """get all EVPN RTS"""

        rts = evpn_rts.findall("evpnRT")
        if not rts:
            return

        for ele in rts:
            vrf_rttype = ele.find('vrfRTType')
            vrf_rtvalue = ele.find('vrfRTValue')

            if vrf_rttype.text == 'export_extcommunity':
                self.evpn_info['vpn_target_export'].append(vrf_rtvalue.text)
            elif vrf_rttype.text == 'import_extcommunity':
                self.evpn_info['vpn_target_import'].append(vrf_rtvalue.text)

    def get_all_evpn_autorts(self, evpn_autorts):
        """"get all EVPN AUTORTS"""

        autorts = evpn_autorts.findall("evpnAutoRT")
        if not autorts:
            return

        for autort in autorts:
            vrf_rttype = autort.find('vrfRTType')

            if vrf_rttype.text == 'export_extcommunity':
                self.evpn_info['vpn_target_export'].append('auto')
            elif vrf_rttype.text == 'import_extcommunity':
                self.evpn_info['vpn_target_import'].append('auto')

    def process_rts_info(self):
        """Process RTS information"""

        if not self.evpn_info['vpn_target_export'] or\
                not self.evpn_info['vpn_target_import']:
            return

        vpn_target_export = copy.deepcopy(self.evpn_info['vpn_target_export'])
        for ele in vpn_target_export:
            if ele in self.evpn_info['vpn_target_import']:
                self.evpn_info['vpn_target_both'].append(ele)
                self.evpn_info['vpn_target_export'].remove(ele)
                self.evpn_info['vpn_target_import'].remove(ele)

    def get_evpn_instance_info(self):
        """ get current EVPN instance information"""
        if not self.bridge_domain_id:
            self.module.fail_json(msg='Error: The value of bridge_domain_id cannot be empty.')

        self.evpn_info['route_distinguisher'] = None
        self.evpn_info['vpn_target_import'] = list()
        self.evpn_info['vpn_target_export'] = list()
        self.evpn_info['vpn_target_both'] = list()
        self.evpn_info['evpn_inst'] = 'true'

        xml_str = CE_NC_GET_EVPN_CONFIG % (
            self.bridge_domain_id, self.bridge_domain_id)
        con_obj = self.__netconf_get_config__(xml_str)
        if "<data/>" in con_obj.xml:
            self.evpn_info['evpn_inst'] = 'false'
            return

        xml_str = con_obj.xml.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        root = ElementTree.fromstring(xml_str)
        evpn_inst = root.find("data/evpn/evpnInstances/evpnInstance")
        if evpn_inst:
            for eles in evpn_inst:
                if eles.tag in ["evpnAutoRD", "evpnRD", "evpnRTs", "evpnAutoRTs"]:
                    if eles.tag == 'evpnAutoRD' and eles.text == 'true':
                        self.evpn_info['route_distinguisher'] = 'auto'
                    elif eles.tag == 'evpnRD' and self.evpn_info['route_distinguisher'] != 'auto':
                        self.evpn_info['route_distinguisher'] = eles.text
                    elif eles.tag == 'evpnRTs':
                        self.get_all_evpn_rts(eles)
                    elif eles.tag == 'evpnAutoRTs':
                        self.get_all_evpn_autorts(eles)
            self.process_rts_info()

    def get_existing(self):
        """get existing config"""

        self.existing = dict(bridge_domain_id=self.bridge_domain_id,
                             evpn=self.evpn_info['evpn_inst'],
                             route_distinguisher=self.evpn_info[
                                 'route_distinguisher'],
                             vpn_target_both=self.evpn_info['vpn_target_both'],
                             vpn_target_import=self.evpn_info[
                                 'vpn_target_import'],
                             vpn_target_export=self.evpn_info['vpn_target_export'])

    def get_proposed(self):
        """get proposed config"""

        self.proposed = dict(bridge_domain_id=self.bridge_domain_id,
                             evpn=self.evpn,
                             route_distinguisher=self.route_distinguisher,
                             vpn_target_both=self.vpn_target_both,
                             vpn_target_import=self.vpn_target_import,
                             vpn_target_export=self.vpn_target_export,
                             state=self.state)

    def get_end_state(self):
        """get end config"""

        self.get_evpn_instance_info()
        self.end_state = dict(bridge_domain_id=self.bridge_domain_id,
                              evpn=self.evpn_info['evpn_inst'],
                              route_distinguisher=self.evpn_info[
                                  'route_distinguisher'],
                              vpn_target_both=self.evpn_info[
                                  'vpn_target_both'],
                              vpn_target_import=self.evpn_info[
                                  'vpn_target_import'],
                              vpn_target_export=self.evpn_info['vpn_target_export'])

    def show_result(self):
        """ show result"""

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)

    def judge_if_vpn_target_exist(self, vpn_target_type):
        """judge whether proposed vpn target has existed"""

        vpn_target = list()
        if vpn_target_type == 'vpn_target_import':
            vpn_target.extend(self.existing['vpn_target_both'])
            vpn_target.extend(self.existing['vpn_target_import'])
            return set(self.proposed['vpn_target_import']).issubset(vpn_target)
        elif vpn_target_type == 'vpn_target_export':
            vpn_target.extend(self.existing['vpn_target_both'])
            vpn_target.extend(self.existing['vpn_target_export'])
            return set(self.proposed['vpn_target_export']).issubset(vpn_target)

        return False

    def judge_if_config_exist(self):
        """ judge whether configuration has existed"""

        if self.state == 'absent':
            if self.route_distinguisher or self.vpn_target_import or self.vpn_target_export or self.vpn_target_both:
                return False
            else:
                return True

        if self.evpn_info['evpn_inst'] != self.evpn:
            return False

        if self.evpn == 'false' and self.evpn_info['evpn_inst'] == 'false':
            return True

        if self.proposed['bridge_domain_id'] != self.existing['bridge_domain_id']:
            return False

        if self.proposed['route_distinguisher']:
            if self.proposed['route_distinguisher'] != self.existing['route_distinguisher']:
                return False

        if self.proposed['vpn_target_both']:
            if not self.existing['vpn_target_both']:
                return False
            if not set(self.proposed['vpn_target_both']).issubset(self.existing['vpn_target_both']):
                return False

        if self.proposed['vpn_target_import']:
            if not self.judge_if_vpn_target_exist('vpn_target_import'):
                return False

        if self.proposed['vpn_target_export']:
            if not self.judge_if_vpn_target_exist('vpn_target_export'):
                return False

        return True

    def unconfig_evpn_instance(self):
        """unconfigure EVPN instance"""

        self.updates_cmd.append("bridge-domain %s" % self.bridge_domain_id)
        xml_str = CE_NC_MERGE_EVPN_CONFIG_HEAD % (
            self.bridge_domain_id, self.bridge_domain_id)
        self.updates_cmd.append("  evpn")

        # unconfigure RD
        if self.route_distinguisher:
            if self.route_distinguisher.lower() == 'auto':
                xml_str += '<evpnAutoRD>false</evpnAutoRD>'
                self.updates_cmd.append("    undo route-distinguisher auto")
            else:
                xml_str += '<evpnRD></evpnRD>'
                self.updates_cmd.append(
                    "    undo route-distinguisher %s" % self.route_distinguisher)
            xml_str += CE_NC_MERGE_EVPN_CONFIG_TAIL
            self.__netconf_set_config__(xml_str, "UNDO_EVPN_BD_RD")
            self.changed = True
            return

        # process VPN target list
        vpn_target_export = copy.deepcopy(self.vpn_target_export)
        vpn_target_import = copy.deepcopy(self.vpn_target_import)
        if self.vpn_target_both:
            for ele in self.vpn_target_both:
                if ele not in vpn_target_export:
                    vpn_target_export.append(ele)
                if ele not in vpn_target_import:
                    vpn_target_import.append(ele)

        # unconfig EVPN auto RTS
        head_flag = False
        if vpn_target_export:
            for ele in vpn_target_export:
                if ele.lower() == 'auto':
                    if not head_flag:
                        xml_str += CE_NC_MERGE_EVPN_AUTORTS_HEAD
                        head_flag = True
                    xml_str += CE_NC_DELETE_EVPN_AUTORTS_CONTEXT % (
                        'export_extcommunity')
                    self.updates_cmd.append(
                        "    undo vpn-target auto export-extcommunity")
        if vpn_target_import:
            for ele in vpn_target_import:
                if ele.lower() == 'auto':
                    if not head_flag:
                        xml_str += CE_NC_MERGE_EVPN_AUTORTS_HEAD
                        head_flag = True
                    xml_str += CE_NC_DELETE_EVPN_AUTORTS_CONTEXT % (
                        'import_extcommunity')
                    self.updates_cmd.append(
                        "    undo vpn-target auto import-extcommunity")

        if head_flag:
            xml_str += CE_NC_MERGE_EVPN_AUTORTS_TAIL

        # unconfig EVPN RTS
        head_flag = False
        if vpn_target_export:
            for ele in vpn_target_export:
                if ele.lower() != 'auto':
                    if not head_flag:
                        xml_str += CE_NC_MERGE_EVPN_RTS_HEAD
                        head_flag = True
                    xml_str += CE_NC_DELETE_EVPN_RTS_CONTEXT % (
                        'export_extcommunity', ele)
                    self.updates_cmd.append(
                        "    undo vpn-target %s export-extcommunity" % ele)

        if vpn_target_import:
            for ele in vpn_target_import:
                if ele.lower() != 'auto':
                    if not head_flag:
                        xml_str += CE_NC_MERGE_EVPN_RTS_HEAD
                        head_flag = True
                    xml_str += CE_NC_DELETE_EVPN_RTS_CONTEXT % (
                        'import_extcommunity', ele)
                    self.updates_cmd.append(
                        "    undo vpn-target %s import-extcommunity" % ele)

        if head_flag:
            xml_str += CE_NC_MERGE_EVPN_RTS_TAIL

        xml_str += CE_NC_MERGE_EVPN_CONFIG_TAIL
        self.__netconf_set_config__(xml_str, "MERGE_EVPN_BD_VPN_TARGET_CONFIG")
        self.changed = True

    def config_evpn_instance(self):
        """configure EVPN instance"""

        self.updates_cmd.append("bridge-domain %s" % self.bridge_domain_id)

        if self.evpn == 'false':
            xml_str = CE_NC_DELETE_EVPN_CONFIG % (
                self.bridge_domain_id, self.bridge_domain_id)
            self.__netconf_set_config__(xml_str, "MERGE_EVPN_BD_CONFIG")
            self.updates_cmd.append("  undo evpn")
            self.changed = True
            return

        xml_str = CE_NC_MERGE_EVPN_CONFIG_HEAD % (
            self.bridge_domain_id, self.bridge_domain_id)
        self.updates_cmd.append("  evpn")

        # configure RD
        if self.route_distinguisher:
            if not self.existing['route_distinguisher']:
                if self.route_distinguisher.lower() == 'auto':
                    xml_str += '<evpnAutoRD>true</evpnAutoRD>'
                    self.updates_cmd.append("    route-distinguisher auto")
                else:
                    xml_str += '<evpnRD>%s</evpnRD>' % self.route_distinguisher
                    self.updates_cmd.append(
                        "    route-distinguisher %s" % self.route_distinguisher)

        # process VPN target list
        vpn_target_export = copy.deepcopy(self.vpn_target_export)
        vpn_target_import = copy.deepcopy(self.vpn_target_import)
        if self.vpn_target_both:
            for ele in self.vpn_target_both:
                if ele not in vpn_target_export:
                    vpn_target_export.append(ele)
                if ele not in vpn_target_import:
                    vpn_target_import.append(ele)

        # config EVPN auto RTS
        head_flag = False
        if vpn_target_export:
            for ele in vpn_target_export:
                if ele.lower() == 'auto' and \
                        (not self.is_vpn_target_exist('export_extcommunity', ele.lower())):
                    if not head_flag:
                        xml_str += CE_NC_MERGE_EVPN_AUTORTS_HEAD
                        head_flag = True
                    xml_str += CE_NC_MERGE_EVPN_AUTORTS_CONTEXT % (
                        'export_extcommunity')
                    self.updates_cmd.append(
                        "    vpn-target auto export-extcommunity")
        if vpn_target_import:
            for ele in vpn_target_import:
                if ele.lower() == 'auto' and \
                        (not self.is_vpn_target_exist('import_extcommunity', ele.lower())):
                    if not head_flag:
                        xml_str += CE_NC_MERGE_EVPN_AUTORTS_HEAD
                        head_flag = True
                    xml_str += CE_NC_MERGE_EVPN_AUTORTS_CONTEXT % (
                        'import_extcommunity')
                    self.updates_cmd.append(
                        "    vpn-target auto import-extcommunity")

        if head_flag:
            xml_str += CE_NC_MERGE_EVPN_AUTORTS_TAIL

        # config EVPN RTS
        head_flag = False
        if vpn_target_export:
            for ele in vpn_target_export:
                if ele.lower() != 'auto' and \
                        (not self.is_vpn_target_exist('export_extcommunity', ele.lower())):
                    if not head_flag:
                        xml_str += CE_NC_MERGE_EVPN_RTS_HEAD
                        head_flag = True
                    xml_str += CE_NC_MERGE_EVPN_RTS_CONTEXT % (
                        'export_extcommunity', ele)
                    self.updates_cmd.append(
                        "    vpn-target %s export-extcommunity" % ele)

        if vpn_target_import:
            for ele in vpn_target_import:
                if ele.lower() != 'auto' and \
                        (not self.is_vpn_target_exist('import_extcommunity', ele.lower())):
                    if not head_flag:
                        xml_str += CE_NC_MERGE_EVPN_RTS_HEAD
                        head_flag = True
                    xml_str += CE_NC_MERGE_EVPN_RTS_CONTEXT % (
                        'import_extcommunity', ele)
                    self.updates_cmd.append(
                        "    vpn-target %s import-extcommunity" % ele)

        if head_flag:
            xml_str += CE_NC_MERGE_EVPN_RTS_TAIL

        xml_str += CE_NC_MERGE_EVPN_CONFIG_TAIL

        self.__netconf_set_config__(xml_str, "MERGE_EVPN_BD_CONFIG")
        self.changed = True

    def is_vpn_target_exist(self, target_type, value):
        """judge whether VPN target has existed"""

        if target_type == 'export_extcommunity':
            if (value not in self.existing['vpn_target_export']) and\
                    (value not in self.existing['vpn_target_both']):
                return False
            return True

        if target_type == 'import_extcommunity':
            if (value not in self.existing['vpn_target_import']) and\
                    (value not in self.existing['vpn_target_both']):
                return False
            return True

        return False

    def config_evnp_bd(self):
        """configure EVPN in BD view"""

        if not self.conf_exist:
            if self.state == 'present':
                self.config_evpn_instance()
            else:
                self.unconfig_evpn_instance()

    def process_input_params(self):
        """Process input parameters"""

        if self.state == 'absent':
            self.evpn = None
        else:
            if self.evpn == 'false':
                return

        if self.vpn_target_both:
            for ele in self.vpn_target_both:
                if ele in self.vpn_target_export:
                    self.vpn_target_export.remove(ele)
                if ele in self.vpn_target_import:
                    self.vpn_target_import.remove(ele)

        if self.vpn_target_export and self.vpn_target_import:
            vpn_target_export = copy.deepcopy(self.vpn_target_export)
            for ele in vpn_target_export:
                if ele in self.vpn_target_import:
                    self.vpn_target_both.append(ele)
                    self.vpn_target_import.remove(ele)
                    self.vpn_target_export.remove(ele)

    def check_vpn_target_para(self):
        """Check whether VPN target value is valid"""

        if self.route_distinguisher:
            if self.route_distinguisher.lower() != 'auto' and\
                    not is_valid_value(self.route_distinguisher):
                self.module.fail_json(
                    msg='Error: Route distinguisher has invalid value %s.' % self.route_distinguisher)

        if self.vpn_target_export:
            for ele in self.vpn_target_export:
                if ele.lower() != 'auto' and not is_valid_value(ele):
                    self.module.fail_json(
                        msg='Error: VPN target extended community attribute has invalid value %s.' % ele)

        if self.vpn_target_import:
            for ele in self.vpn_target_import:
                if ele.lower() != 'auto' and not is_valid_value(ele):
                    self.module.fail_json(
                        msg='Error: VPN target extended community attribute has invalid value %s.' % ele)

        if self.vpn_target_both:
            for ele in self.vpn_target_both:
                if ele.lower() != 'auto' and not is_valid_value(ele):
                    self.module.fail_json(
                        msg='Error: VPN target extended community attribute has invalid value %s.' % ele)

    def check_undo_params_if_exist(self):
        """check whether all undo parameters is existed"""

        if self.vpn_target_import:
            for ele in self.vpn_target_import:
                if ele not in self.evpn_info['vpn_target_import'] and ele not in self.evpn_info['vpn_target_both']:
                    self.module.fail_json(
                        msg='Error: VPN target import attribute value %s doesnot exist.' % ele)

        if self.vpn_target_export:
            for ele in self.vpn_target_export:
                if ele not in self.evpn_info['vpn_target_export'] and ele not in self.evpn_info['vpn_target_both']:
                    self.module.fail_json(
                        msg='Error: VPN target export attribute value %s doesnot exist.' % ele)

        if self.vpn_target_both:
            for ele in self.vpn_target_both:
                if ele not in self.evpn_info['vpn_target_both']:
                    self.module.fail_json(
                        msg='Error: VPN target export and import attribute value %s doesnot exist.' % ele)

    def check_params(self):
        """Check all input params"""

        # bridge_domain_id check
        if self.bridge_domain_id:
            if not self.bridge_domain_id.isdigit():
                self.module.fail_json(
                    msg='Error: The parameter of bridge domain id is invalid.')
            if int(self.bridge_domain_id) > 16777215 or int(self.bridge_domain_id) < 1:
                self.module.fail_json(
                    msg='Error: The bridge domain id must be an integer between 1 and 16777215.')

        if self.state == 'absent':
            self.check_undo_params_if_exist()

        # check bd whether binding the vxlan vni
        self.check_vni_bd()
        self.check_vpn_target_para()

        if self.state == 'absent':
            if self.route_distinguisher:
                if not self.evpn_info['route_distinguisher']:
                    self.module.fail_json(
                        msg='Error: Route distinguisher doesnot have been configured.')
                else:
                    if self.route_distinguisher != self.evpn_info['route_distinguisher']:
                        self.module.fail_json(
                            msg='Error: Current route distinguisher value is %s.' %
                            self.evpn_info['route_distinguisher'])

        if self.state == 'present':
            if self.route_distinguisher:
                if self.evpn_info['route_distinguisher'] and\
                        self.route_distinguisher != self.evpn_info['route_distinguisher']:
                    self.module.fail_json(
                        msg='Error: Route distinguisher has already been configured.')

    def check_vni_bd(self):
        """Check whether vxlan vni is configured in BD view"""

        xml_str = CE_NC_GET_VNI_BD % self.bridge_domain_id
        con_obj = self.__netconf_get_config__(xml_str)
        if "<data/>" in con_obj.xml:
            self.module.fail_json(
                msg='Error: The vxlan vni is not configured or the bridge domain id is invalid.')

    def work(self):
        """excute task"""

        self.get_evpn_instance_info()
        self.process_input_params()
        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.conf_exist = self.judge_if_config_exist()

        self.config_evnp_bd()

        self.get_end_state()
        self.show_result()


def main():
    """main function entry"""

    argument_spec = dict(
        bridge_domain_id=dict(required=True, type='str'),
        evpn=dict(required=False, type='str',
                  default='true', choices=['true', 'false']),
        route_distinguisher=dict(required=False, type='str'),
        vpn_target_both=dict(required=False, type='list'),
        vpn_target_import=dict(required=False, type='list'),
        vpn_target_export=dict(required=False, type='list'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent'])
    )

    evpn_bd = EvpnBd(argument_spec)
    evpn_bd.work()

if __name__ == '__main__':
    main()
