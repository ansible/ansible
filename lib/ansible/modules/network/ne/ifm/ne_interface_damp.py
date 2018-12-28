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
module: ne_interface_damp
version_added: "2.6"
short_description: Manages interface status suppression configuration.
description:
    - Manages status suppression configuration of an interface on HUAWEI netengine routers.
author: Shijiawei (@netengine-Ansible)
options:
    name:
        description:
            - The textual name of the interface. The value of this object should be the name of the
              interface as assigned by the local device and should be suitable for use in commands
              entered at the device's `console'. This might be a text name, depending on the interface
              naming syntax of the device. The value is a string of 1 to 63 characters.
        required: true
        default: null
    control_flap_enable:
        description:
            - Enable the control flap function on an interface.
        required: true
        default: null
        choices: ['true', 'false']
    control_flap_suppress:
        description:
            - Suppression threshold on an interface. The value is an integer ranging from 1 to 20000.
              The value must be greater than the reusing threshold and smaller than the suppression
              upper limit. The interface will be depressed, when penalty value is bigger than suppress value.
        required: true
        default: null
    control_flap_reuse:
        description:
            - Reusing threshold of an interface. The value is an integer ranging from 1 to 20000.
              The value must be smaller than the suppression threshold. The depressed status of
              interface will be released, when the penalty value is equal or smaller than the reuse value.
        required: true
        default: null
    control_flap_ceiling:
        description:
            - Maximum suppression value on an interface. The value is an integer ranging from 1001 to 20000.
              The value should be greater than the Damping Suppression Threshold. The penalty value will
              not increase any more, when reaching The ceiling value.
        required: true
        default: null
    control_flap_decay_ok:
        description:
            - The penalty value of an Up interface attenuates to 1/2. The value is an integer ranging
              from 1 to 900. The value is expressed in seconds. The half-life period of Interface,
              whose status is up.
        required: true
        default: null
    control_flap_decay_ng:
        description:
            - The penalty value of a Down interface attenuates to 1/2. The value is an integer ranging
              from 1 to 900. The value is expressed in seconds. The half-life period of Interface,
              whose status is down.
        required: true
        default: null
    damp_ignore_global:
        description:
            - Ignore global damp function.
        required: true
        default: null
        choices: ['true', 'false']
    damp_enable:
        description:
            - Interface physical status damping enable.
        required: true
        default: null
        choices: ['true', 'false']
    damp_tx_off:
        description:
            - Shutdown transmission when damping suppressed.
        required: true
        default: null
        choices: ['true', 'false']
    damp_level:
        description:
            - Interface physical status damping level.
              light: Light weight.
              middle: Middle weight.
              heavy: Heavy weight.
              manual: Manually configure the parameters.
        required: true
        default: null
        choices: ['light', 'middle', 'heavy', 'manual']
    damp_suppress:
        description:
            -  1000 times of suppress threshold. The value is an integer ranging from 1 to 20000.
        required: true
        default: null
    damp_reuse:
        description:
            - 1000 times of reuse threshold. The value is an integer ranging from 1 to 20000.
        required: true
        default: null
    damp_max_suppress_time:
        description:
            - Max suppress time(seconds). The value is an integer ranging from 1 to 255.
        required: true
        default: null
    damp_half_life_period:
        description:
            - Half life time(seconds). The value is an integer ranging from 1 to 60.
        required: true
        default: null
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present', 'absent', 'query']
'''

EXAMPLES = '''
- name: interface_damp module test
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
  - name: Config interface control-flap
    ne_interface_damp:
      name: GigabitEthernet2/0/0
      control_flap_enable: true
      control_flap_suppress: 2000
      control_flap_reuse: 1000
      control_flap_ceiling: 3000
      control_flap_decay_ok: 1
      control_flap_decay_ng: 1
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"name": "GigabitEthernet2/0/0",
             "control_flap_enable": "true",
             "control_flap_suppress": "2000",
             "control_flap_reuse": "2000",
             "control_flap_ceiling": "3000",
             "control_flap_decay_ok": "1",
             "control_flap_decay_ng": "1"
             "state": "present"}
