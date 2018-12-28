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
# GNU General Public License for more detai++++++++ls.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from ansible.modules.network.ne.snmp.ne_snmp_base import config_params_func
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'snmp'}

DOCUMENTATION = '''
---
module: ne_snmp_get_config
version_added: "2.6"
short_description: Get snmp configurations.
description:
    - Get snmp configurations that include snmp enable, version, mibviews, communitys, engineID, \
    V3 groups, usm users, target host, trap enable status and one trap config status.
author:Zhaweiwei(@netengine-Ansible)

options:
    get_single_trap_switch:
        description:
            - Whether get single trap switch's configuration.
        required: no
        default: null
        choices: ['yes', 'no']
'''

EXAMPLES = '''

- name: ne_snmp_get_config
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    yang:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"

  tasks:

  - name: "Get snmp config"
    ne_snmp_get_config:
      get_single_trap_switch: no
'''

RETURN = '''
    "changed": false,
    "get_response": [
        {
            "global_info": {
                "agentEnable": "true",
                "engineID": "800007XX0338XXXX2BCA01",
                "gblTrapSwitch": "enable",
                "version": "v2c"
            }
        },
        {
            "mib_view_info": [
                {
                    "subtree": "iso",
                    "type": "included",
                    "viewName": "abc"
                },
                {
                    "subtree": "iso",
                    "type": "included",
                    "viewName": "myview"
                },
                {
                    "subtree": "internet",
                    "type": "included",
                    "viewName": "ViewDefault"
                },
                {
                    "subtree": "snmpCommunityMIB",
                    "type": "excluded",
                    "viewName": "ViewDefault"
                },
                {
                    "subtree": "snmpUsmMIB",
                    "type": "excluded",
                    "viewName": "ViewDefault"
                },
                {
                    "subtree": "snmpVacmMIB",
                    "type": "excluded",
                    "viewName": "ViewDefault"
                }
            ]
        },
        {
            "community_info": [
                {
                    "accessRight": "write",
                    "communityName": "%^%#Jx[|LtP:5~ZrKw9>(3RW2nKlL&pb0A%TYmEsS5@\"kT~[L`8b-..G{P@(7P#Yh]-;<s[Qp8rV%1Ot'jJ/%^%#",
                    "mibViewName": "myview"
                },
                {
                    "accessRight": "read",
                    "communityName": "%^%#:f<cO\"Hli%ubx;'=d$-7~[Gm(pY_NPCL5=-#JofHn>%A@I]o9Z/6bEP\\7FE.g7aPW>\"9/7VhS%-Mvh^!%^%#",
                    "mibViewName": "myview"
                },
                {
                    "accessRight": "read",
                    "aclNumber": "2000",
                    "communityName": "%^%#R#heJg`3;9ZO!ZWelXLY<sJ<7lm*iX5y>@#/c'{;^FmkSMLLCZ|}9'Q+Piy-0@Ft8IP/i.!58OC2}Q|L%^%#",
                    "mibViewName": "ViewDefault"
                }
            ]
        },
        {
            "V3_group_info": [
                {
                    "groupName": "test",
                    "notifyViewName": "myview",
                    "readViewName": "myview",
                    "securityLevel": "privacy",
                    "writeViewName": "myview"
                },
                {
                    "groupName": "v3test",
                    "notifyViewName": "myview",
                    "readViewName": "myview",
                    "securityLevel": "privacy",
                    "writeViewName": "myview"
                }
            ]
        },
        {
            "usm_user_info": [
                {
                    "aclNumber": "2000",
                    "authKey": "%^%#)E9fE7IxqTs@+KH!{IlUHzTkKZRkJG`EpMB>_s48%^%#",
                    "authProtocol": "md5",
                    "engineID": "800007DB0338BA142BCA01",
                    "privKey": "%^%#10\\LF7_E\"=F~7WA%0aT+iDLoB9hm@DiY3.-nf9}4%^%#",
                    "privProtocol": "aes128",
                    "remoteEngineID": "false",
                    "userName": "abc"
                },
                {
                    "authKey": "%^%#nkgt4[qZ,FN($`YT%\".QlaAx>%*Ls=JRI_5w*b#J%^%#",
                    "authProtocol": "sha",
                    "engineID": "800007DB0338BA142BCA01",
                    "groupName": "v3test",
                    "privKey": "%^%#PfFgOR7lMNPBLL4!Ii<Jbq4@,&Q~p,)@GWW+4o)~%^%#",
                    "privProtocol": "des56",
                    "remoteEngineID": "false",
                    "userName": "test"
                }
            ]
        },
        {
            "target_host_info": [
                {
                    "address": "1.100.100.100",
                    "domain": "snmpUDPDomain",
                    "nmsName": "abc",
                    "notifyType": "trap",
                    "portNumber": "2017",
                    "securityLevel": "noAuthNoPriv",
                    "securityModel": "v2c",
                    "securityName": "%^%#@'W!Ji|YcA}{]\"VZfFR,B`ms4K~PO-fA$qV7dVo3%^%#"
                }
            ]
        }
    ]
'''

