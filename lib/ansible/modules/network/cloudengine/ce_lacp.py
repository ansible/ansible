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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ce_lacp
version_added: "2.10"
short_description: Manages Eth-Trunk interfaces on HUAWEI CloudEngine switches
description:
    - Manages Eth-Trunk specific configuration parameters on HUAWEI CloudEngine switches.
author: xuxiaowei0512 (@CloudEngine-Ansible)
notes:
    - C(state=absent) removes the Eth-Trunk config and interface if it already exists. If members to be removed are not explicitly
      passed, all existing members (if any), are removed, and Eth-Trunk removed.
    - This module requires the netconf system service be enabled on the remote device being managed.
    - Recommended connection is C(netconf).
    - This module also works with C(local) connections for legacy playbooks.
options:
    trunk_id:
        description:
            - Eth-Trunk interface number.
              The value is an integer.
              The value range depends on the assign forward eth-trunk mode command.
              When 256 is specified, the value ranges from 0 to 255.
              When 512 is specified, the value ranges from 0 to 511.
              When 1024 is specified, the value ranges from 0 to 1023.
        type: int
    mode:
        description:
            - Specifies the working mode of an Eth-Trunk interface.
        default: null
        choices: ['Manual','Dynamic','Static']
        type: str
    preempt_enable:
        description:
            - Specifies lacp preempt enable of Eth-Trunk lacp.
              The value is an boolean 'true' or 'false'.
        type: bool
    state_flapping:
        description:
            - Lacp dampening state-flapping.
        type: bool
    port_id_extension_enable:
        description:
            - Enable the function of extending the LACP negotiation port number.
        type: bool
    unexpected_mac_disable:
        description:
            - Lacp dampening unexpected-mac disable.
        type: bool
    system_id:
        description:
            - Link Aggregation Control Protocol System ID,interface Eth-Trunk View.
            - Formate 'X-X-X',X is hex(a,aa,aaa, or aaaa)
        type: str
    timeout_type:
        description:
            - Lacp timeout type,that may be 'Fast' or 'Slow'.
        choices: ['Slow', 'Fast']
        type: str
    fast_timeout:
        description:
            - When lacp timeout type is 'Fast', user-defined time can be a number(3~90).
        type: int
    mixed_rate_link_enable:
        description:
            - Value of max active linknumber.
        type: bool
    preempt_delay:
        description:
            - Value of preemption delay time.
        type: int
    collector_delay:
        description:
            - Value of delay time in units of 10 microseconds.
        type: int
    max_active_linknumber:
        description:
            - Max active linknumber in link aggregation group.
        type: int
    select:
        description:
            - Select priority or speed to preempt.
        choices: ['Speed', 'Prority']
        type: str
    priority:
        description:
            - The priority of eth-trunk member interface.
        type: int
    global_priority:
        description:
            - Configure lacp priority on system-view.
        type: int
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present','absent']
        type: str
'''
EXAMPLES = r'''
  - name: Ensure Eth-Trunk100 is created, and set to mode lacp-static
    ce_lacp:
      trunk_id: 100
      mode: 'lacp-static'
      state: present
  - name: Ensure Eth-Trunk100 is created, add two members, and set global priority to 1231
    ce_lacp:
      trunk_id: 100
      global_priority: 1231
      state: present
  - name: Ensure Eth-Trunk100 is created, and set mode to Dynamic and configure other options
    ce_lacp:
      trunk_id: 100
      mode: Dynamic
      preempt_enable: True,
      state_flapping: True,
      port_id_extension_enable: True,
      unexpected_mac_disable: True,
      timeout_type: Fast,
      fast_timeout: 123,
      mixed_rate_link_enable: True,
      preempt_delay: 23,
      collector_delay: 33,
      state: present
'''

RETURN = r'''
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
'''

import xml.etree.ElementTree as ET
import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config

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
        'weight': 'weight',
        'priority': 'portPriority',
        'global_priority': 'priority'
        }


def has_element(parent, xpath):
    """get or create a element by xpath"""
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
    """create a xml tree by dictionary with operation,get,merge and delete"""
    attrib = {'xmlns': "http://www.huawei.com/netconf/vrp",
              'content-version': "1.0", 'format-version': "1.0"}

    root = ET.Element('ifmtrunk')
    for key in kwargs.keys():
        if key in ('global_priority',):
            xpath = 'lacpSysInfo'
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
            if key == 'mode':
                element.text = str(kwargs[key])
            if key == 'trunk_id':
                element.text = 'Eth-Trunk' + str(kwargs[key])
    root.attrib = attrib
    config = ET.tostring(root)
    if operation == 'merge' or operation == 'delete':
        return '<config>%s</config>' % to_native(config)
    return '<filter type="subtree">%s</filter>' % to_native(config)


def check_param(kwargs):
    """check args list,the boolean or list values cloud not be checked,because they are limit by args list in main"""

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
    """transfer xml string into dict """
    rdict = dict()
    args = re.sub(r'xmlns=\".+?\"', '', args)
    root = ET.fromstring(args)
    ifmtrunk = root.find('.//ifmtrunk')
    if ifmtrunk is not None:
        try:
            ifmtrunk_iter = ET.Element.iter(ifmtrunk)
        except AttributeError:
            ifmtrunk_iter = ifmtrunk.getiterator()

        for ele in ifmtrunk_iter:
            if ele.text is not None and len(ele.text.strip()) > 0:
                rdict[ele.tag] = ele.text
    return rdict


def compare_config(module, kwarg_exist, kwarg_end):
    """compare config between exist and end"""
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
        self.init_module()

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

    def init_module(self):
        """ init AnsibleModule """

        self.module = AnsibleModule(
            argument_spec=self.spec,
            mutually_exclusive=[['trunk_id', 'global_priority']],
            required_one_of=[['trunk_id', 'global_priority']],
            supports_check_mode=True)

    def check_params(self):
        """check module params """
        for key in self.module.params.keys():
            if key in LACP.keys() and self.module.params[key] is not None:
                self.param[key] = self.module.params[key]
                if isinstance(self.module.params[key], bool):
                    self.param[key] = str(self.module.params[key]).lower()
        msg = check_param(self.param)
        if msg != 'ok':
            self.module.fail_json(msg=msg)

    def get_existing(self):
        """get existing"""
        xml_str = bulid_xml(self.param)
        xml = get_nc_config(self.module, xml_str)
        return xml_to_dict(xml)

    def get_proposed(self):
        """get proposed"""
        proposed = dict(state=self.state)
        proposed.update(self.param)
        return proposed

    def get_end_state(self):
        """ get end_state"""
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

    argument_spec = dict(
        mode=dict(required=False,
                  choices=['Manual', 'Dynamic', 'Static'],
                  type='str'),
        trunk_id=dict(required=False, type='int'),
        preempt_enable=dict(required=False, type='bool'),
        state_flapping=dict(required=False, type='bool'),
        port_id_extension_enable=dict(required=False, type='bool'),
        unexpected_mac_disable=dict(required=False, type='bool'),
        system_id=dict(required=False, type='str'),
        timeout_type=dict(required=False, type='str', choices=['Slow', 'Fast']),
        fast_timeout=dict(required=False, type='int'),
        mixed_rate_link_enable=dict(required=False, type='bool'),
        preempt_delay=dict(required=False, type='int'),
        collector_delay=dict(required=False, type='int'),
        max_active_linknumber=dict(required=False, type='int'),
        select=dict(required=False, type='str', choices=['Speed', 'Prority']),
        priority=dict(required=False, type='int'),
        global_priority=dict(required=False, type='int'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent'])
    )

    module = Lacp(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
