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
                    'supported_by': 'network'}

DOCUMENTATION = '''
---
module: nxos_ip_interface
version_added: "2.1"
short_description: Manages L3 attributes for IPv4 and IPv6 interfaces.
description:
    - Manages Layer 3 attributes for IPv4 and IPv6 interfaces.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - Interface must already be a L3 port when using this module.
    - Logical interfaces (po, loop, svi) must be created first.
    - C(mask) must be inserted in decimal format (i.e. 24) for
      both IPv6 and IPv4.
    - A single interface can have multiple IPv6 configured.
    - C(tag) is not idempotent for IPv6 addresses and I2 system image.
options:
    interface:
        description:
            - Full name of interface, i.e. Ethernet1/1, vlan10.
        required: true
    addr:
        description:
            - IPv4 or IPv6 Address.
        required: false
        default: null
    mask:
        description:
            - Subnet mask for IPv4 or IPv6 Address in decimal format.
        required: false
        default: null
    dot1q:
        description:
            - Configures IEEE 802.1Q VLAN encapsulation on the subinterface. The range is from 2 to 4093.
        required: false
        default: null
        version_added: "2.5"
    tag:
        description:
            - Route tag for IPv4 or IPv6 Address in integer format.
        required: false
        default: 0
        version_added: "2.4"
    allow_secondary:
        description:
            - Allow to configure IPv4 secondary addresses on interface.
        required: false
        default: false
        version_added: "2.4"
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent']
requirements:
    - "ipaddress"
'''

