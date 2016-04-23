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
module: nxos_facts
version_added: "2.1"
short_description: Gets facts about NX-OS switches
description:
    - Offers ability to extract facts from device
extends_documentation_fragment: nxos
author: Jason Edelman (@jedelman8), Gabriele Gerbino (@GGabriele)
'''

EXAMPLES = '''
# retrieve facts
- nxos_facts: host={{ inventory_hostname }}
'''

RETURN = '''
facts:
    description:
        - Show multiple information about device.
          These include interfaces, vlans, module and environment information.
    returned: always
    type: dict
    sample: {"fan_info": [{"direction":"front-to-back","hw_ver": "--",
            "model":"N9K-C9300-FAN2","name":"Fan1(sys_fan1)","status":"Ok"}],
            "hostname": "N9K2","interfaces": ["mgmt0","Ethernet1/1"],
            "kickstart": "6.1(2)I3(1)","module": [{"model": "N9K-C9396PX",
            "ports": "48","status": "active *"}],"os": "6.1(2)I3(1)",
            "platform": "Nexus9000 C9396PX Chassis","power_supply_info": [{
            "actual_output": "0 W","model": "N9K-PAC-650W","number": "1",
            "status":"Shutdown"}],"rr":"Reset Requested by CLI command reload",
            "vlan_list":[{"admin_state":"noshutdown","interfaces":["Ethernet1/1"],
            "name": "default","state": "active","vlan_id": "1"}]}
'''


def get_cli_body_ssh(command, response, module):
    if 'xml' in response[0]:
        body = []
    else:
        body = [json.loads(response[0])]
    return body


def execute_show(cmds, module, command_type=None):
    try:
        if command_type:
            response = module.execute(cmds, command_type=command_type)
        else:
            response = module.execute(cmds)
    except ShellError, clie:
        module.fail_json(msg='Error sending {0}'.format(command),
                         error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh(command, response, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            value = table.get(key)
            if value:
                new_dict[new_key] = str(value)
            else:
                new_dict[new_key] = value
    return new_dict


def get_show_version_facts(module):
    command = 'show version'
    body = execute_show_command(command, module)[0]

    key_map = {
                "rr_sys_ver": "os",
                "kickstart_ver_str": "kickstart",
                "chassis_id": "platform",
                "host_name": "hostname",
                "rr_reason": "rr"
            }

    mapped_show_version_facts = apply_key_map(key_map, body)
    return mapped_show_version_facts


def get_interface_facts(module):
    command = 'show interface status'
    body = execute_show_command(command, module)[0]

    interface_list = []
    interface_table = body['TABLE_interface']['ROW_interface']

    if isinstance(interface_table, dict):
        interface_table = [interface_table]

    for each in interface_table:
        interface = str(each.get('interface', None))
        if interface:
            interface_list.append(interface)
    return interface_list


def get_show_module_facts(module):
    command = 'show module'
    body = execute_show_command(command, module)[0]

    module_facts = []
    module_table = body['TABLE_modinfo']['ROW_modinfo']

    key_map = {
                "ports": "ports",
                "type": "type",
                "model": "model",
                "status": "status"
            }

    if isinstance(module_table, dict):
        module_table = [module_table]

    for each in module_table:
        mapped_module_facts = apply_key_map(key_map, each)
        module_facts.append(mapped_module_facts)
    return module_facts


def get_environment_facts(module):
    command = 'show environment'
    body = execute_show_command(command, module)[0]

    powersupply = get_powersupply_facts(body)
    fan = get_fan_facts(body)

    return (powersupply, fan)


def get_powersupply_facts(body):
    powersupply_facts = []
    powersupply_table = body['powersup']['TABLE_psinfo']['ROW_psinfo']

    key_map = {
                "psnum": "number",
                "psmodel": "model",
                "actual_out": "actual_output",
                "actual_in": "actual_input",
                "total_capa": "total_capacity",
                "ps_status": "status"
            }

    if isinstance(powersupply_table, dict):
        powersupply_table = [powersupply_table]

    for each in powersupply_table:
        mapped_powersupply_facts = apply_key_map(key_map, each)
        powersupply_facts.append(mapped_powersupply_facts)
    return powersupply_facts


def get_fan_facts(body):
    fan_facts = []
    fan_table = body['fandetails']['TABLE_faninfo']['ROW_faninfo']

    key_map = {
                "fanname": "name",
                "fanmodel": "model",
                "fanhwver": "hw_ver",
                "fandir": "direction",
                "fanstatus": "status"
            }

    if isinstance(fan_table, dict):
        fan_table = [fan_table]

    for each in fan_table:
        mapped_fan_facts = apply_key_map(key_map, each)
        fan_facts.append(mapped_fan_facts)
    return fan_facts


def get_vlan_facts(module):
    command = 'show vlan brief'
    body = execute_show_command(command, module)[0]

    vlan_list = []
    vlan_table = body['TABLE_vlanbriefxbrief']['ROW_vlanbriefxbrief']

    if isinstance(vlan_table, dict):
        vlan_table = [vlan_table]

    for each in vlan_table:
        vlan = str(each.get('vlanshowbr-vlanid-utf', None))
        if vlan:
            vlan_list.append(vlan)
    return vlan_list


def main():
    argument_spec = dict()
    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    # Get 'show version' facts.
    show_version = get_show_version_facts(module)

    # Get interfaces facts.
    interfaces_list = get_interface_facts(module)

    # Get module facts.
    show_module = get_show_module_facts(module)

    # Get environment facts.
    powersupply, fan = get_environment_facts(module)

    # Get vlans facts.
    vlan = get_vlan_facts(module)

    facts = dict(
        interfaces_list=interfaces_list,
        module=show_module,
        power_supply_info=powersupply,
        fan_info=fan,
        vlan_list=vlan)

    facts.update(show_version)

    module.exit_json(ansible_facts=facts)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.nxos import *
if __name__ == '__main__':
    main()
