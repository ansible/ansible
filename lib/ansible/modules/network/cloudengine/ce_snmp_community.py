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
module: ce_snmp_community
version_added: "2.4"
short_description: Manages SNMP community configuration on HUAWEI CloudEngine switches.
description:
    - Manages SNMP community configuration on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@CloudEngine-Ansible)
options:
    acl_number:
        description:
            - Access control list number.
    community_name:
        description:
            - Unique name to identify the community.
    access_right:
        description:
            - Access right read or write.
        choices: ['read','write']
    community_mib_view:
        description:
            - Mib view name.
    group_name:
        description:
            - Unique name to identify the SNMPv3 group.
    security_level:
        description:
            - Security level indicating whether to use authentication and encryption.
        choices: ['noAuthNoPriv', 'authentication', 'privacy']
    read_view:
        description:
            - Mib view name for read.
    write_view:
        description:
            - Mib view name for write.
    notify_view:
        description:
            - Mib view name for notification.
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''

- name: CloudEngine snmp community test
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

  - name: "Config SNMP community"
    ce_snmp_community:
      state: present
      community_name: Wdz123456789
      access_right: write
      provider: "{{ cli }}"

  - name: "Undo SNMP community"
    ce_snmp_community:
      state: absent
      community_name: Wdz123456789
      access_right: write
      provider: "{{ cli }}"

  - name: "Config SNMP group"
    ce_snmp_community:
      state: present
      group_name: wdz_group
      security_level: noAuthNoPriv
      acl_number: 2000
      provider: "{{ cli }}"

  - name: "Undo SNMP group"
    ce_snmp_community:
      state: absent
      group_name: wdz_group
      security_level: noAuthNoPriv
      acl_number: 2000
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
    sample: {"acl_number": "2000", "group_name": "wdz_group",
             "security_level": "noAuthNoPriv", "state": "present"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"snmp v3 group": {"snmp_group": ["wdz_group", "noAuthNoPriv", "2000"]}}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["snmp-agent group v3 wdz_group noauthentication acl 2000"]
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec


# get snmp commutiny
CE_GET_SNMP_COMMUNITY_HEADER = """
    <filter type="subtree">
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <communitys>
          <community>
            <communityName></communityName>
            <accessRight></accessRight>
"""
CE_GET_SNMP_COMMUNITY_TAIL = """
          </community>
        </communitys>
      </snmp>
    </filter>
"""
# merge snmp commutiny
CE_MERGE_SNMP_COMMUNITY_HEADER = """
    <config>
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <communitys>
          <community operation="merge">
            <communityName>%s</communityName>
            <accessRight>%s</accessRight>
"""
CE_MERGE_SNMP_COMMUNITY_TAIL = """
          </community>
        </communitys>
      </snmp>
    </config>
"""
# create snmp commutiny
CE_CREATE_SNMP_COMMUNITY_HEADER = """
    <config>
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <communitys>
          <community operation="create">
            <communityName>%s</communityName>
            <accessRight>%s</accessRight>
"""
CE_CREATE_SNMP_COMMUNITY_TAIL = """
          </community>
        </communitys>
      </snmp>
    </config>
"""
# delete snmp commutiny
CE_DELETE_SNMP_COMMUNITY_HEADER = """
    <config>
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <communitys>
          <community operation="delete">
            <communityName>%s</communityName>
            <accessRight>%s</accessRight>
"""
CE_DELETE_SNMP_COMMUNITY_TAIL = """
          </community>
        </communitys>
      </snmp>
    </config>
"""