existing:
    description: k/v pairs of existing interface
    returned: always
    type: dict
    sample: {"control_flap_enable": "false",
             "damp_enable": "false",
             "damp_ignore_global": "false",
             "name": "GigabitEthernet2/0/0"}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"control_flap_ceiling": "3000",
             "control_flap_decay_ng": "1",
             "control_flap_decay_ok": "1",
             "control_flap_enable": "true",
             "control_flap_reuse": "1000",
             "control_flap_suppress": "2000",
             "damp_enable": "false",
             "damp_ignore_global": "false",
             "name": "GigabitEthernet2/0/0"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface GigabitEthernet2/0/0", "control-flap 2000 1000 3000 1 1"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import logging

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
# Interface 模块私有宏定义
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_OPTYPE_MERGE
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_GET_IFM_HEAD
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_GET_IFM_TAIL
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_SET_IFM_HEAD
from ansible.modules.network.ne.ifm.ne_interface_def import NE_NC_SET_IFM_TAIL

# Interface 模块私有接口公共函数
from ansible.modules.network.ne.ifm.ne_interface_def import constr_leaf_value
from ansible.modules.network.ne.ifm.ne_interface_def import constr_container_head
from ansible.modules.network.ne.ifm.ne_interface_def import constr_container_tail
from ansible.modules.network.ne.ifm.ne_interface_def import constr_leaf_process_delete
from ansible.modules.network.ne.ifm.ne_interface_def import constr_container_novalue

logging.basicConfig(filename='/opt/python_logger.log', level=logging.INFO)

INTERFACE_XML2CLI = {'ifName': 'name'}

CONTROLFLAP_XML2CLI = {'ifCtrlFlapEnbl': 'control_flap_enable',
                       'ifSuppress': 'control_flap_suppress',
                       'ifReuse': 'control_flap_reuse',
                       'ifCeiling': 'control_flap_ceiling',
                       'ifDecayOk': 'control_flap_decay_ok',
                       'ifDecayNg': 'control_flap_decay_ng'}

DAMP_XML2CLI = {'dampIgnoreGlobal': 'damp_ignore_global',
                'ifDampEnable': 'damp_enable',
                'ifDampTxOff': 'damp_tx_off',
                'ifDampLevel': 'damp_level',
                'ifSuppress': 'damp_suppress',
                'ifReuse': 'damp_reuse',
                'ifMaxSuppressTime': 'damp_max_suppress_time',
                'ifHalfLifePeriod': 'damp_half_life_period'}


