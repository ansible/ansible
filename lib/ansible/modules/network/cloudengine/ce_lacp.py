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
module: ce_lacp
version_added: "2.4"
short_description: Manages Eth-Trunk interfaces on HUAWEI CloudEngine switches.
description:
    - Manages Eth-Trunk specific configuration parameters on HUAWEI CloudEngine switches.
author: QijunPan (@CloudEngine-Ansible)
notes:
    - C(state=absent) removes the Eth-Trunk config and interface if it
      already exists. If members to be removed are not explicitly
      passed, all existing members (if any), are removed,
      and Eth-Trunk removed.
    - Members must be a list.
options:
    trunk_id:
        description:
            - Eth-Trunk interface number.
              The value is an integer.
              The value range depends on the assign forward eth-trunk mode command.
              When 256 is specified, the value ranges from 0 to 255.
              When 512 is specified, the value ranges from 0 to 511.
              When 1024 is specified, the value ranges from 0 to 1023.
        required: true
    mode:
        description:
            - Specifies the working mode of an Eth-Trunk interface.
        required: false
        default: null
        choices: ['Manual','Dynamic','Static']
    preempt_enable:
        description:
            - Specifies lacp preempt enable of Eth-Trunk lacp.
              The value is an boolean 'true' or 'false'.
        required: false
        default: null
        choices: ['true', 'false']
    state_flapping:
        description:
            - Lacp dampening state-flapping.
        required: false
        default: null
        choices: ['true', 'false']
    port_id_extension_enable:
        description:
            - Enable the function of extending the LACP negotiation port number.
        required: false
        default: null
        choices: ['true', 'false']
    unexpected_mac_disable:
        description:
            - Lacp dampening unexpected-mac disable.
        required: false
        default: false
        choices: ['true', 'false']
    system_id:
        description:
            - Link Aggregation Control Protocol System ID,interface Eth-Trunk View.
            - Formate 'X-X-X',X is hex(a,aa,aaa, or aaaa)
        required: false
        default: false
    timeout_type:
        description:
            - Lacp timeout type,that may be 'Fast' or 'Slow'.
        required: false
        default: false
    fast_timeout:
        description:
            - When lacp timeout type is 'Fast', user-defined time can be a number(3~90).
        required: false
        default: false
    mixed_rate_link_enable:
        description:
            - Value of max active linknumber.
        required: false
        default: false
    preempt_delay:
        description:
            - Value of preemption delay time.
        required: false
        default: false
    collector_delay:
        description:
            - Value of delay time in units of 10 microseconds.
        required: false
        default: false
    max_active_linknumber:
        description:
            - Max active linknumber in link aggregation group.
        required: false
        default: false
    select:
        description:
            - Select priority or speed to preempt.
        required: false
        default: false
    member_if:
        description:
            - The member interface of eth-trunk that is selected is merge priority.
        required: false
        default: false
    priority:
        description:
            - The priority of eth-trunk member interface,and 'member_if' is need when priority is not none.
        required: false
        default: false
    global_priority:
        description:
            - Configure lacp priority on system-view.
        required: false
        default: false
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
- name: eth_trunk module test
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
  - name: Ensure Eth-Trunk100 is created, add two members, and set to mode lacp-static
    ce_eth_trunk:
      trunk_id: 100
      members: ['10GE1/0/24','10GE1/0/25']
      mode: 'lacp-static'
      state: present
      provider: '{{ cli }}'
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"trunk_id": "100", "members": ['10GE1/0/24','10GE1/0/25'], "mode": "lacp-static"}
existing:
    description: k/v pairs of existing Eth-Trunk
    returned: always
    type: dict
    sample: {"trunk_id": "100", "hash_type": "mac", "members_detail": [
            {"memberIfName": "10GE1/0/25", "memberIfState": "Down"}],
            "min_links": "1", "mode": "manual"}