# get snmp v3 group
CE_GET_SNMP_V3_GROUP_HEADER = """
    <filter type="subtree">
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <snmpv3Groups>
          <snmpv3Group>
            <groupName></groupName>
            <securityLevel></securityLevel>
"""
CE_GET_SNMP_V3_GROUP_TAIL = """
          </snmpv3Group>
        </snmpv3Groups>
      </snmp>
    </filter>
"""
# merge snmp v3 group
CE_MERGE_SNMP_V3_GROUP_HEADER = """
    <config>
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <snmpv3Groups>
          <snmpv3Group operation="merge">
            <groupName>%s</groupName>
            <securityLevel>%s</securityLevel>
"""
CE_MERGE_SNMP_V3_GROUP_TAIL = """
          </snmpv3Group>
        </snmpv3Groups>
      </snmp>
    </filter>
"""
# create snmp v3 group
CE_CREATE_SNMP_V3_GROUP_HEADER = """
    <config>
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <snmpv3Groups>
          <snmpv3Group operation="create">
            <groupName>%s</groupName>
            <securityLevel>%s</securityLevel>
"""
CE_CREATE_SNMP_V3_GROUP_TAIL = """
          </snmpv3Group>
        </snmpv3Groups>
      </snmp>
    </filter>
"""
# delete snmp v3 group
CE_DELETE_SNMP_V3_GROUP_HEADER = """
    <config>
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <snmpv3Groups>
          <snmpv3Group operation="delete">
            <groupName>%s</groupName>
            <securityLevel>%s</securityLevel>
"""
CE_DELETE_SNMP_V3_GROUP_TAIL = """
          </snmpv3Group>
        </snmpv3Groups>
      </snmp>
    </filter>
"""


