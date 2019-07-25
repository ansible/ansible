#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
module: nxos_vsan
extends_documentation_fragment: nxos
version_added: 2.9
short_description: Configuration of vsan.
description:
    - Configuration of vsan for Cisco MDS NXOS.
author:
    - Suhas Bharadwaj (@srbharadwaj) (subharad@cisco.com)
options:
    vsan:
        description:
            - List of vsan details to be added or removed
        type: list
        suboptions:
            id:
                description:
                    - Vsan id
                required: True
            name:
                description:
                    - Name of the vsan
            suspend:
                description:
                    - suspend the vsan if True
                type: bool
                default: False
            remove:
                description:
                    - Removes the vsan if True
                type: bool
                default: False
            interface:
                description:
                    - List of vsan's interfaces to be added
                type: list
'''

EXAMPLES = '''
---
-
  name: "Test that vsan module works"
  nxos_vsan:
    provider: "{{ creds }}"
    vsan:
      -
        id: 922
        interface:
          - fc1/1
          - fc1/2
          - "port-channel 1"
        name: vsan-SAN-A
        remove: false
        suspend: false
      -
        id: 923
        interface:
          - fc1/11
          - fc1/21
          - "port-channel 2"
        name: vsan-SAN-B
        remove: false
        suspend: true
      -
        id: 1923
        name: vsan-SAN-Old
        remove: true

'''

RETURN = '''
commands:
  description: commands sent to the device
  returned: always
  type: list
  sample:
    - terminal dont-ask
    - vsan database
    - vsan 922 interface fc1/40
    - vsan 922 interface port-channel 155
    - no terminal dont-ask
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.nxos import load_config, nxos_argument_spec, run_commands
import re

__metaclass__ = type


class Vsan(object):
    def __init__(self, vsanid):
        self.vsanid = vsanid
        self.vsanname = None
        self.vsanstate = None
        self.vsanoperstate = None
        self.vsaninterfaces = []


class GetVsanInfoFromSwitch(object):
    """docstring for GetVsanInfoFromSwitch"""

    def __init__(self, module):
        self.module = module
        self.vsaninfo = {}
        self.processShowVsan()
        self.processShowVsanMembership()

    def execute_show_vsan_cmd(self):
        output = execute_show_command('show vsan', self.module)[0]
        return output

    def execute_show_vsan_mem_cmd(self):
        output = execute_show_command('show vsan membership', self.module)[0]
        return output

    def processShowVsan(self):
        patv = r"^vsan\s+(\d+)\s+information"
        patnamestate = "name:(.*)state:(.*)"
        patoperstate = "operational state:(.*)"

        output = self.execute_show_vsan_cmd().split("\n")
        for o in output:
            z = re.match(patv, o.strip())
            if z:
                v = z.group(1).strip()
                self.vsaninfo[v] = Vsan(v)

            z1 = re.match(patnamestate, o.strip())
            if z1:
                n = z1.group(1).strip()
                s = z1.group(2).strip()
                self.vsaninfo[v].vsanname = n
                self.vsaninfo[v].vsanstate = s

            z2 = re.match(patoperstate, o.strip())
            if z2:
                oper = z2.group(1).strip()
                self.vsaninfo[v].vsanoperstate = oper

        # 4094/4079 vsan is always present
        self.vsaninfo['4079'] = Vsan('4079')
        self.vsaninfo['4094'] = Vsan('4094')

    def processShowVsanMembership(self):
        patv = r"^vsan\s+(\d+).*"
        output = self.execute_show_vsan_mem_cmd().split("\n")
        memlist = []
        v = None
        for o in output:
            z = re.match(patv, o.strip())
            if z:
                if v is not None:
                    self.vsaninfo[v].vsaninterfaces = memlist
                    memlist = []
                v = z.group(1)
            if 'interfaces' not in o:
                llist = o.strip().split()
                memlist = memlist + llist
        self.vsaninfo[v].vsaninterfaces = memlist

    def getVsanInfoObjects(self):
        return self.vsaninfo


