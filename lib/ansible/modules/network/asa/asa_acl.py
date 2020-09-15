#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: asa_acl
version_added: "2.2"
author: "Patrick Ogenstad (@ogenstad)"
short_description: Manage access-lists on a Cisco ASA
description:
  - This module allows you to work with access-lists on a Cisco ASA device.
extends_documentation_fragment: asa
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device running-config.  Be sure to note the configuration
        command syntax as some commands are automatically modified by the
        device config parser.
    required: true
    aliases: [commands]
  before:
    description:
      - The ordered set of commands to push on to the command stack if
        a change needs to be made.  This allows the playbook designer
        the opportunity to perform configuration commands prior to pushing
        any changes without affecting how the set of commands are matched
        against the system.
  after:
    description:
      - The ordered set of commands to append to the end of the command
        stack if a changed needs to be made.  Just like with I(before) this
        allows the playbook designer to append a set of commands to be
        executed after the command set.
  match:
    description:
      - Instructs the module on the way to perform the matching of
        the set of commands against the current device config.  If
        match is set to I(line), commands are matched line by line.  If
        match is set to I(strict), command lines are matched with respect
        to position.  Finally if match is set to I(exact), command lines
        must be an equal match.
    default: line
    choices: ['line', 'strict', 'exact']
  replace:
    description:
      - Instructs the module on the way to perform the configuration
        on the device.  If the replace argument is set to I(line) then
        the modified lines are pushed to the device in configuration
        mode.  If the replace argument is set to I(block) then the entire
        command block is pushed to the device in configuration mode if any
        line is not correct.
    default: line
    choices: ['line', 'block']
  force:
    description:
      - The force argument instructs the module to not consider the
        current devices running-config.  When set to true, this will
        cause the module to push the contents of I(src) into the device
        without first checking if already configured.
    type: bool
    default: 'no'
  config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current running-config to use as a base for comparing
        against the contents of source.  There are times when it is not
        desirable to have the task get the current running-config for
        every task in a playbook.  The I(config) argument allows the
        implementer to pass in the configuration to use as the base
        config for comparison.
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
---
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: cisco
    password: cisco
    transport: cli
    authorize: yes
    auth_pass: cisco

---
- asa_acl:
    lines:
      - access-list ACL-ANSIBLE extended permit tcp any any eq 82
      - access-list ACL-ANSIBLE extended permit tcp any any eq www
      - access-list ACL-ANSIBLE extended permit tcp any any eq 97
      - access-list ACL-ANSIBLE extended permit tcp any any eq 98
      - access-list ACL-ANSIBLE extended permit tcp any any eq 99
    before: clear configure access-list ACL-ANSIBLE
    match: strict
    replace: block
    provider: "{{ cli }}"

- asa_acl:
    lines:
      - access-list ACL-OUTSIDE extended permit tcp any any eq www
      - access-list ACL-OUTSIDE extended permit tcp any any eq https
    context: customer_a
    provider: "{{ cli }}"
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['access-list ACL-OUTSIDE extended permit tcp any any eq www']
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.asa.asa import asa_argument_spec, check_args
from ansible.module_utils.network.asa.asa import get_config, load_config, run_commands

from ansible.module_utils.network.common.config import NetworkConfig, dumps


def get_acl_config(module, acl_name):
    contents = module.params['config']
    if not contents:
        contents = get_config(module)

    filtered_config = list()
    for item in contents.split('\n'):
        if item.startswith('access-list %s ' % acl_name):
            filtered_config.append(item)

    return NetworkConfig(indent=1, contents='\n'.join(filtered_config))


def parse_acl_name(module):
    first_line = True
    for line in module.params['lines']:
        ace = line.split()
        if ace[0] != 'access-list':
            module.fail_json(msg='All lines/commands must begin with "access-list" %s is not permitted' % ace[0])
        if len(ace) <= 1:
            module.fail_json(msg='All lines/commands must contain the name of the access-list')
        if first_line:
            acl_name = ace[1]
        else:
            if acl_name != ace[1]:
                module.fail_json(msg='All lines/commands must use the same access-list %s is not %s' % (ace[1], acl_name))
        first_line = False

    return acl_name


def main():

    argument_spec = dict(
        lines=dict(aliases=['commands'], required=True, type='list'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=['line', 'strict', 'exact']),
        replace=dict(default='line', choices=['line', 'block']),

        force=dict(default=False, type='bool'),
        config=dict()
    )

    argument_spec.update(asa_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    lines = module.params['lines']

    result = {'changed': False}

    candidate = NetworkConfig(indent=1)
    candidate.add(lines)

    acl_name = parse_acl_name(module)

    if not module.params['force']:
        contents = get_acl_config(module, acl_name)
        config = NetworkConfig(indent=1, contents=contents)

        commands = candidate.difference(config)
        commands = dumps(commands, 'commands').split('\n')
        commands = [str(c) for c in commands if c]
    else:
        commands = str(candidate).split('\n')

    if commands:
        if module.params['before']:
            commands[:0] = module.params['before']

        if module.params['after']:
            commands.extend(module.params['after'])

        if not module.check_mode:
            load_config(module, commands)

        result['changed'] = True

    result['updates'] = commands

    module.exit_json(**result)


if __name__ == '__main__':
    main()