class SnmpCommunity(object):
    """ Manages SNMP community configuration """

    def netconf_get_config(self, **kwargs):
        """ Get configure through netconf """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        xml_str = get_nc_config(module, conf_str)

        return xml_str

    def netconf_set_config(self, **kwargs):
        """ Set configure through netconf """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        xml_str = set_nc_config(module, conf_str)

        return xml_str

    def check_snmp_community_args(self, **kwargs):
        """ Check snmp community args """

        module = kwargs["module"]
        result = dict()
        need_cfg = False
        result["community_info"] = []
        state = module.params['state']
        community_name = module.params['community_name']
        access_right = module.params['access_right']
        acl_number = module.params['acl_number']
        community_mib_view = module.params['community_mib_view']

        if community_name and access_right:
            if len(community_name) > 32 or len(community_name) == 0:
                module.fail_json(
                    msg='Error: The len of community_name %s is out of [1 - 32].' % community_name)

            if acl_number:
                if acl_number.isdigit():
                    if int(acl_number) > 2999 or int(acl_number) < 2000:
                        module.fail_json(
                            msg='Error: The value of acl_number %s is out of [2000 - 2999].' % acl_number)
                else:
                    if not acl_number[0].isalpha() or len(acl_number) > 32 or len(acl_number) < 1:
                        module.fail_json(
                            msg='Error: The len of acl_number %s is out of [1 - 32] or is invalid.' % acl_number)

            if community_mib_view:
                if len(community_mib_view) > 32 or len(community_mib_view) == 0:
                    module.fail_json(
                        msg='Error: The len of community_mib_view %s is out of [1 - 32].' % community_mib_view)

            conf_str = CE_GET_SNMP_COMMUNITY_HEADER
            if acl_number:
                conf_str += "<aclNumber></aclNumber>"
            if community_mib_view:
                conf_str += "<mibViewName></mibViewName>"

            conf_str += CE_GET_SNMP_COMMUNITY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                if state == "present":
                    need_cfg = True
            else:
                xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                    replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                    replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

                root = ElementTree.fromstring(xml_str)
                community_info = root.findall("data/snmp/communitys/community")
                if community_info:
                    for tmp in community_info:
                        tmp_dict = dict()
                        for site in tmp:
                            if site.tag in ["communityName", "accessRight", "aclNumber", "mibViewName"]:
                                tmp_dict[site.tag] = site.text

                        result["community_info"].append(tmp_dict)

                if result["community_info"]:
                    for tmp in result["community_info"]:
                        if "communityName" in tmp.keys():
                            need_cfg = True

                        if "accessRight" in tmp.keys():
                            if state == "present":
                                if tmp["accessRight"] != access_right:
                                    need_cfg = True
                            else:
                                if tmp["accessRight"] == access_right:
                                    need_cfg = True

                        if acl_number:
                            if "aclNumber" in tmp.keys():
                                if state == "present":
                                    if tmp["aclNumber"] != acl_number:
                                        need_cfg = True
                                else:
                                    if tmp["aclNumber"] == acl_number:
                                        need_cfg = True

                        if community_mib_view:
                            if "mibViewName" in tmp.keys():
                                if state == "present":
                                    if tmp["mibViewName"] != community_mib_view:
                                        need_cfg = True
                                else:
                                    if tmp["mibViewName"] == community_mib_view:
                                        need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_snmp_v3_group_args(self, **kwargs):
        """ Check snmp v3 group args """

        module = kwargs["module"]
        result = dict()
        need_cfg = False
        result["group_info"] = []
        state = module.params['state']
        group_name = module.params['group_name']
        security_level = module.params['security_level']
        acl_number = module.params['acl_number']
        read_view = module.params['read_view']
        write_view = module.params['write_view']
        notify_view = module.params['notify_view']

        community_name = module.params['community_name']
        access_right = module.params['access_right']

        if group_name and security_level:

            if community_name and access_right:
                module.fail_json(
                    msg='Error: Community is used for v1/v2c, group_name is used for v3, do not '
                        'input at the same time.')

            if len(group_name) > 32 or len(group_name) == 0:
                module.fail_json(
                    msg='Error: The len of group_name %s is out of [1 - 32].' % group_name)

            if acl_number:
                if acl_number.isdigit():
                    if int(acl_number) > 2999 or int(acl_number) < 2000:
                        module.fail_json(
                            msg='Error: The value of acl_number %s is out of [2000 - 2999].' % acl_number)
                else:
                    if not acl_number[0].isalpha() or len(acl_number) > 32 or len(acl_number) < 1:
                        module.fail_json(
                            msg='Error: The len of acl_number %s is out of [1 - 32] or is invalid.' % acl_number)

            if read_view:
                if len(read_view) > 32 or len(read_view) < 1:
                    module.fail_json(
                        msg='Error: The len of read_view %s is out of [1 - 32].' % read_view)

            if write_view:
                if len(write_view) > 32 or len(write_view) < 1:
                    module.fail_json(
                        msg='Error: The len of write_view %s is out of [1 - 32].' % write_view)

            if notify_view:
                if len(notify_view) > 32 or len(notify_view) < 1:
                    module.fail_json(
                        msg='Error: The len of notify_view %s is out of [1 - 32].' % notify_view)

            conf_str = CE_GET_SNMP_V3_GROUP_HEADER
            if acl_number:
                conf_str += "<aclNumber></aclNumber>"
            if read_view:
                conf_str += "<readViewName></readViewName>"
            if write_view:
                conf_str += "<writeViewName></writeViewName>"
            if notify_view:
                conf_str += "<notifyViewName></notifyViewName>"

            conf_str += CE_GET_SNMP_V3_GROUP_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                if state == "present":
                    need_cfg = True
            else:
                xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                    replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                    replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

                root = ElementTree.fromstring(xml_str)
                group_info = root.findall("data/snmp/snmpv3Groups/snmpv3Group")
                if group_info:
                    for tmp in group_info:
                        tmp_dict = dict()
                        for site in tmp:
                            if site.tag in ["groupName", "securityLevel", "readViewName", "writeViewName",
                                            "notifyViewName", "aclNumber"]:
                                tmp_dict[site.tag] = site.text

                        result["group_info"].append(tmp_dict)

                if result["group_info"]:
                    for tmp in result["group_info"]:
                        if "groupName" in tmp.keys():
                            if state == "present":
                                if tmp["groupName"] != group_name:
                                    need_cfg = True
                            else:
                                if tmp["groupName"] == group_name:
                                    need_cfg = True

                        if "securityLevel" in tmp.keys():
                            if state == "present":
                                if tmp["securityLevel"] != security_level:
                                    need_cfg = True
                            else:
                                if tmp["securityLevel"] == security_level:
                                    need_cfg = True

                        if acl_number:
                            if "aclNumber" in tmp.keys():
                                if state == "present":
                                    if tmp["aclNumber"] != acl_number:
                                        need_cfg = True
                                else:
                                    if tmp["aclNumber"] == acl_number:
                                        need_cfg = True

                        if read_view:
                            if "readViewName" in tmp.keys():
                                if state == "present":
                                    if tmp["readViewName"] != read_view:
                                        need_cfg = True
                                else:
                                    if tmp["readViewName"] == read_view:
                                        need_cfg = True

                        if write_view:
                            if "writeViewName" in tmp.keys():
                                if state == "present":
                                    if tmp["writeViewName"] != write_view:
                                        need_cfg = True
                                else:
                                    if tmp["writeViewName"] == write_view:
                                        need_cfg = True

                        if notify_view:
                            if "notifyViewName" in tmp.keys():
                                if state == "present":
                                    if tmp["notifyViewName"] != notify_view:
                                        need_cfg = True
                                else:
                                    if tmp["notifyViewName"] == notify_view:
                                        need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def merge_snmp_community(self, **kwargs):
        """ Merge snmp community operation """

        module = kwargs["module"]
        community_name = module.params['community_name']
        access_right = module.params['access_right']
        acl_number = module.params['acl_number']
        community_mib_view = module.params['community_mib_view']

        conf_str = CE_MERGE_SNMP_COMMUNITY_HEADER % (
            community_name, access_right)
        if acl_number:
            conf_str += "<aclNumber>%s</aclNumber>" % acl_number
        if community_mib_view:
            conf_str += "<mibViewName>%s</mibViewName>" % community_mib_view

        conf_str += CE_MERGE_SNMP_COMMUNITY_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge snmp community failed.')

        community_safe_name = "******"

        cmd = "snmp-agent community %s %s" % (access_right, community_safe_name)

        if acl_number:
            cmd += " acl %s" % acl_number
        if community_mib_view:
            cmd += " mib-view %s" % community_mib_view

        return cmd

    def create_snmp_community(self, **kwargs):
        """ Create snmp community operation """

        module = kwargs["module"]
        community_name = module.params['community_name']
        access_right = module.params['access_right']
        acl_number = module.params['acl_number']
        community_mib_view = module.params['community_mib_view']

        conf_str = CE_CREATE_SNMP_COMMUNITY_HEADER % (
            community_name, access_right)
        if acl_number:
            conf_str += "<aclNumber>%s</aclNumber>" % acl_number
        if community_mib_view:
            conf_str += "<mibViewName>%s</mibViewName>" % community_mib_view

        conf_str += CE_CREATE_SNMP_COMMUNITY_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Create snmp community failed.')

        community_safe_name = "******"

        cmd = "snmp-agent community %s %s" % (access_right, community_safe_name)

        if acl_number:
            cmd += " acl %s" % acl_number
        if community_mib_view:
            cmd += " mib-view %s" % community_mib_view

        return cmd

    def delete_snmp_community(self, **kwargs):
        """ Delete snmp community operation """

        module = kwargs["module"]
        community_name = module.params['community_name']
        access_right = module.params['access_right']
        acl_number = module.params['acl_number']
        community_mib_view = module.params['community_mib_view']

        conf_str = CE_DELETE_SNMP_COMMUNITY_HEADER % (
            community_name, access_right)
        if acl_number:
            conf_str += "<aclNumber>%s</aclNumber>" % acl_number
        if community_mib_view:
            conf_str += "<mibViewName>%s</mibViewName>" % community_mib_view

        conf_str += CE_DELETE_SNMP_COMMUNITY_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Create snmp community failed.')

        community_safe_name = "******"
        cmd = "undo snmp-agent community %s %s" % (
            access_right, community_safe_name)

        return cmd

    def merge_snmp_v3_group(self, **kwargs):
        """ Merge snmp v3 group operation """

        module = kwargs["module"]
        group_name = module.params['group_name']
        security_level = module.params['security_level']
        acl_number = module.params['acl_number']
        read_view = module.params['read_view']
        write_view = module.params['write_view']
        notify_view = module.params['notify_view']

        conf_str = CE_MERGE_SNMP_V3_GROUP_HEADER % (group_name, security_level)
        if acl_number:
            conf_str += "<aclNumber>%s</aclNumber>" % acl_number
        if read_view:
            conf_str += "<readViewName>%s</readViewName>" % read_view
        if write_view:
            conf_str += "<writeViewName>%s</writeViewName>" % write_view
        if notify_view:
            conf_str += "<notifyViewName>%s</notifyViewName>" % notify_view
        conf_str += CE_MERGE_SNMP_V3_GROUP_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge snmp v3 group failed.')

        if security_level == "noAuthNoPriv":
            security_level_cli = "noauthentication"
        elif security_level == "authentication":
            security_level_cli = "authentication"
        elif security_level == "privacy":
            security_level_cli = "privacy"

        cmd = "snmp-agent group v3 %s %s" % (group_name, security_level_cli)

        if read_view:
            cmd += " read-view %s" % read_view
        if write_view:
            cmd += " write-view %s" % write_view
        if notify_view:
            cmd += " notify-view %s" % notify_view
        if acl_number:
            cmd += " acl %s" % acl_number

        return cmd

    def create_snmp_v3_group(self, **kwargs):
        """ Create snmp v3 group operation """

        module = kwargs["module"]
        group_name = module.params['group_name']
        security_level = module.params['security_level']
        acl_number = module.params['acl_number']
        read_view = module.params['read_view']
        write_view = module.params['write_view']
        notify_view = module.params['notify_view']

        conf_str = CE_CREATE_SNMP_V3_GROUP_HEADER % (
            group_name, security_level)
        if acl_number:
            conf_str += "<aclNumber>%s</aclNumber>" % acl_number
        if read_view:
            conf_str += "<readViewName>%s</readViewName>" % read_view
        if write_view:
            conf_str += "<writeViewName>%s</writeViewName>" % write_view
        if notify_view:
            conf_str += "<notifyViewName>%s</notifyViewName>" % notify_view
        conf_str += CE_CREATE_SNMP_V3_GROUP_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Create snmp v3 group failed.')

        if security_level == "noAuthNoPriv":
            security_level_cli = "noauthentication"
        elif security_level == "authentication":
            security_level_cli = "authentication"
        elif security_level == "privacy":
            security_level_cli = "privacy"

        cmd = "snmp-agent group v3 %s %s" % (group_name, security_level_cli)

        if read_view:
            cmd += " read-view %s" % read_view
        if write_view:
            cmd += " write-view %s" % write_view
        if notify_view:
            cmd += " notify-view %s" % notify_view
        if acl_number:
            cmd += " acl %s" % acl_number

        return cmd

    def delete_snmp_v3_group(self, **kwargs):
        """ Delete snmp v3 group operation """

        module = kwargs["module"]
        group_name = module.params['group_name']
        security_level = module.params['security_level']
        acl_number = module.params['acl_number']
        read_view = module.params['read_view']
        write_view = module.params['write_view']
        notify_view = module.params['notify_view']

        conf_str = CE_DELETE_SNMP_V3_GROUP_HEADER % (
            group_name, security_level)
        if acl_number:
            conf_str += "<aclNumber>%s</aclNumber>" % acl_number
        if read_view:
            conf_str += "<readViewName>%s</readViewName>" % read_view
        if write_view:
            conf_str += "<writeViewName>%s</writeViewName>" % write_view
        if notify_view:
            conf_str += "<notifyViewName>%s</notifyViewName>" % notify_view
        conf_str += CE_DELETE_SNMP_V3_GROUP_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Delete snmp v3 group failed.')

        if security_level == "noAuthNoPriv":
            security_level_cli = "noauthentication"
        elif security_level == "authentication":
            security_level_cli = "authentication"
        elif security_level == "privacy":
            security_level_cli = "privacy"

        cmd = "undo snmp-agent group v3 %s %s" % (
            group_name, security_level_cli)

        return cmd