def execute_show_command(command, module, command_type='cli_show'):
    output = 'text'
    commands = [{
        'command': command,
        'output': output,
    }]
    return run_commands(module, commands)


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def main():
    vsan_element_spec = dict(
        id=dict(required=True, type='int'),
        name=dict(type='str'),
        remove=dict(type='bool'),
        suspend=dict(type='bool'),
        interface=dict(type='list', elements='str')
    )

    argument_spec = dict(
        vsan=dict(type='list', elements='dict', options=vsan_element_spec)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)
    warnings = list()
    messages = list()
    commands_executed = list()
    result = {'changed': False}

    obj = GetVsanInfoFromSwitch(module)
    dictSwVsanObjs = obj.getVsanInfoObjects()

    commands = []
    vsan_list = module.params['vsan']

    for eachvsan in vsan_list:
        vsanid = str(eachvsan['id'])
        vsanname = eachvsan['name']
        vsanremove = eachvsan['remove']
        vsansuspend = eachvsan['suspend']
        vsaninterface_list = eachvsan['interface']

        if int(vsanid) < 1 or int(vsanid) >= 4095:
            module.fail_json(msg=vsanid + " - This is an invalid vsan. Supported vsan range is 1-4094")

        if vsanid in dictSwVsanObjs.keys():
            sw_vsanid = vsanid
            sw_vsanname = dictSwVsanObjs[vsanid].vsanname
            sw_vsanstate = dictSwVsanObjs[vsanid].vsanstate
            sw_vsaninterfaces = dictSwVsanObjs[vsanid].vsaninterfaces
        else:
            sw_vsanid = None
            sw_vsanname = None
            sw_vsanstate = None
            sw_vsaninterfaces = []

        if vsanremove:
            # Negetive case:
            if vsanid == '4079' or vsanid == '4094':
                messages.append(str(vsanid) + " is a reserved vsan, hence cannot be removed")
                continue
            if vsanid == sw_vsanid:
                commands.append("no vsan " + str(vsanid))
                messages.append("deleting the vsan " + str(vsanid))
            else:
                messages.append("There is no vsan " + str(vsanid) + " present in the switch. Hence there is nothing to delete")
            continue
        else:
            # Negetive case:
            if vsanid == '4079' or vsanid == '4094':
                messages.append(str(vsanid) + " is a reserved vsan, and always present on the switch")
            else:
                if vsanid == sw_vsanid:
                    messages.append("There is already a vsan " + str(vsanid) + " present in the switch. Hence there is nothing to configure")
                else:
                    commands.append("vsan " + str(vsanid))
                    messages.append("creating vsan " + str(vsanid))

        if vsanname is not None:
            # Negetive case:
            if vsanid == '4079' or vsanid == '4094':
                messages.append(str(vsanid) + " is a reserved vsan, and cannot be renamed")
            else:
                if vsanname == sw_vsanname:
                    messages.append(
                        "There is already a vsan " +
                        str(vsanid) +
                        " present in the switch, which has the name " +
                        vsanname +
                        " Hence there is nothing to configure")
                else:
                    commands.append("vsan " + str(vsanid) + " name " + vsanname)
                    messages.append("setting vsan name to " + vsanname + " for vsan " + str(vsanid))

        if vsansuspend:
            # Negetive case:
            if vsanid == '4079' or vsanid == '4094':
                messages.append(str(vsanid) + " is a reserved vsan, and cannot be suspended")
            else:
                if sw_vsanstate == 'suspended':
                    messages.append("There is already a vsan " + str(vsanid) + " present in the switch, which is in suspended state ")
                else:
                    commands.append("vsan " + str(vsanid) + " suspend")
                    messages.append("suspending the vsan " + str(vsanid))
        else:
            if sw_vsanstate == 'active':
                messages.append("There is already a vsan " + str(vsanid) + " present in the switch, which is in active state ")
            else:
                commands.append("no vsan " + str(vsanid) + " suspend")
                messages.append("no suspending the vsan " + str(vsanid))

        if vsaninterface_list is not None:
            for each_interface_name in vsaninterface_list:
                # For fcip,port-channel,vfc-port-channel need to remove the extra space to compare
                temp = re.sub(' +', '', each_interface_name)
                if temp in sw_vsaninterfaces:
                    messages.append(each_interface_name + " is already present in the vsan " + str(vsanid) + " interface list")
                else:
                    commands.append("vsan " + str(vsanid) + " interface " + each_interface_name)
                    messages.append("adding interface " + each_interface_name + " to vsan " + str(vsanid))

    if len(commands) != 0:
        commands = ["terminal dont-ask"] + ["vsan database"] + commands + ["no terminal dont-ask"]

    cmds = flatten_list(commands)
    commands_executed = cmds

    if commands_executed:
        if module.check_mode:
            module.exit_json(changed=False, commands=commands_executed, msg="Check Mode: No cmds issued to the hosts")
        else:
            result['changed'] = True
            load_config(module, commands_executed)

    result['messages'] = messages
    result['commands'] = commands_executed
    result['warnings'] = warnings
    module.exit_json(**result)


if __name__ == '__main__':
    main()