end_state:
    description: k/v pairs of Eth-Trunk info after module execution
    returned: always
    type: dict
    sample: {"trunk_id": "100", "hash_type": "mac", "members_detail": [
            {"memberIfName": "10GE1/0/24", "memberIfState": "Down"},
            {"memberIfName": "10GE1/0/25", "memberIfState": "Down"}],
            "min_links": "1", "mode": "lacp-static"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface Eth-Trunk 100",
             "mode lacp-static",
             "interface 10GE1/0/25",
             "eth-trunk 100"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import xml.etree.ElementTree as ET
import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec

LACP = {'trunk_id': 'ifName',
        'mode': 'workMode',
        'preempt_enable': 'isSupportPrmpt',
        'state_flapping': 'dampStaFlapEn',
        'port_id_extension_enable': 'trunkPortIdExt',
        'unexpected_mac_disable': 'dampUnexpMacEn',
        'system_id': 'trunkSysMac',
        'timeout_type': 'rcvTimeoutType',
        'fast_timeout': 'fastTimeoutUserDefinedValue',
        'mixed_rate_link_enable': 'mixRateEnable',
        'preempt_delay': 'promptDelay',
        'collector_delay': 'collectMaxDelay',
        'max_active_linknumber': 'maxActiveNum',
        'select': 'selectPortStd',
        'member_if': 'memberIfName',
        'weight': 'weight',
        'priority': 'portPriority',
        'global_priority': 'priority'
        }


def has_element(parent, xpath):
    """
    get or create a element by xpath
    """
    ele = parent.find('./' + xpath)
    if ele is not None:
        return ele
    ele = parent
    lpath = xpath.split('/')
    for p in lpath:
        e = parent.find('.//' + p)
        if e is None:
            e = ET.SubElement(ele, p)
        ele = e
    return ele


def bulid_xml(kwargs, operation='get'):
    """
    create a xml tree by dictionary with operation,get,merge and delete
    :param kwargs: tags and values
    :param operation: get, merge, delete
    :return: a string
    """
    attrib = {'xmlns': "http://www.huawei.com/netconf/vrp",
              'content-version': "1.0", 'format-version': "1.0"}

    root = ET.Element('ifmtrunk')
    for key in kwargs.keys():
        if key in ('global_priority',):
            xpath = 'lacpSysInfo'
        elif key in ('member_if',):
            xpath = 'TrunkIfs/TrunkIf/TrunkMemberIfs/TrunkMemberIf'
        elif key in ('priority',):
            xpath = 'TrunkIfs/TrunkIf/TrunkMemberIfs/TrunkMemberIf/lacpPortInfo/lacpPort'
        elif key in ['preempt_enable', 'timeout_type', 'fast_timeout', 'select', 'preempt_delay',
                     'max_active_linknumber', 'collector_delay', 'mixed_rate_link_enable',
                     'state_flapping', 'unexpected_mac_disable', 'system_id',
                     'port_id_extension_enable']:
            xpath = 'TrunkIfs/TrunkIf/lacpTrunk'
        elif key in ('trunk_id', 'mode'):
            xpath = 'TrunkIfs/TrunkIf'
        if xpath != '':
            parent = has_element(root, xpath)
            element = ET.SubElement(parent, LACP[key])
            if operation == 'merge':
                parent.attrib = dict(operation=operation)
                element.text = str(kwargs[key])
            if key == 'member_if':
                element.text = str(kwargs[key])
            if key == 'mode':
                element.text = str(kwargs[key])
            if key == 'trunk_id':
                element.text = 'Eth-Trunk' + str(kwargs[key])
    root.attrib = attrib
    config = ET.tostring(root)
    if operation == 'merge' or operation == 'delete':
        return '<config>%s</config>' % config
    return '<filter type="subtree">%s</filter>' % config


def check_param(kwargs):
    """
    check args list
    the boolean or list values cloud not be checked,because they are limit by args list in main
    """

    for key in kwargs:
        if kwargs[key] is None:
            continue
        if key == 'trunk_id':
            value = int(kwargs[key])
            # maximal value is 1024,although the value is limit by command 'assign forward eth-trunk mode '
            if value < 0 or value > 1024:
                return 'Error: Wrong Value of Eth-Trunk interface number'
        elif key == 'system_id':
            # X-X-X ,X is hex(4 bit)
            if not re.match(r'[0-9a-f]{1,4}\-[0-9a-f]{1,4}\-[0-9a-f]{1,4}', kwargs[key], re.IGNORECASE):
                return 'Error: The system-id is invalid.'
            values = kwargs[key].split('-')
            flag = 0
            # all 'X' is 0,that is invalid value
            for v in values:
                if len(v.strip('0')) < 1:
                    flag += 1
            if flag == 3:
                return 'Error: The system-id is invalid.'
        elif key == 'timeout_type':
            # select a value from choices, choices=['Slow','Fast'],it's checked by AnsibleModule
            pass
        elif key == 'fast_timeout':
            value = int(kwargs[key])
            if value < 3 or value > 90:
                return 'Error: Wrong Value of timeout,fast user-defined value<3-90>'
            rtype = str(kwargs.get('timeout_type'))
            if rtype == 'Slow':
                return 'Error: Short timeout period for receiving packets is need,when user define the time.'
        elif key == 'preempt_delay':
            value = int(kwargs[key])
            if value < 0 or value > 180:
                return 'Error: Value of preemption delay time is from 0 to 180'
        elif key == 'collector_delay':
            value = int(kwargs[key])
            if value < 0 or value > 65535:
                return 'Error: Value of collector delay time is from 0 to 65535'
        elif key == 'max_active_linknumber':
            value = int(kwargs[key])
            if value < 0 or value > 64:
                return 'Error: Value of collector delay time is from 0 to 64'
        elif key == 'priority' or key == 'global_priority':
            value = int(kwargs[key])
            if value < 0 or value > 65535:
                return 'Error: Value of priority is from 0 to 65535'
    return 'ok'


def xml_to_dict(args):
    """
    transfer xml string into dict
    :param args: a xml string
    :return: dict
    """
    rdict = dict()
    args = re.sub(r'xmlns=\".+?\"', '', args)
    root = ET.fromstring(args)
    ifmtrunk = root.find('.//ifmtrunk')
    if ifmtrunk is not None:
        for ele in ifmtrunk.iter():
            if ele.text is not None and len(ele.text.strip()) > 0:
                rdict[ele.tag] = ele.text
    return rdict


def compare_config(module, kwarg_exist, kwarg_end):
    """
    :param kwarg_exist: existing config dictionary
    :param kwarg_end:  end config dictionary
    :return: commands update list
    """
    dic_command = {'isSupportPrmpt': 'lacp preempt enable',
                   'rcvTimeoutType': 'lacp timeout',  # lacp timeout fast user-defined 23
                   'fastTimeoutUserDefinedValue': 'lacp timeout user-defined',
                   'selectPortStd': 'lacp select',
                   'promptDelay': 'lacp preempt delay',
                   'maxActiveNum': 'lacp max active-linknumber',
                   'collectMaxDelay': 'lacp collector delay',
                   'mixRateEnable': 'lacp mixed-rate link enable',
                   'dampStaFlapEn': 'lacp dampening state-flapping',
                   'dampUnexpMacEn': 'lacp dampening unexpected-mac disable',
                   'trunkSysMac': 'lacp system-id',
                   'trunkPortIdExt': 'lacp port-id-extension enable',
                   'portPriority': 'lacp priority',  # interface 10GE1/0/1
                   'lacpMlagPriority': 'lacp m-lag priority',
                   'lacpMlagSysId': 'lacp m-lag system-id',
                   'priority': 'lacp priority'
                   }
    rlist = list()
    exist = set(kwarg_exist.keys())
    end = set(kwarg_end.keys())
    undo = exist - end
    add = end - exist
    update = end & exist

    for key in undo:
        if key in dic_command:
            rlist.append('undo ' + dic_command[key])
    for key in add:
        if key in dic_command:
            rlist.append(dic_command[key] + ' ' + kwarg_end[key])
    for key in update:
        if kwarg_exist[key] != kwarg_end[key] and key in dic_command:
            if kwarg_exist[key] == 'true' and kwarg_end[key] == 'false':
                rlist.append('undo ' + dic_command[key])
            elif kwarg_exist[key] == 'false' and kwarg_end[key] == 'true':
                rlist.append(dic_command[key])
            else:
                rlist.append(dic_command[key] + ' ' + kwarg_end[key].lower())
    return rlist


class Lacp(object):
    """
    Manages Eth-Trunk interfaces LACP.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.__init_module__()

        # module input info
        self.trunk_id = self.module.params['trunk_id']
        self.mode = self.module.params['mode']
        self.param = dict()

        self.state = self.module.params['state']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def __init_module__(self):
        """ init module """

        self.module = AnsibleModule(
            argument_spec=self.spec,
            mutually_exclusive=[['trunk_id', 'global_priority']],
            required_one_of=[['trunk_id', 'global_priority']],
            required_together=[['member_if', 'priority']],
            supports_check_mode=True)

    def check_params(self):
        """
        :return:
        """
        for key in self.module.params.keys():
            if key in LACP.keys() and self.module.params[key] is not None:
                self.param[key] = self.module.params[key]
        msg = check_param(self.param)
        # if self.param.get('fast_timeout') is not None and self.param.get('timeout_type') is None:
        # self.param['timeout_type'] = 'Fast'
        if msg != 'ok':
            self.module.fail_json(msg=msg)

    def get_existing(self):
        """
        :return:
        """
        xml_str = bulid_xml(self.param)
        xml = get_nc_config(self.module, xml_str)
        return xml_to_dict(xml)

    def get_proposed(self):
        """
        :return:
        """
        proposed = dict(state=self.state)
        proposed.update(self.param)
        return proposed

    def get_end_state(self):
        """
        :return:
        """
        xml_str = bulid_xml(self.param)
        xml = get_nc_config(self.module, xml_str)
        return xml_to_dict(xml)

    def work(self):
        """worker"""

        self.check_params()
        existing = self.get_existing()
        proposed = self.get_proposed()

        # deal present or absent
        if self.state == "present":
            operation = 'merge'
        else:
            operation = 'delete'

        xml_str = bulid_xml(self.param, operation=operation)
        set_nc_config(self.module, xml_str)
        end_state = self.get_end_state()

        self.results['proposed'] = proposed
        self.results['existing'] = existing
        self.results['end_state'] = end_state
        updates_cmd = compare_config(self.module, existing, end_state)
        self.results['updates'] = updates_cmd
        if updates_cmd:
            self.results['changed'] = True
        else:
            self.results['changed'] = False

        self.module.exit_json(**self.results)


def main():
    """Module main"""

    argument_spec = dict(
        mode=dict(required=False,
                  choices=['Manual', 'Dynamic', 'Static'],
                  type='str'),
        trunk_id=dict(required=False, type='str'),
        preempt_enable=dict(required=False, choices=['true', 'false']),
        state_flapping=dict(required=False, choices=['true', 'false']),
        port_id_extension_enable=dict(required=False, choices=['true', 'false']),
        unexpected_mac_disable=dict(required=False, choices=['true', 'false']),
        system_id=dict(required=False, type='str'),
        timeout_type=dict(required=False, type='str', choices=['Slow', 'Fast']),
        fast_timeout=dict(required=False, type='int'),
        mixed_rate_link_enable=dict(required=False, choices=['true', 'false']),
        preempt_delay=dict(required=False, type='int'),
        collector_delay=dict(required=False, type='int'),
        max_active_linknumber=dict(required=False, type='int'),
        select=dict(required=False, type='str', choices=['Speed', 'Prority']),
        member_if=dict(required=False, type='str'),
        priority=dict(required=False, type='int'),
        global_priority=dict(required=False, type='int'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent'])
    )

    argument_spec.update(ce_argument_spec)
    module = Lacp(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
