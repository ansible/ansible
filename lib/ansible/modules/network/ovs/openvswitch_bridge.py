#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2013, David Stygstra <david.stygstra@gmail.com>
# Portions copyright @ 2015 VMware, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: openvswitch_bridge
version_added: 1.4
author: "David Stygstra (@stygstra)"
short_description: Manage Open vSwitch bridges
requirements: [ ovs-vsctl ]
description:
    - Manage Open vSwitch bridges
options:
    bridge:
        required: true
        description:
            - Name of bridge or fake bridge to manage
    parent:
        version_added: "2.3"
        description:
            - Bridge parent of the fake bridge to manage
    vlan:
        version_added: "2.3"
        description:
            - The VLAN id of the fake bridge to manage (must be between 0 and
              4095). This parameter is required if I(parent) parameter is set.
    state:
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the bridge should exist
    timeout:
        default: 5
        description:
            - How long to wait for ovs-vswitchd to respond
    external_ids:
        version_added: 2.0
        description:
            - A dictionary of external-ids. Omitting this parameter is a No-op.
              To  clear all external-ids pass an empty value.
    fail_mode:
        version_added: 2.0
        choices : [secure, standalone]
        description:
            - Set bridge fail-mode. The default value (None) is a No-op.
    set:
        version_added: 2.3
        description:
            - Run set command after bridge configuration. This parameter is
              non-idempotent, play will always return I(changed) state if
              present
'''

EXAMPLES = '''
# Create a bridge named br-int
- openvswitch_bridge:
    bridge: br-int
    state: present

# Create a fake bridge named br-int within br-parent on the VLAN 405
- openvswitch_bridge:
    bridge: br-int
    parent: br-parent
    vlan: 405
    state: present

# Create an integration bridge
- openvswitch_bridge:
    bridge: br-int
    state: present
    fail_mode: secure
  args:
    external_ids:
      bridge-id: br-int
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


def _fail_mode_to_str(text):
    if not text:
        return None
    else:
        return text.strip()


def _external_ids_to_dict(text):
    if not text:
        return None
    else:
        d = {}

        for l in text.splitlines():
            if l:
                k, v = l.split('=')
                d[k] = v

        return d


def map_obj_to_commands(want, have, module):
    commands = list()

    if module.params['state'] == 'absent':
        if have:
            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s del-br"
                                   " %(bridge)s")
            command = templatized_command % module.params
            commands.append(command)
    else:
        if have:
            if want['fail_mode'] != have['fail_mode']:
                templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                       " set-fail-mode %(bridge)s"
                                       " %(fail_mode)s")
                command = templatized_command % module.params
                commands.append(command)

            if want['external_ids'] != have['external_ids']:
                templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                       " br-set-external-id %(bridge)s")
                command = templatized_command % module.params
                if want['external_ids']:
                    for k, v in iteritems(want['external_ids']):
                        if (k not in have['external_ids']
                                or want['external_ids'][k] != have['external_ids'][k]):
                            command += " " + k + " " + v
                            commands.append(command)
        else:
            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s add-br"
                                   " %(bridge)s")
            command = templatized_command % module.params

            if want['parent']:
                templatized_command = "%(parent)s %(vlan)s"
                command += " " + templatized_command % module.params

            if want['set']:
                templatized_command = " -- set %(set)s"
                command += templatized_command % module.params

            commands.append(command)

            if want['fail_mode']:
                templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                       " set-fail-mode %(bridge)s"
                                       " %(fail_mode)s")
                command = templatized_command % module.params
                commands.append(command)

            if want['external_ids']:
                for k, v in iteritems(want['external_ids']):
                    templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                           " br-set-external-id %(bridge)s")
                    command = templatized_command % module.params
                    command += " " + k + " " + v
                    commands.append(command)
    return commands


def map_config_to_obj(module):
    templatized_command = "%(ovs-vsctl)s -t %(timeout)s list-br"
    command = templatized_command % module.params
    rc, out, err = module.run_command(command, check_rc=True)
    if rc != 0:
        module.fail_json(msg=err)

    obj = {}

    if module.params['bridge'] in out.splitlines():
        obj['bridge'] = module.params['bridge']

        templatized_command = ("%(ovs-vsctl)s -t %(timeout)s br-to-parent"
                               " %(bridge)s")
        command = templatized_command % module.params
        rc, out, err = module.run_command(command, check_rc=True)
        obj['parent'] = out.strip()

        templatized_command = ("%(ovs-vsctl)s -t %(timeout)s br-to-vlan"
                               " %(bridge)s")
        command = templatized_command % module.params
        rc, out, err = module.run_command(command, check_rc=True)
        obj['vlan'] = out.strip()

        templatized_command = ("%(ovs-vsctl)s -t %(timeout)s get-fail-mode"
                               " %(bridge)s")
        command = templatized_command % module.params
        rc, out, err = module.run_command(command, check_rc=True)
        obj['fail_mode'] = _fail_mode_to_str(out)

        templatized_command = ("%(ovs-vsctl)s -t %(timeout)s br-get-external-id"
                               " %(bridge)s")
        command = templatized_command % module.params
        rc, out, err = module.run_command(command, check_rc=True)
        obj['external_ids'] = _external_ids_to_dict(out)

    return obj


def map_params_to_obj(module):
    obj = {
        'bridge': module.params['bridge'],
        'parent': module.params['parent'],
        'vlan': module.params['vlan'],
        'fail_mode': module.params['fail_mode'],
        'external_ids': module.params['external_ids'],
        'set': module.params['set']
    }

    return obj


def main():
    """ Entry point. """
    argument_spec = {
        'bridge': {'required': True},
        'parent': {'default': None},
        'vlan': {'default': None, 'type': 'int'},
        'state': {'default': 'present', 'choices': ['present', 'absent']},
        'timeout': {'default': 5, 'type': 'int'},
        'external_ids': {'default': None, 'type': 'dict'},
        'fail_mode': {'default': None},
        'set': {'required': False, 'default': None}
    }

    required_if = [('parent', not None, ('vlan',))]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
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