SNMP_GET_ENABLE = """
  <filter type="subtree">
    <snmp:snmp xmlns:snmp="http://www.huawei.com/netconf/vrp/huawei-snmp">
      <snmp:agentCfg>
        <snmp:agentEnable/>
      </snmp:agentCfg>
    </snmp:snmp>
  </filter>
"""

SNMP_GET_VERSION = """
  <filter type="subtree">
    <snmp:snmp xmlns:snmp="http://www.huawei.com/netconf/vrp/huawei-snmp">
      <snmp:engine>
        <snmp:version/>
      </snmp:engine>
    </snmp:snmp>
  </filter>
"""

SNMP_GET_ENGINEID = """
  <filter type="subtree">
    <snmp:snmp xmlns:snmp="http://www.huawei.com/netconf/vrp/huawei-snmp">
      <snmp:engine>
        <snmp:engineID/>
      </snmp:engine>
    </snmp:snmp>
  </filter>
"""

SNMP_GET_ACL = """
  <filter type="subtree">
    <snmp:snmp xmlns:snmp="http://www.huawei.com/netconf/vrp/huawei-snmp">
      <snmp:systemCfg>
        <snmp:acl/>
      </snmp:systemCfg>
    </snmp:snmp>
  </filter>
"""

SNMP_GET_MIBVIEW = """
  <filter type="subtree">
    <snmp:snmp xmlns:snmp="http://www.huawei.com/netconf/vrp/huawei-snmp">
      <snmp:mibViews>
        <snmp:mibView/>
      </snmp:mibViews>
    </snmp:snmp>
  </filter>
"""

SNMP_GET_COMMUNITY = """
  <filter type="subtree">
    <snmp:snmp xmlns:snmp="http://www.huawei.com/netconf/vrp/huawei-snmp">
      <snmp:communitys>
        <snmp:community/>
      </snmp:communitys>
    </snmp:snmp>
  </filter>
"""

SNMP_GET_USERGROUP = """
  <filter type="subtree">
    <snmp:snmp xmlns:snmp="http://www.huawei.com/netconf/vrp/huawei-snmp">
      <snmp:snmpv3Groups>
        <snmp:snmpv3Group/>
      </snmp:snmpv3Groups>
    </snmp:snmp>
  </filter>
"""

SNMP_GET_USMUSER = """
  <filter type="subtree">
    <snmp:snmp xmlns:snmp="http://www.huawei.com/netconf/vrp/huawei-snmp">
      <snmp:usmUsers>
        <snmp:usmUser/>
      </snmp:usmUsers>
    </snmp:snmp>
  </filter>
"""

SNMP_GET_TGTHOST = """
  <filter type="subtree">
    <snmp:snmp xmlns:snmp="http://www.huawei.com/netconf/vrp/huawei-snmp">
      <snmp:targetHosts>
        <snmp:targetHost/>
      </snmp:targetHosts>
    </snmp:snmp>
  </filter>
"""

SNMP_GET_TRAP_ENABLE = """
  <filter type="subtree">
    <fm:fm xmlns:fm="http://www.huawei.com/netconf/vrp/huawei-fm">
      <fm:globalParam>
        <fm:gblTrapSwitch/>
      </fm:globalParam>
    </fm:fm>
  </filter>
"""

SNMP_GET_TRAPCONF = """
  <filter type="subtree">
    <fm:fm xmlns:fm="http://www.huawei.com/netconf/vrp/huawei-fm">
      <fm:trapCfgs>
        <fm:trapCfg/>
      </fm:trapCfgs>
    </fm:fm>
  </filter>
"""