EXAMPLES = '''
- name: Ensure ipv4 address is configured on Ethernet1/32
  nxos_ip_interface:
    interface: Ethernet1/32
    transport: nxapi
    version: v4
    state: present
    addr: 20.20.20.20
    mask: 24

- name: Ensure ipv6 address is configured on Ethernet1/31
  nxos_ip_interface:
    interface: Ethernet1/31
    transport: cli
    version: v6
    state: present
    addr: '2001::db8:800:200c:cccb'
    mask: 64

- name: Ensure ipv4 address is configured with tag
  nxos_ip_interface:
    interface: Ethernet1/32
    transport: nxapi
    version: v4
    state: present
    tag: 100
    addr: 20.20.20.20
    mask: 24

- name: Ensure ipv4 address is configured on sub-intf with dot1q encapsulation
  nxos_ip_interface:
    interface: Ethernet1/32.10
    transport: nxapi
    version: v4
    state: present
    dot1q: 10
    addr: 20.20.20.20
    mask: 24

- name: Configure ipv4 address as secondary if needed
  nxos_ip_interface:
    interface: Ethernet1/32
    transport: nxapi
    version: v4
    state: present
    allow_secondary: true
    addr: 21.21.21.21
    mask: 24
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"addr": "20.20.20.20", "allow_secondary": true,
            "interface": "Ethernet1/32", "mask": "24", "tag": 100}
existing:
    description: k/v pairs of existing IP attributes on the interface
    returned: always
    type: dict
    sample: {"addresses": [{"addr": "11.11.11.11", "mask": 17, "tag": 101, "secondary": false}],
            "interface": "ethernet1/32", "prefixes": ["11.11.0.0/17"],
            "type": "ethernet", "vrf": "default"}
end_state:
    description: k/v pairs of IP attributes after module execution
    returned: always
    type: dict
    sample: {"addresses": [{"addr": "11.11.11.11", "mask": 17, "tag": 101, "secondary": false},
                           {"addr": "20.20.20.20", "mask": 24, "tag": 100, "secondary": true}],
            "interface": "ethernet1/32", "prefixes": ["11.11.0.0/17", "20.20.20.0/24"],
            "type": "ethernet", "vrf": "default"}
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface ethernet1/32", "ip address 20.20.20.20/24 secondary tag 100"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import re

try:
    import ipaddress

    HAS_IPADDRESS = True
except ImportError:
    HAS_IPADDRESS = False

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec
from ansible.module_utils.basic import AnsibleModule


def find_same_addr(existing, addr, mask, full=False, **kwargs):
    for address in existing['addresses']:
        if address['addr'] == addr and address['mask'] == mask:
            if full:
                if kwargs['version'] == 'v4' and int(address['tag']) == kwargs['tag']:
                    return address
                elif kwargs['version'] == 'v6' and kwargs['tag'] == 0:
                    # Currently we don't get info about IPv6 address tag
                    # But let's not break idempotence for the default case
                    return address
            else:
                return address
    return False


def execute_show_command(command, module):
    cmd = {}
    cmd['answer'] = None
    cmd['command'] = command
    cmd['output'] = 'text'
    cmd['prompt'] = None

    body = run_commands(module, [cmd])

    return body


def get_interface_type(interface):
    if interface.upper().startswith('ET'):
        return 'ethernet'
    elif interface.upper().startswith('VL'):
        return 'svi'
    elif interface.upper().startswith('LO'):
        return 'loopback'
    elif interface.upper().startswith('MG'):
        return 'management'
    elif interface.upper().startswith('MA'):
        return 'management'
    elif interface.upper().startswith('PO'):
        return 'portchannel'
    else:
        return 'unknown'


def is_default(interface, module):
    command = 'show run interface {0}'.format(interface)

    try:
        body = execute_show_command(command, module)[0]
        if 'invalid' in body.lower():
            return 'DNE'
        else:
            raw_list = body.split('\n')
            if raw_list[-1].startswith('interface'):
                return True
            else:
                return False
    except KeyError:
        return 'DNE'


def get_interface_mode(interface, intf_type, module):
    command = 'show interface {0} switchport'.format(interface)
    mode = 'unknown'

    if intf_type in ['ethernet', 'portchannel']:
        body = execute_show_command(command, module)[0]
        if len(body) > 0:
            if 'Switchport: Disabled' in body:
                mode = 'layer3'
            elif 'Switchport: Enabled' in body:
                mode = "layer2"
    elif intf_type == 'svi':
        mode = 'layer3'
    return mode


def send_show_command(interface_name, version, module):
    if version == 'v4':
        command = 'show ip interface {0}'.format(interface_name)
    elif version == 'v6':
        command = 'show ipv6 interface {0}'.format(interface_name)
    body = execute_show_command(command, module)
    return body


def parse_unstructured_data(body, interface_name, version, module):
    interface = {}
    interface['addresses'] = []
    interface['prefixes'] = []
    vrf = None

    body = body[0]
    splitted_body = body.split('\n')

    if version == "v6":
        if "ipv6 is disabled" not in body.lower():
            address_list = []
            # We can have multiple IPv6 on the same interface.
            # We need to parse them manually from raw output.
            for index in range(0, len(splitted_body) - 1):
                if "IPv6 address:" in splitted_body[index]:
                    first_reference_point = index + 1
                elif "IPv6 subnet:" in splitted_body[index]:
                    last_reference_point = index
                    break

            interface_list_table = splitted_body[first_reference_point:last_reference_point]

            for each_line in interface_list_table:
                address = each_line.strip().split(' ')[0]
                if address not in address_list:
                    address_list.append(address)
                    interface['prefixes'].append(str(ipaddress.ip_interface(u"%s" % address).network))

            if address_list:
                for ipv6 in address_list:
                    address = {}
                    splitted_address = ipv6.split('/')
                    address['addr'] = splitted_address[0]
                    address['mask'] = splitted_address[1]
                    interface['addresses'].append(address)

    else:
        for index in range(0, len(splitted_body) - 1):
            if "IP address" in splitted_body[index]:
                regex = r'.*IP\saddress:\s(?P<addr>\d{1,3}(?:\.\d{1,3}){3}),\sIP\ssubnet:' + \
                        r'\s\d{1,3}(?:\.\d{1,3}){3}\/(?P<mask>\d+)(?:\s(?P<secondary>secondary)\s)?' + \
                        r'(.+?tag:\s(?P<tag>\d+).*)?'
                match = re.match(regex, splitted_body[index])
                if match:
                    match_dict = match.groupdict()
                    if match_dict['secondary'] is None:
                        match_dict['secondary'] = False
                    else:
                        match_dict['secondary'] = True
                    if match_dict['tag'] is None:
                        match_dict['tag'] = 0
                    else:
                        match_dict['tag'] = int(match_dict['tag'])
                    interface['addresses'].append(match_dict)
                    prefix = str(ipaddress.ip_interface(u"%(addr)s/%(mask)s" % match_dict).network)
                    interface['prefixes'].append(prefix)

    try:
        vrf_regex = r'.+?VRF\s+(?P<vrf>\S+?)\s'
        match_vrf = re.match(vrf_regex, body, re.DOTALL)
        vrf = match_vrf.groupdict()['vrf']
    except AttributeError:
        vrf = None

    interface['interface'] = interface_name
    interface['type'] = get_interface_type(interface_name)
    interface['vrf'] = vrf

    return interface


def parse_interface_data(body):
    body = body[0]
    splitted_body = body.split('\n')

    for index in range(0, len(splitted_body) - 1):
        if "Encapsulation 802.1Q" in splitted_body[index]:
            regex = r'(.+?ID\s(?P<dot1q>\d+).*)?'
            match = re.match(regex, splitted_body[index])
            if match:
                match_dict = match.groupdict()
                if match_dict['dot1q'] is not None:
                    return int(match_dict['dot1q'])
    return 0


def get_dot1q_id(interface_name, module):

    if "." not in interface_name:
        return 0

    command = 'show interface {0}'.format(interface_name)
    try:
        body = execute_show_command(command, module)
        dot1q = parse_interface_data(body)
        return dot1q
    except KeyError:
        return 0


def get_ip_interface(interface_name, version, module):
    body = send_show_command(interface_name, version, module)
    interface = parse_unstructured_data(body, interface_name, version, module)
    return interface


def get_remove_ip_config_commands(interface, addr, mask, existing, version):
    commands = []
    if version == 'v4':
        # We can't just remove primary address if secondary address exists
        for address in existing['addresses']:
            if address['addr'] == addr:
                if address['secondary']:
                    commands.append('no ip address {0}/{1} secondary'.format(addr, mask))
                elif len(existing['addresses']) > 1:
                    new_primary = False
                    for address in existing['addresses']:
                        if address['addr'] != addr:
                            commands.append('no ip address {0}/{1} secondary'.format(address['addr'], address['mask']))

                            if not new_primary:
                                command = 'ip address {0}/{1}'.format(address['addr'], address['mask'])
                                new_primary = True
                            else:
                                command = 'ip address {0}/{1} secondary'.format(address['addr'], address['mask'])

                            if 'tag' in address and address['tag'] != 0:
                                command += " tag " + str(address['tag'])
                            commands.append(command)
                else:
                    commands.append('no ip address {0}/{1}'.format(addr, mask))
                break
    else:
        for address in existing['addresses']:
            if address['addr'] == addr:
                commands.append('no ipv6 address {0}/{1}'.format(addr, mask))

    return commands


def get_config_ip_commands(delta, interface, existing, version):
    commands = []
    delta = dict(delta)

    if version == 'v4':
        command = 'ip address {addr}/{mask}'.format(**delta)
        if len(existing['addresses']) > 0:
            if delta['allow_secondary']:
                for address in existing['addresses']:
                    if delta['addr'] == address['addr'] and address['secondary'] is False and delta['tag'] != 0:
                        break
                else:
                    command += ' secondary'
            else:
                # Remove all existed addresses if 'allow_secondary' isn't specified
                for address in existing['addresses']:
                    if address['secondary']:
                        commands.insert(0, 'no ip address {addr}/{mask} secondary'.format(**address))
                    else:
                        commands.append('no ip address {addr}/{mask}'.format(**address))
    else:
        if not delta['allow_secondary']:
            # Remove all existed addresses if 'allow_secondary' isn't specified
            for address in existing['addresses']:
                commands.insert(0, 'no ipv6 address {addr}/{mask}'.format(**address))

        command = 'ipv6 address {addr}/{mask}'.format(**delta)

    if int(delta['tag']) > 0:
        command += ' tag {tag}'.format(**delta)
    elif int(delta['tag']) == 0:
        # Case when we need to remove tag from an address. Just enter command like
        # 'ip address ...' (without 'tag') not enough
        commands += get_remove_ip_config_commands(interface, delta['addr'], delta['mask'], existing, version)

    commands.append(command)
    return commands


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def validate_params(addr, interface, mask, dot1q, tag, allow_secondary, version, state, intf_type, module):
    device_info = get_capabilities(module)
    network_api = device_info.get('network_api', 'nxapi')

    if state == "present":
        if addr is None or mask is None:
            module.fail_json(msg="An IP address AND a mask must be provided "
                                 "when state=present.")
    elif state == "absent" and version == "v6":
        if addr is None or mask is None:
            module.fail_json(msg="IPv6 address and mask must be provided when "
                                 "state=absent.")

    if intf_type != "ethernet" and network_api == 'cliconf':
        if is_default(interface, module) == "DNE":
            module.fail_json(msg="That interface does not exist yet. Create "
                                 "it first.", interface=interface)
    if mask is not None:
        try:
            if (int(mask) < 1 or int(mask) > 32) and version == "v4":
                raise ValueError
            elif int(mask) < 1 or int(mask) > 128:
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'mask' must be an integer between"
                                 " 1 and 32 when version v4 and up to 128 "
                                 "when version v6.", version=version,
                             mask=mask)
    if addr is not None and mask is not None:
        try:
            ipaddress.ip_interface(u'%s/%s' % (addr, mask))
        except ValueError:
            module.fail_json(msg="Warning! Invalid ip address or mask set.", addr=addr, mask=mask)

    if dot1q is not None:
        try:
            if 2 > dot1q > 4093:
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'dot1q' must be an integer between"
                                 " 2 and 4093", dot1q=dot1q)
    if tag is not None:
        try:
            if 0 > tag > 4294967295:
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'tag' must be an integer between"
                                 " 0 (default) and 4294967295."
                                 "To use tag you must set 'addr' and 'mask' params.", tag=tag)
    if allow_secondary is not None:
        try:
            if addr is None or mask is None:
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'secondary' can be used only when 'addr' and 'mask' set.",
                             allow_secondary=allow_secondary)


def main():
    argument_spec = dict(
        interface=dict(required=True),
        addr=dict(required=False),
        version=dict(required=False, choices=['v4', 'v6'],
                     default='v4'),
        mask=dict(type='str', required=False),
        dot1q=dict(required=False, default=0, type='int'),
        tag=dict(required=False, default=0, type='int'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent']),
        allow_secondary=dict(required=False, default=False,
                             type='bool'),
        include_defaults=dict(default=True),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if not HAS_IPADDRESS:
        module.fail_json(msg="ipaddress is required for this module. Run 'pip install ipaddress' for install.")

    warnings = list()

    addr = module.params['addr']
    version = module.params['version']
    mask = module.params['mask']
    dot1q = module.params['dot1q']
    tag = module.params['tag']
    allow_secondary = module.params['allow_secondary']
    interface = module.params['interface'].lower()
    state = module.params['state']

    intf_type = get_interface_type(interface)
    validate_params(addr, interface, mask, dot1q, tag, allow_secondary, version, state, intf_type, module)

    mode = get_interface_mode(interface, intf_type, module)
    if mode == 'layer2':
        module.fail_json(msg='That interface is a layer2 port.\nMake it '
                             'a layer 3 port first.', interface=interface)

    existing = get_ip_interface(interface, version, module)

    dot1q_tag = get_dot1q_id(interface, module)
    if dot1q_tag > 1:
        existing['dot1q'] = dot1q_tag

    args = dict(addr=addr, mask=mask, dot1q=dot1q, tag=tag, interface=interface, allow_secondary=allow_secondary)
    proposed = dict((k, v) for k, v in args.items() if v is not None)
    commands = []
    changed = False
    end_state = existing

    commands = ['interface {0}'.format(interface)]
    if state == 'absent':
        if existing['addresses']:
            if find_same_addr(existing, addr, mask):
                command = get_remove_ip_config_commands(interface, addr,
                                                        mask, existing, version)
                commands.append(command)
        if 'dot1q' in existing and existing['dot1q'] > 1:
            command = 'no encapsulation dot1Q {0}'.format(existing['dot1q'])
            commands.append(command)
    elif state == 'present':
        if not find_same_addr(existing, addr, mask, full=True, tag=tag, version=version):
            command = get_config_ip_commands(proposed, interface, existing, version)
            commands.append(command)
        if 'dot1q' not in existing and (intf_type in ['ethernet', 'portchannel'] and "." in interface):
            command = 'encapsulation dot1Q {0}'.format(proposed['dot1q'])
            commands.append(command)
    if len(commands) < 2:
        del commands[0]
    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            load_config(module, cmds)
            changed = True
            end_state = get_ip_interface(interface, version, module)
            if 'configure' in cmds:
                cmds.pop(0)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['commands'] = cmds
    results['changed'] = changed
    results['warnings'] = warnings

    module.exit_json(**results)


if __name__ == '__main__':
    main()
