#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2013, David Stygstra <david.stygstra@gmail.com>
# Portions copyright @ 2015 VMware, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: openvswitch_port
version_added: 1.4
author: "David Stygstra (@stygstra)"
short_description: Manage Open vSwitch ports
requirements: [ ovs-vsctl ]
description:
    - Manage Open vSwitch ports
options:
    bridge:
        required: true
        description:
            - Name of bridge to manage
    port:
        required: true
        description:
            - Name of port to manage on the bridge
    tag:
        version_added: 2.2
        required: false
        description:
            - VLAN tag for this port. Must be a value between
              0 and 4095.
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the port should exist
    timeout:
        required: false
        default: 5
        description:
            - How long to wait for ovs-vswitchd to respond
    external_ids:
        version_added: 2.0
        required: false
        default: {}
        description:
            - Dictionary of external_ids applied to a port.
    set:
        version_added: 2.0
        required: false
        default: None
        description:
            - Set a single property on a port.
'''

EXAMPLES = '''
# Creates port eth2 on bridge br-ex
- openvswitch_port:
    bridge: br-ex
    port: eth2
    state: present

# Creates port eth6
- openvswitch_port:
    bridge: bridge-loop
    port: eth6
    state: present
    set: Interface eth6

# Creates port vlan10 with tag 10 on bridge br-ex
- openvswitch_port:
    bridge: br-ex
    port: vlan10
    tag: 10
    state: present
    set: Interface vlan10

# Assign interface id server1-vifeth6 and mac address 00:00:5E:00:53:23
# to port vifeth6 and setup port to be managed by a controller.
- openvswitch_port:
    bridge: br-int
    port: vifeth6
    state: present
  args:
    external_ids:
      iface-id: '{{ inventory_hostname }}-vifeth6'
      attached-mac: '00:00:5E:00:53:23'
      vm-id: '{{ inventory_hostname }}'
      iface-status: active
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


def _external_ids_to_dict(text):
    text = text.strip()

    if text == '{}':
        return None
    else:
        d = {}

        for kv in text[1:-1].split(','):
            kv = kv.strip()
            k, v = kv.split('=')
            d[k] = v

        return d

def _tag_to_str(text):
    text = text.strip()

    if text == '[]':
        return None
    else:
        return text

def map_obj_to_commands(want, have, module):
    commands = list()

    if module.params['state'] == 'absent':
        if have:
            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s del-port"
                                   " %(bridge)s %(port)s")
            command = templatized_command % module.params
            commands.append(command)
    else:
        if have:
            if want['tag'] != have['tag']:
                templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                       " set port %(port)s tag=%(tag)s")
                command = templatized_command % module.params
                commands.append(command)

            if want['external_ids'] != have['external_ids']:
                for k, v in iteritems(want['external_ids']):
                    if (not have['external_ids']
                            or k not in have['external_ids']
                            or want['external_ids'][k] != have['external_ids'][k]):
                        if v is None:
                            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                                   " remove port %(port)s"
                                                   " external_ids " + k)
                            command = templatized_command % module.params
                            commands.append(command)
                        else:
                            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                                   " set port %(port)s"
                                                   " external_ids:")
                            command = templatized_command % module.params
                            command += k + "=" + v
                            commands.append(command)
        else:
            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s add-port"
                                   " %(bridge)s %(port)s")
            command = templatized_command % module.params

            if want['tag']:
                templatized_command =  " tag=%(tag)s"
                command += templatized_command % module.params

            if want['set']:
                templatized_command = " -- set %(set)s"
                command += templatized_command % module.params

            commands.append(command)

            if want['external_ids']:
                for k, v in iteritems(want['external_ids']):
                    templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                           " set port %(port)s external_ids:")
                    command = templatized_command % module.params
                    command +=  k + "=" + v
                    commands.append(command)

    return commands


def map_config_to_obj(module):
    templatized_command = "%(ovs-vsctl)s -t %(timeout)s list-ports %(bridge)s"
    command = templatized_command % module.params
    rc, out, err = module.run_command(command, check_rc=True)
    if rc != 0:
        module.fail_json(msg=err)

    obj = {}

    if module.params['port'] in out.splitlines():
        obj['bridge'] = module.params['bridge']
        obj['port'] = module.params['port']

        templatized_command = ("%(ovs-vsctl)s -t %(timeout)s get"
                               " Port %(port)s tag")
        command = templatized_command % module.params
        rc, out, err = module.run_command(command, check_rc=True)
        obj['tag'] = _tag_to_str(out)

        templatized_command = ("%(ovs-vsctl)s -t %(timeout)s get"
                               " Port %(port)s external_ids")
        command = templatized_command % module.params
        rc, out, err = module.run_command(command, check_rc=True)
        obj['external_ids'] = _external_ids_to_dict(out)

    return obj


def map_params_to_obj(module):
    obj = {
        'bridge': module.params['bridge'],
        'port': module.params['port'],
        'tag': module.params['tag'],
        'external_ids': module.params['external_ids'],
        'set': module.params['set']
    }

    return obj

def main():
    """ Entry point. """
    argument_spec={
        'bridge': {'required': True},
        'port': {'required': True},
        'state': {'default': 'present', 'choices': ['present', 'absent']},
        'timeout': {'default': 5, 'type': 'int'},
        'external_ids': {'default': None, 'type': 'dict'},
        'tag': {'default': None},
        'set': {'required': False, 'default': None}
    }

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    # We add ovs-vsctl to module_params to later build up templatized commands
    module.params["ovs-vsctl"] = module.get_bin_path("ovs-vsctl", True)

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            for c in commands:
                module.run_command(c, check_rc=True)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