def get_snmp_enable_config(module):

    recv_xml = get_nc_config(module, SNMP_GET_ENABLE)
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp"', "")

    root = ElementTree.fromstring(xml_str)
    enable_info = root.findall("snmp/agentCfg")
    tmp_dict = dict()
    if enable_info:
        for tmp in enable_info:
            for site in tmp:
                if site.tag in ["agentEnable"]:
                    tmp_dict[site.tag] = site.text

    return tmp_dict


def get_snmp_version_config(module):
    recv_xml = get_nc_config(module, SNMP_GET_VERSION)
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp"', "")

    root = ElementTree.fromstring(xml_str)
    cfg_info = root.findall("snmp/engine")
    tmp_dict = dict()
    if cfg_info:
        for tmp in cfg_info:
            for site in tmp:
                if site.tag in ["version"]:
                    tmp_dict[site.tag] = site.text

    return tmp_dict


def get_snmp_engineid_config(module):
    recv_xml = get_nc_config(module, SNMP_GET_ENGINEID)
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp"', "")

    root = ElementTree.fromstring(xml_str)
    cfg_info = root.findall("snmp/engine")
    tmp_dict = dict()
    if cfg_info:
        for tmp in cfg_info:
            for site in tmp:
                if site.tag in ["engineID"]:
                    tmp_dict[site.tag] = site.text

    return tmp_dict


def get_snmp_acl_config(module):
    recv_xml = get_nc_config(module, SNMP_GET_ACL)
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp"', "")

    root = ElementTree.fromstring(xml_str)
    cfg_info = root.findall("snmp/systemCfg")
    tmp_dict = dict()
    if cfg_info:
        for tmp in cfg_info:
            for site in tmp:
                if site.tag in ["acl"]:
                    tmp_dict[site.tag] = site.text

    return tmp_dict


def get_snmp_trap_enable_config(module):

    recv_xml = get_nc_config(module, SNMP_GET_TRAP_ENABLE)
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-fm"', "")

    root = ElementTree.fromstring(xml_str)
    enable_info = root.findall("fm/globalParam")
    tmp_dict = dict()
    if enable_info:
        for tmp in enable_info:
            for site in tmp:
                if site.tag in ["gblTrapSwitch"]:
                    tmp_dict[site.tag] = site.text

    return tmp_dict


def get_snmp_mibview_config(module):
    recv_xml = get_nc_config(module, SNMP_GET_MIBVIEW)
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp"', "")

    root = ElementTree.fromstring(xml_str)
    cfg_info = root.findall("snmp/mibViews/mibView")

    result = dict()
    result["mib_view_info"] = []
    if cfg_info:
        for temp in cfg_info:
            tmp_dict = dict()
            for site in temp:
                if site.tag in ["viewName", "subtree", "type"]:
                    tmp_dict[site.tag] = site.text
            result["mib_view_info"].append(tmp_dict)

    return result


def get_snmp_community_config(module):
    recv_xml = get_nc_config(module, SNMP_GET_COMMUNITY)
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp"', "")

    root = ElementTree.fromstring(xml_str)
    cfg_info = root.findall("snmp/communitys/community")

    result = dict()
    result["community_info"] = []
    if cfg_info:
        for temp in cfg_info:
            tmp_dict = dict()
            for site in temp:
                if site.tag in ["communityName",
                                "accessRight", "mibViewName", "aclNumber"]:
                    tmp_dict[site.tag] = site.text
            result["community_info"].append(tmp_dict)

    return result


def get_snmp_usergroup_config(module):
    recv_xml = get_nc_config(module, SNMP_GET_USERGROUP)
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp"', "")

    root = ElementTree.fromstring(xml_str)
    cfg_info = root.findall("snmp/snmpv3Groups/snmpv3Group")

    result = dict()
    result["V3_group_info"] = []
    if cfg_info:
        for temp in cfg_info:
            tmp_dict = dict()
            for site in temp:
                if site.tag in ["groupName", "securityLevel", "readViewName",
                                "writeViewName", "notifyViewName", "aclNumber"]:
                    tmp_dict[site.tag] = site.text
            result["V3_group_info"].append(tmp_dict)

    return result


