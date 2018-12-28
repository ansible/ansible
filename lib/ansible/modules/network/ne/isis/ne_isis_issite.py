# -*- coding: utf-8 -*-
# !/usr/bin/python
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
module: ne_isis_issite
version_added: "2.6"
short_description: Manages configuration of an ISIS instance on HUAWEI netengine switches.
description:
    - Manages configuration of an ISIS instance on HUAWEI netengine switches.
author: Xuenjian (@netengine-Ansible)
options:
    instanceid:
        description:
            - Set the process ID. If the process ID does not exist, you can create a process. Otherwise, the system fails to create a process.
              The value is an integer ranging from 1 to 4294967295.
        required: true
'''

EXAMPLES = '''
- name: isis module test
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      transport: cli

  tasks:
  - name: Configure isis
    ne_isis_issite:
      instanceid: 1
      description: ISIS
      vpnname:__public__
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"instanceid": "1", "description": "ISIS", "vpnname":__public__}
proposed:
    description: k/v pairs of proposed configuration
    returned: verbose mode
    type: dict
    sample: {"instanceid": "1", "description": "ISIS", "vpnname":__public__}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"instanceid": "1",
             "description": "ISIS"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["isis 1", "description ISIS"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

# import pydevd

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

# ISIS 模块私有宏定义
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_GET_ISISCOMM_HEAD
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_GET_ISISCOMM_TAIL
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_PROCESS_ISIS_HEAD
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_PROCESS_ISIS_TAIL

# ISIS 模块私有接口公共函数
from ansible.modules.network.ne.isis.ne_isis_def import constr_leaf_value
from ansible.modules.network.ne.isis.ne_isis_def import constr_leaf_novalue
from ansible.modules.network.ne.isis.ne_isis_def import constr_container_head
from ansible.modules.network.ne.isis.ne_isis_def import constr_container_tail
from ansible.modules.network.ne.isis.ne_isis_def import constr_container_process_head
from ansible.modules.network.ne.isis.ne_isis_def import constr_container_process_tail


class ISIS(object):
    """Manages configuration of an ISIS instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.instanceid = self.module.params['instanceid']
        self.vpnname = self.module.params['vpnname']
        self.description = self.module.params['description']
        self.islevel = self.module.params['islevel']
        self.coststyle = self.module.params['coststyle']
        self.localsymbolicname = self.module.params['localsymbolicname']
        self.spfmaxinterval = self.module.params['spfmaxinterval']
        self.spfinitinterval = self.module.params['spfinitinterval']
        self.spfincrinterval = self.module.params['spfincrinterval']
        self.lspmaxage = self.module.params['lspmaxage']
        self.lsprefreshinterval = self.module.params['lsprefreshinterval']

        self.state = self.module.params['state']
        # isis info
        self.isis_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """ init module """
        required_one_of = [["instanceid", "vpnname", "description"]]
        # mutually_exclusive=mutually_exclusive,
        required_together = [("spfmaxinterval", "spfinitinterval", "spfincrinterval")]

        self.module = AnsibleModule(
            argument_spec=self.spec,
            required_one_of=required_one_of,
            required_together=required_together,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        # 不检查参数， 有lua脚本侧返回统一错误信息
        # check instanceid
        # if self.instanceid:
        #    if not self.instanceid.isdigit():
        #        self.module.fail_json(
        #            msg='Error: Instance Id is not digit.')
        #    if int(self.instanceid) <= 1 or int(self.instanceid) > 4294967295:
        #        self.module.fail_json(
        #            msg='Error: Instance Id is not in the range from 1 to 4294967295.')
        #
        # check isis description 1~80
        # if self.description:
        #    if len(self.description) > 80 or len(self.description.replace(' ', '')) < 1:
        #        self.module.fail_json(
        #            msg='Error: Isis instance description is not in the range from 1 to 80.')
        #
        # check vpnname
        # if self.vpnname:
        #    if len(self.vpnname) > 31 or len(self.vpnname.replace(' ', '')) < 1:
        #        self.module.fail_json(
        #            msg='Error: VpnInstance name  is not in the range from 1 to 31.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_isis_dict(self):
        """ get one isis attributes dict."""

        isis_info = dict()
        # Head info
        conf_str = NE_COMMON_XML_GET_ISISCOMM_HEAD

        # Body info
        conf_str = constr_leaf_value(conf_str, "instanceId", self.instanceid)
        conf_str = constr_leaf_novalue(conf_str, "vpnName")
        conf_str = constr_leaf_novalue(conf_str, "isLevel")
        conf_str = constr_leaf_novalue(conf_str, "costStyle")
        conf_str = constr_leaf_novalue(conf_str, "localSymbolicName")
        conf_str = constr_leaf_novalue(conf_str, "spfMaxInterval")
        conf_str = constr_leaf_novalue(conf_str, "spfInitInterval")
        conf_str = constr_leaf_novalue(conf_str, "spfIncrInterval")
        conf_str = constr_leaf_novalue(conf_str, "lspMaxAge")
        conf_str = constr_leaf_novalue(conf_str, "lspRefreshInterval")
        conf_str = constr_leaf_novalue(conf_str, "description")
        # Tail info
        conf_str += NE_COMMON_XML_GET_ISISCOMM_TAIL
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return isis_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-isiscomm"', "")

        # get process base info
        # 另外一种获取数据处理的方式，暂不修改
        # re_find = re.findall(
        #    r'.*<instanceId>(.*)</instanceId>.*', xml_str)

        root = ElementTree.fromstring(xml_str)
        iSsite = root.find("isiscomm/isSites/isSite")
        # if iSsite is not None:
        if len(iSsite) != 0:
            for site in iSsite:
                if site.tag in ["instanceId",
                                "vpnName",
                                "isLevel",
                                "costStyle",
                                "localSymbolicName",
                                "spfMaxInterval",
                                "spfInitInterval",
                                "spfIncrInterval",
                                "lspMaxAge",
                                "lspRefreshInterval",
                                "description"]:
                    isis_info[site.tag.lower()] = site.text

        return isis_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["instanceid"] = self.instanceid
        self.proposed["state"] = self.state

        if self.description is not None:
            self.proposed["description"] = self.description
        if self.vpnname is not None:
            self.proposed["vpnname"] = self.vpnname
        if self.islevel is not None:
            self.proposed["islevel"] = self.islevel
        if self.coststyle is not None:
            self.proposed["coststyle"] = self.coststyle
        if self.localsymbolicname is not None:
            self.proposed["localsymbolicname"] = self.localsymbolicname
        if self.spfmaxinterval is not None:
            self.proposed["spfmaxinterval"] = self.spfmaxinterval
        if self.spfinitinterval is not None:
            self.proposed["spfinitinterval"] = self.spfinitinterval
        if self.spfincrinterval is not None:
            self.proposed["spfincrinterval"] = self.spfincrinterval
        if self.lspmaxage is not None:
            self.proposed["lspmaxage"] = self.lspmaxage
        if self.lsprefreshinterval is not None:
            self.proposed["lsprefreshinterval"] = self.lsprefreshinterval

    def get_existing(self):
        """get existing info"""
        if not self.isis_info:
            return

        self.existing["instanceid"] = self.instanceid
        try:
            self.existing["description"] = self.isis_info["description"]
        except BaseException:
            pass

        self.existing["vpnname"] = self.isis_info["vpnname"]
        self.existing["islevel"] = self.isis_info["islevel"]
        self.existing["coststyle"] = self.isis_info["coststyle"]

        try:
            self.existing["localsymbolicname"] = self.isis_info["localsymbolicname"]
        except BaseException:
            pass

        self.existing["spfmaxinterval"] = self.isis_info["spfmaxinterval"]
        self.existing["spfinitinterval"] = self.isis_info["spfinitinterval"]
        self.existing["spfincrinterval"] = self.isis_info["spfincrinterval"]
        self.existing["lspmaxage"] = self.isis_info["lspmaxage"]
        self.existing["lsprefreshinterval"] = self.isis_info["lsprefreshinterval"]

    def get_end_state(self):
        """get end state info"""

        isis_info = self.get_isis_dict()
        if not isis_info:
            return

        self.end_state["instanceid"] = self.instanceid
        try:
            self.end_state["description"] = isis_info["description"]
        except BaseException:
            pass

        try:
            self.end_state["vpnname"] = isis_info["vpnname"]
        except BaseException:
            pass

        self.end_state["islevel"] = isis_info["islevel"]
        self.end_state["coststyle"] = isis_info["coststyle"]
        try:
            self.end_state["localsymbolicname"] = isis_info["localsymbolicname"]
        except BaseException:
            pass

        self.end_state["spfmaxinterval"] = isis_info["spfmaxinterval"]
        self.end_state["spfinitinterval"] = isis_info["spfinitinterval"]
        self.end_state["spfincrinterval"] = isis_info["spfincrinterval"]
        self.end_state["lspmaxage"] = isis_info["lspmaxage"]
        self.end_state["lsprefreshinterval"] = isis_info["lsprefreshinterval"]

    def common_process(self, operationType, operationDesc):
        """Common  isis process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % operationType
        # Body process
        xml_str = constr_leaf_value(xml_str, "instanceId", self.instanceid)
        xml_str = constr_leaf_value(xml_str, "vpnName", self.vpnname)
        xml_str = constr_leaf_value(xml_str, "description", self.description)
        xml_str = constr_leaf_value(xml_str, "isLevel", self.islevel)
        xml_str = constr_leaf_value(xml_str, "costStyle", self.coststyle)
        xml_str = constr_leaf_value(xml_str, "localSymbolicName", self.localsymbolicname)
        xml_str = constr_leaf_value(xml_str, "spfMaxInterval", self.spfmaxinterval)
        xml_str = constr_leaf_value(xml_str, "spfInitInterval", self.spfinitinterval)
        xml_str = constr_leaf_value(xml_str, "spfIncrInterval", self.spfincrinterval)
        xml_str = constr_leaf_value(xml_str, "lspMaxAge", self.lspmaxage)
        xml_str = constr_leaf_value(xml_str, "lspRefreshInterval", self.lsprefreshinterval)
        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_ISIS_TAIL
        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

        # 命令行更新待补充其他
        # if self.vpnname:
        #    self.updates_cmd.append("isis %s %s" % (self.instanceid, self.vpnname))
        # else:
        #    self.updates_cmd.append("isis %s " % self.instanceid)
        #
        # if self.description:
        #    self.updates_cmd.append("description %s " % self.description)

    def create_process(self):
        """Create isis process"""

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge isis process"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete isis  process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % NE_COMMON_XML_OPERATION_DELETE
        # Body process
        xml_str = constr_leaf_value(xml_str, "instanceId", self.instanceid)
        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_ISIS_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")

        self.updates_cmd.append("undo isis %s" % self.instanceid)
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        self.isis_info = self.get_isis_dict()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            if not self.isis_info:
                # create isis process
                self.create_process()
            else:
                # merge isis process
                self.merge_process()
        elif self.state == "absent":
            if self.isis_info:
                # remove isis process
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: Isis instance does not exist')
        elif self.state == "query":
            # 查询输出
            if not self.isis_info:
                self.module.fail_json(msg='Error: Isis instance does not exist')

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        self.get_end_state()

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """Module main"""

    argument_spec = dict(
        instanceid=dict(required=True, type='str'),
        vpnname=dict(required=False, type='str'),
        description=dict(required=False, type='str'),

        # 在此增加其他支持参数 , default 不能设置, 设置的话导致,命令不带参数时,
        # 赋值处理,导致业务逻辑不可控。
        # /isiscomm/isSites/isSite/isLevel            CLI : is-level level-<ISISLEVEL>
        islevel=dict(required=False, choices=['level_1', 'level_2', 'level_1_2']),

        # /isiscomm/isSites/isSite/costStyle          CLI : cost-style wide
        coststyle=dict(required=False, choices=['narrow', 'wide', 'transition', 'ntransition', 'wtransition']),

        # /isiscomm/isSites/isSite/localSymbolicName  CLI : is-name <hostname>
        localsymbolicname=dict(required=False, type='str'),

        # /isiscomm/isSites/isSite/spfMaxInterval        CLI : timer spf 1 50 50
        spfmaxinterval=dict(required=False, type='int'),

        # /isiscomm/isSites/isSite/spfInitInterval       CLI : timer spf 1 50 50
        spfinitinterval=dict(required=False, type='int'),

        # /isiscomm/isSites/isSite/spfIncrInterval　　   CLI : timer spf 1 50 50
        spfincrinterval=dict(required=False, type='int'),

        # /isiscomm/isSites/isSite/lspMaxAge             CLI: timer lsp-max-age 65535
        lspmaxage=dict(required=False, type='int'),

        # /isiscomm/isSites/isSite/lspRefreshInterval    CLI: timer lsp-refresh 32767
        lsprefreshinterval=dict(required=False, type='int'),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = ISIS(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
