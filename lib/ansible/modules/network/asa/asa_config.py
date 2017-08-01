#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: asa_config
version_added: "2.2"
author: "Peter Sprygada (@privateip), Patrick Ogenstad (@ogenstad)"
short_description: Manage configuration sections on Cisco ASA devices
description:
  - Cisco ASA configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with ASA configuration sections in
    a deterministic way.
extends_documentation_fragment: asa
options:
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device running-config.  Be sure to note the configuration
        command syntax as some commands are automatically modified by the
        device config parser.
    required: false
    default: null
    aliases: ['commands']
  parents:
    description:
      - The ordered set of parents that uniquely identify the section
        the commands should be checked against.  If the parents argument
        is omitted, the commands are checked against the set of top
        level or global commands.
    required: false
    default: null
  src:
    description:
      - Specifies the source path to the file that contains the configuration
        or configuration template to load.  The path to the source file can
        either be the full path on the Ansible control host or a relative
        path from the playbook or role root directory.  This argument is mutually
        exclusive with I(lines).
    required: false
    default: null
  before:
    description:
      - The ordered set of commands to push on to the command stack if
        a change needs to be made.  This allows the playbook designer
        the opportunity to perform configuration commands prior to pushing
        any changes without affecting how the set of commands are matched
        against the system
    required: false
    default: null
  after:
    description:
      - The ordered set of commands to append to the end of the command
        stack if a change needs to be made.  Just like with I(before) this
        allows the playbook designer to append a set of commands to be
        executed after the command set.
    required: false
    default: null
  match:
    description:
      - Instructs the module on the way to perform the matching of
        the set of commands against the current device config.  If
        match is set to I(line), commands are matched line by line.  If
        match is set to I(strict), command lines are matched with respect
        to position.  If match is set to I(exact), command lines
        must be an equal match.  Finally, if match is set to I(none), the
        module will not attempt to compare the source configuration with
        the running configuration on the remote device.
    required: false
    default: line
    choices: ['line', 'strict', 'exact', 'none']
  replace:
    description:
      - Instructs the module on the way to perform the configuration
        on the device.  If the replace argument is set to I(line) then
        the modified lines are pushed to the device in configuration
        mode.  If the replace argument is set to I(block) then the entire
        command block is pushed to the device in configuration mode if any
        line is not correct
    required: false
    default: line
    choices: ['line', 'block']
  update:
    description:
      - The I(update) argument controls how the configuration statements
        are processed on the remote device.  Valid choices for the I(update)
        argument are I(merge) and I(check).  When the argument is set to
        I(merge), the configuration changes are merged with the current
        device running configuration.  When the argument is set to I(check)
        the configuration updates are determined but not actually configured
        on the remote device.
    required: false
    default: merge
    choices: ['merge', 'check']
  commit:
    description:
      - This argument specifies the update method to use when applying the
        configuration changes to the remote node.  If the value is set to
        I(merge) the configuration updates are merged with the running-
        config.  If the value is set to I(check), no changes are made to
        the remote host.
    required: false
    default: merge
    choices: ['merge', 'check']
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made.  The backup file is written to the C(backup)
        folder in the playbook root directory.  If the directory does not
        exist, it is created.
    required: false
    default: no
    choices: ['yes', 'no']
  config:
    description:
      - The C(config) argument allows the playbook designer to supply
        the base configuration to be used to validate configuration
        changes necessary.  If this argument is provided, the module
        will not download the running-config from the remote node.
    required: false
    default: null
  defaults:
    description:
      - This argument specifies whether or not to collect all defaults
        when getting the remote device running config.  When enabled,
        the module will get the current config by issuing the command
        C(show running-config all).
    required: false
    default: no
    choices: ['yes', 'no']
  passwords:
    description:
      - This argument specifies to include passwords in the config
        when retrieving the running-config from the remote device.  This
        includes passwords related to VPN endpoints.  This argument is
        mutually exclusive with I(defaults).
    required: false
    default: no
    choices: ['yes', 'no']
  save:
    description:
      - The C(save) argument instructs the module to save the running-
        config to the startup-config at the conclusion of the module
        running.  If check mode is specified, this argument is ignored.
    required: false
    default: no
    choices: ['yes', 'no']
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
    authorize: yes
    auth_pass: cisco
    transport: cli

---
- asa_config:
    lines:
      - network-object host 10.80.30.18
      - network-object host 10.80.30.19
      - network-object host 10.80.30.20
    parents: ['object-group network OG-MONITORED-SERVERS']
    provider: "{{ cli }}"

- asa_config:
    host: "{{ inventory_hostname }}"
    lines:
      - message-length maximum client auto
      - message-length maximum 512
    match: line
    parents: ['policy-map type inspect dns PM-DNS', 'parameters']
    authorize: yes
    auth_pass: cisco
    username: admin
    password: cisco
    context: ansible

- asa_config:
    lines:
      - ikev1 pre-shared-key MyS3cretVPNK3y
    parents: tunnel-group 1.1.1.1 ipsec-attributes
    passwords: yes
    provider: "{{ cli }}"

"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['...', '...']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: string
  sample: /playbooks/ansible/backup/asa_config.2016-07-16@22:28:34
responses:
  description: The set of responses from issuing the commands on the device
  returned: when not check_mode
  type: list
  sample: ['...', '...']
"""
import traceback

from ansible.module_utils.network import NetworkModule, NetworkError
from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.module_utils._text import to_native


def get_config(module):
    contents = module.params['config']
    if not contents:
        if module.params['defaults']:
            include = 'defaults'
        elif module.params['passwords']:
            include = 'passwords'
        else:
            include = None
        contents = module.config.get_config(include=include)
    return NetworkConfig(indent=1, contents=contents)

def get_candidate(module):
    candidate = NetworkConfig(indent=1)
    if module.params['src']:
        candidate.load(module.params['src'])
    elif module.params['lines']:
        parents = module.params['parents'] or list()
        candidate.add(module.params['lines'], parents=parents)
    return candidate

def run(module, result):
    match = module.params['match']
    replace = module.params['replace']
    path = module.params['parents']

    candidate = get_candidate(module)

    if match != 'none':
        config = get_config(module)
        configobjs = candidate.difference(config, path=path, match=match,
                                          replace=replace)
    else:
        configobjs = candidate.items

    if configobjs:
        commands = dumps(configobjs, 'commands').split('\n')

        if module.params['lines']:
            if module.params['before']:
                commands[:0] = module.params['before']

            if module.params['after']:
                commands.extend(module.params['after'])

        result['updates'] = commands

        # send the configuration commands to the device and merge
        # them with the current running config
        if not module.check_mode:
            result['responses'] = module.config.load_config(commands)
        result['changed'] = True

    if module.params['save']:
        if not module.check_mode:
            module.config.save_config()
        result['changed'] = True

def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        src=dict(type='path'),

        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block']),

        config=dict(),
        defaults=dict(type='bool', default=False),
        passwords=dict(type='bool', default=False),

        backup=dict(type='bool', default=False),
        save=dict(type='bool', default=False),
    )

    mutually_exclusive = [('lines', 'src'), ('defaults', 'passwords')]

    required_if = [('match', 'strict', ['lines']),
                   ('match', 'exact', ['lines']),
                   ('replace', 'block', ['lines'])]

    module = NetworkModule(argument_spec=argument_spec,
                           connect_on_load=False,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    result = dict(changed=False)

    if module.params['backup']:
        result['__backup__'] = module.config.get_config()

    try:
        run(module, result)
    except NetworkError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc(), **e.kwargs)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