def get_snmp_usmuser_config(module):
    recv_xml = get_nc_config(module, SNMP_GET_USMUSER)
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp"', "")

    root = ElementTree.fromstring(xml_str)
    cfg_info = root.findall("snmp/usmUsers/usmUser")

    result = dict()
    result["usm_user_info"] = []
    if cfg_info:
        for temp in cfg_info:
            tmp_dict = dict()
            for site in temp:
                if site.tag in ["userName", "remoteEngineID", "engineID",
                                "authProtocol", "authKey", "privProtocol",
                                "privKey", "aclNumber", "groupName"]:
                    tmp_dict[site.tag] = site.text
            result["usm_user_info"].append(tmp_dict)

    return result


def get_snmp_tgthost_config(module):
    recv_xml = get_nc_config(module, SNMP_GET_TGTHOST)
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp"', "")

    root = ElementTree.fromstring(xml_str)
    cfg_info = root.findall("snmp/targetHosts/targetHost")

    result = dict()
    result["target_host_info"] = []
    if cfg_info:
        for temp in cfg_info:
            tmp_dict = dict()
            for site in temp:
                if site.tag in ["nmsName", "address", "portNumber",
                                "securityName", "securityModel", "securityLevel",
                                "notifyType", "domain", "securityNameV3"]:
                    tmp_dict[site.tag] = site.text
            result["target_host_info"].append(tmp_dict)

    return result


def get_trap_config(module):
    recv_xml = get_nc_config(module, SNMP_GET_TRAPCONF)
    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-fm"', "")

    root = ElementTree.fromstring(xml_str)
    cfg_info = root.findall("fm/trapCfgs/trapCfg")

    result = dict()
    result["trap_conf_info"] = []
    if cfg_info:
        for temp in cfg_info:
            tmp_dict = dict()
            for site in temp:
                if site.tag in ["trapName", "featureName", "trapCfgStatus"]:
                    tmp_dict[site.tag] = site.text
            result["trap_conf_info"].append(tmp_dict)

    return result


def main():
    """ main function """

    argument_spec = dict(
        get_single_trap_switch=dict(choices=['yes', 'no'])
    )

    argument_spec.update(ne_argument_spec)
    module = AnsibleModule(
        argument_spec=argument_spec
    )

    results = dict()
    results["get_response"] = []
    get_values = dict()
    get_result = get_snmp_enable_config(module)
    if get_result:
        for item in get_result:
            get_values[item] = get_result[item]

    get_result = get_snmp_version_config(module)
    if get_result:
        for item in get_result:
            get_values[item] = get_result[item]

    get_result = get_snmp_engineid_config(module)
    if get_result:
        for item in get_result:
            get_values[item] = get_result[item]

    get_result = get_snmp_acl_config(module)
    if get_result:
        for item in get_result:
            get_values[item] = get_result[item]

    get_result = get_snmp_trap_enable_config(module)
    if get_result:
        for item in get_result:
            get_values[item] = get_result[item]

    get_value = dict()
    get_value["global_info"] = get_values

    results["get_response"].append(get_value)

    view_values = dict()
    view_result = get_snmp_mibview_config(module)
    if view_result:
        for item in view_result:
            view_values[item] = view_result[item]

    results["get_response"].append(view_values)

    comm_values = dict()
    comm_result = get_snmp_community_config(module)
    if comm_result:
        for item in comm_result:
            comm_values[item] = comm_result[item]

    results["get_response"].append(comm_values)

    group_values = dict()
    group_result = get_snmp_usergroup_config(module)
    if group_result:
        for item in group_result:
            group_values[item] = group_result[item]

    results["get_response"].append(group_values)

    user_values = dict()
    user_result = get_snmp_usmuser_config(module)
    if user_result:
        for item in user_result:
            user_values[item] = user_result[item]

    results["get_response"].append(user_values)

    tgt_values = dict()
    tgt_result = get_snmp_tgthost_config(module)
    if tgt_result:
        for item in tgt_result:
            tgt_values[item] = tgt_result[item]

    results["get_response"].append(tgt_values)

    if config_params_func(module.params['get_single_trap_switch']):
        if module.params['get_single_trap_switch'] == "yes":
            trap_values = dict()
            trp_result = get_trap_config(module)
            if trp_result:
                for item in trp_result:
                    trap_values[item] = trp_result[item]

            results["get_response"].append(trap_values)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