def main():
    """ main function """

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        acl_number=dict(type='str'),
        community_name=dict(type='str', no_log=True),
        access_right=dict(choices=['read', 'write']),
        community_mib_view=dict(type='str'),
        group_name=dict(type='str'),
        security_level=dict(
            choices=['noAuthNoPriv', 'authentication', 'privacy']),
        read_view=dict(type='str'),
        write_view=dict(type='str'),
        notify_view=dict(type='str')
    )

    argument_spec.update(ce_argument_spec)
    required_together = [("community_name", "access_right"), ("security_level", "group_name")]
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=required_together,
        supports_check_mode=True
    )

    changed = False
    proposed = dict()
    existing = dict()
    end_state = dict()
    updates = []

    state = module.params['state']
    acl_number = module.params['acl_number']
    community_name = module.params['community_name']
    community_mib_view = module.params['community_mib_view']
    access_right = module.params['access_right']
    group_name = module.params['group_name']
    security_level = module.params['security_level']
    read_view = module.params['read_view']
    write_view = module.params['write_view']
    notify_view = module.params['notify_view']

    snmp_community_obj = SnmpCommunity()

    if not snmp_community_obj:
        module.fail_json(msg='Error: Init module failed.')

    snmp_community_rst = snmp_community_obj.check_snmp_community_args(
        module=module)
    snmp_v3_group_rst = snmp_community_obj.check_snmp_v3_group_args(
        module=module)

    # get proposed
    proposed["state"] = state
    if acl_number:
        proposed["acl_number"] = acl_number
    if community_name:
        proposed["community_name"] = community_name
    if community_mib_view:
        proposed["community_mib_view"] = community_mib_view
    if access_right:
        proposed["access_right"] = access_right
    if group_name:
        proposed["group_name"] = group_name
    if security_level:
        proposed["security_level"] = security_level
    if read_view:
        proposed["read_view"] = read_view
    if write_view:
        proposed["write_view"] = write_view
    if notify_view:
        proposed["notify_view"] = notify_view

    # state exist snmp community config
    exist_tmp = dict()
    for item in snmp_community_rst:
        if item != "need_cfg":
            exist_tmp[item] = snmp_community_rst[item]

    if exist_tmp:
        existing["snmp community"] = exist_tmp
    # state exist snmp v3 group config
    exist_tmp = dict()
    for item in snmp_v3_group_rst:
        if item != "need_cfg":
            exist_tmp[item] = snmp_v3_group_rst[item]

    if exist_tmp:
        existing["snmp v3 group"] = exist_tmp

    if state == "present":
        if snmp_community_rst["need_cfg"]:
            if len(snmp_community_rst["community_info"]) != 0:
                cmd = snmp_community_obj.merge_snmp_community(module=module)
                changed = True
                updates.append(cmd)
            else:
                cmd = snmp_community_obj.create_snmp_community(module=module)
                changed = True
                updates.append(cmd)

        if snmp_v3_group_rst["need_cfg"]:
            if len(snmp_v3_group_rst["group_info"]):
                cmd = snmp_community_obj.merge_snmp_v3_group(module=module)
                changed = True
                updates.append(cmd)
            else:
                cmd = snmp_community_obj.create_snmp_v3_group(module=module)
                changed = True
                updates.append(cmd)

    else:
        if snmp_community_rst["need_cfg"]:
            cmd = snmp_community_obj.delete_snmp_community(module=module)
            changed = True
            updates.append(cmd)
        if snmp_v3_group_rst["need_cfg"]:
            cmd = snmp_community_obj.delete_snmp_v3_group(module=module)
            changed = True
            updates.append(cmd)

    # state end snmp community config
    snmp_community_rst = snmp_community_obj.check_snmp_community_args(
        module=module)
    end_tmp = dict()
    for item in snmp_community_rst:
        if item != "need_cfg":
            exist_tmp[item] = snmp_community_rst[item]
    if end_tmp:
        end_state["snmp community"] = end_tmp
    # state exist snmp v3 group config
    snmp_v3_group_rst = snmp_community_obj.check_snmp_v3_group_args(
        module=module)
    end_tmp = dict()
    for item in snmp_v3_group_rst:
        if item != "need_cfg":
            exist_tmp[item] = snmp_v3_group_rst[item]
    if end_tmp:
        end_state["snmp v3 group"] = end_tmp

    results = dict()
    results['proposed'] = proposed
    results['existing'] = existing
    results['changed'] = changed
    results['end_state'] = end_state
    results['updates'] = updates

    module.exit_json(**results)


if __name__ == '__main__':
    main()