class Interface_Damp(object):
    """Manages configuration of an interface."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.input_info = dict()
        for _, cli_key in INTERFACE_XML2CLI.items():
            self.input_info[cli_key] = self.module.params[cli_key]

        for _, cli_key in CONTROLFLAP_XML2CLI.items():
            self.input_info[cli_key] = self.module.params[cli_key]

        for _, cli_key in DAMP_XML2CLI.items():
            self.input_info[cli_key] = self.module.params[cli_key]

        self.state = self.module.params['state']
        # interface info
        self.interface_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """ init module """
        required_one_of = [["name"]]
        # mutually_exclusive=mutually_exclusive,
        required_together = []

        self.module = AnsibleModule(
            argument_spec=self.spec,
            required_one_of=required_one_of,
            required_together=required_together,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        # 其他参数待同步增加补充
        # check ifName
        if self.input_info.get("name") is not None:
            if len(self.input_info.get("name")) > 63 or len(
                    self.input_info.get("name").replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: Interface name is not in the range from 1 to 63.')

    def netconf_set_config(self, xml_str, xml_name):
        """ netconf set config """
        logging.info("netconf_set_config %s %s", xml_name, xml_str)
        recv_xml = set_nc_config(self.module, xml_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_interface_dict(self):
        """ get one interface attributes dict."""

        interface_info = dict()
        # Head info
        conf_str = NE_NC_GET_IFM_HEAD

        # Body info
        conf_str = constr_leaf_value(
            conf_str, "ifName", self.input_info.get("name"))
        conf_str = constr_container_novalue(conf_str, "ifControlFlap")
        conf_str = constr_container_novalue(conf_str, "phyDampIfCfg")

        # Tail info
        conf_str += NE_NC_GET_IFM_TAIL
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return interface_info

        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm"', "")

        root = ElementTree.fromstring(xml_str)
        interface = root.find("ifm/interfaces/interface")
        if interface is not None and len(interface) != 0:
            for field in interface:
                if field.tag in INTERFACE_XML2CLI.keys():
                    logging.info(
                        "INTERFACE_XML2CLI: %s %s",
                        field.tag,
                        field.text)
                    interface_info[INTERFACE_XML2CLI[field.tag]] = field.text

        interface_controlflap = root.find(
            "ifm/interfaces/interface/ifControlFlap")
        if interface_controlflap is not None and len(
                interface_controlflap) != 0:
            for field in interface_controlflap:
                if field.tag in CONTROLFLAP_XML2CLI.keys():
                    logging.info(
                        "CONTROLFLAP_XML2CLI: %s %s",
                        field.tag,
                        field.text)
                    interface_info[CONTROLFLAP_XML2CLI[field.tag]] = field.text

        interface_damp = root.find("ifm/interfaces/interface/phyDampIfCfg")
        if interface_damp is not None and len(interface_damp) != 0:
            for field in interface_damp:
                if field.tag in DAMP_XML2CLI.keys():
                    logging.info("DAMP_XML2CLI: %s %s", field.tag, field.text)
                    interface_info[DAMP_XML2CLI[field.tag]] = field.text

        return interface_info

    def get_proposed(self):
        """get proposed info"""
        self.proposed["state"] = self.state
        for key, value in self.input_info.items():
            if value is not None:
                self.proposed[key] = value

    def get_existing(self):
        """get existing info"""
        if not self.interface_info:
            return

        for key, value in self.interface_info.items():
            if value is not None:
                self.existing[key] = value

    def get_end_state(self):
        """get end state info"""

        interface_info = self.get_interface_dict()
        if not interface_info:
            return

        for key, value in interface_info.items():
            if value is not None:
                self.end_state[key] = value

    def is_input_controlflap(self):
        for xml_key, cli_key in CONTROLFLAP_XML2CLI.items():
            if self.input_info.get(cli_key) is not None:
                return True
        return False

    def is_input_damp(self):
        for xml_key, cli_key in DAMP_XML2CLI.items():
            if self.input_info.get(cli_key) is not None:
                return True
        return False

    def merge_process(self):
        """Common interface process"""
        # Head process
        xml_str = NE_NC_SET_IFM_HEAD % NE_NC_OPTYPE_MERGE

        # Body process
        for xml_key, cli_key in INTERFACE_XML2CLI.items():
            if self.input_info.get(cli_key) is not None:
                xml_str = constr_leaf_value(
                    xml_str, xml_key, self.input_info[cli_key])

        if self.is_input_controlflap():
            xml_str = constr_container_head(xml_str, "ifControlFlap")

            for xml_key, cli_key in CONTROLFLAP_XML2CLI.items():
                if self.input_info.get(cli_key) is not None:
                    xml_str = constr_leaf_value(
                        xml_str, xml_key, self.input_info[cli_key])

            xml_str = constr_container_tail(xml_str, "ifControlFlap")

        if self.is_input_damp():
            xml_str = constr_container_head(xml_str, "phyDampIfCfg")

            for xml_key, cli_key in DAMP_XML2CLI.items():
                if self.input_info.get(cli_key) is not None:
                    xml_str = constr_leaf_value(
                        xml_str, xml_key, self.input_info[cli_key])

            xml_str = constr_container_tail(xml_str, "phyDampIfCfg")

        # Tail process
        xml_str += NE_NC_SET_IFM_TAIL

        self.netconf_set_config(xml_str, "SET_CTRILFLAP_OR_DAMP")

        # 生成配置命令行
        changed_interface_info = self.get_interface_dict()
        self.generate_updates_cmd(self.interface_info, changed_interface_info)

    def delete_para_process(self):
        """Delete interface process"""
        # Head process
        xml_str = NE_NC_SET_IFM_HEAD % NE_NC_OPTYPE_MERGE
        # Body process
        xml_str = constr_leaf_value(
            xml_str, "ifName", self.input_info.get("name"))

        if self.is_input_controlflap():
            xml_str = constr_container_head(xml_str, "ifControlFlap")

            # 如果是清除control-flap使能，则只处理ifCtrlFlapEnbl，否则会下发报错
            if self.input_info.get("control_flap_enable") is not None:
                xml_str = constr_leaf_process_delete(xml_str, "ifCtrlFlapEnbl")
            else:
                for xml_key, cli_key in CONTROLFLAP_XML2CLI.items():
                    if self.input_info.get(cli_key) is not None:
                        xml_str = constr_leaf_process_delete(xml_str, xml_key)

            xml_str = constr_container_tail(xml_str, "ifControlFlap")

        if self.is_input_damp():
            xml_str = constr_container_head(xml_str, "phyDampIfCfg")

            # 如果是清除damp使能，则只处理damp使能和damp隔离，否则会下发报错
            if self.input_info.get("damp_enable") is not None:
                xml_str = constr_leaf_process_delete(xml_str, "ifDampEnable")
                if self.input_info.get("damp_ignore_global") is not None:
                    xml_str = constr_leaf_process_delete(
                        xml_str, "dampIgnoreGlobal")
            else:
                for xml_key, cli_key in DAMP_XML2CLI.items():
                    if self.input_info.get(cli_key) is not None:
                        xml_str = constr_leaf_process_delete(xml_str, xml_key)

            xml_str = constr_container_tail(xml_str, "phyDampIfCfg")

        # Tail process
        xml_str += NE_NC_SET_IFM_TAIL

        self.netconf_set_config(xml_str, "DELETE_CTRILFLAP_OR_DAMP")

        # 生成配置命令行
        changed_interface_info = self.get_interface_dict()
        self.generate_updates_cmd(self.interface_info, changed_interface_info)

    def generate_updates_cmd(self, interface_info, changed_interface_info):

        for key, value in self.input_info.items():
            if value is not None and changed_interface_info.get(
                    key) != interface_info.get(key):
                self.changed = True
                break

        self.updates_cmd.append(
            "interface %s" %
            changed_interface_info.get("name"))

        if self.is_input_controlflap():
            if interface_info.get("control_flap_enable") != changed_interface_info.get(
                    "control_flap_enable"):
                if "false" == changed_interface_info.get(
                        "control_flap_enable"):
                    self.updates_cmd.append("undo control-flap")
                elif "true" == changed_interface_info.get("control_flap_enable"):
                    self.updates_cmd.append("control-flap %s %s %s %s %s" %
                                            (changed_interface_info.get("control_flap_suppress"),
                                             changed_interface_info.get(
                                                 "control_flap_reuse"),
                                             changed_interface_info.get(
                                                 "control_flap_ceiling"),
                                             changed_interface_info.get(
                                                 "control_flap_decay_ok"),
                                             changed_interface_info.get("control_flap_decay_ng")))

        if self.input_info.get("damp_ignore_global") is not None and \
                interface_info.get("damp_ignore_global") != changed_interface_info.get("damp_ignore_global"):
            if "true" == changed_interface_info.get("damp_ignore_global"):
                self.updates_cmd.append("damp-interface ignore-global")
            else:
                self.updates_cmd.append("undo damp-interface ignore-global")

        if self.input_info.get("damp_enable") is not None and \
                interface_info.get("damp_enable") != changed_interface_info.get("damp_enable"):
            if "true" == changed_interface_info.get("damp_enable"):
                self.updates_cmd.append("damp-interface enable")

        if self.input_info.get("damp_tx_off") is not None and \
                interface_info.get("damp_tx_off") != changed_interface_info.get("damp_tx_off"):
            if "true" == changed_interface_info.get("damp_tx_off"):
                self.updates_cmd.append("damp-interface mode tx-off")
            else:
                self.updates_cmd.append("undo damp-interface mode tx-off")

        if self.input_info.get("damp_level") is not None or self.input_info.get("damp_suppress") is not None \
                or self.input_info.get("damp_reuse") is not None or self.input_info.get("damp_max_suppress_time") is not None \
                or self.input_info.get("damp_half_life_period") is not None:

            if interface_info.get("damp_level") != changed_interface_info.get("damp_level") \
                    or interface_info.get("damp_suppress") != changed_interface_info.get("damp_suppress") \
                    or interface_info.get("damp_reuse") != changed_interface_info.get("damp_reuse") \
                    or interface_info.get("damp_max_suppress_time") != changed_interface_info.get("damp_max_suppress_time") \
                    or interface_info.get("damp_half_life_period") != changed_interface_info.get("damp_half_life_period"):

                if self.state == "present":
                    if "manual" == changed_interface_info.get("damp_level"):
                        self.updates_cmd.append("damp-interface level %s %s %s %s %s" %
                                                (changed_interface_info.get("damp_level"),
                                                 changed_interface_info.get(
                                                     "damp_half_life_period"),
                                                 changed_interface_info.get(
                                                     "damp_suppress"),
                                                 changed_interface_info.get(
                                                     "damp_reuse"),
                                                 changed_interface_info.get("damp_max_suppress_time")))
                    else:
                        self.updates_cmd.append(
                            "damp-interface level %s" %
                            changed_interface_info.get("damp_level"))
                elif self.state == "absent":
                    self.updates_cmd.append(
                        "undo damp-interface level %s" %
                        interface_info.get("damp_level"))

        # undo damp-interface enable放在最后，保证命令行顺序
        if self.input_info.get("damp_enable") is not None and \
                interface_info.get("damp_enable") != changed_interface_info.get("damp_enable"):
            if "false" == changed_interface_info.get("damp_enable"):
                self.updates_cmd.append("undo damp-interface enable")

    def work(self):
        """worker"""
        self.check_params()

        self.interface_info = self.get_interface_dict()
        self.get_proposed()
        self.get_existing()

        if not self.interface_info:
            self.module.fail_json(
                msg='Error: Interface %s does not exist' %
                self.input_info.get("name"))

        # deal present or absent
        if self.state == "present":
            self.merge_process()
        elif self.state == "absent":
            self.delete_para_process()

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
        name=dict(required=True, type='str'),

        control_flap_enable=dict(required=False, choices=['true', 'false']),
        control_flap_suppress=dict(required=False, type='int'),
        control_flap_reuse=dict(required=False, type='int'),
        control_flap_ceiling=dict(required=False, type='int'),
        control_flap_decay_ok=dict(required=False, type='int'),
        control_flap_decay_ng=dict(required=False, type='int'),

        damp_ignore_global=dict(required=False, choices=['true', 'false']),
        damp_enable=dict(required=False, choices=['true', 'false']),
        damp_tx_off=dict(required=False, choices=['true', 'false']),
        damp_level=dict(
            required=False,
            choices=[
                'light',
                'middle',
                'heavy',
                'manual']),
        damp_suppress=dict(required=False, type='int'),
        damp_reuse=dict(required=False, type='int'),
        damp_max_suppress_time=dict(required=False, type='int'),
        damp_half_life_period=dict(required=False, type='int'),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = Interface_Damp(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
