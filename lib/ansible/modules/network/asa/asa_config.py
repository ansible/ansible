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
    aliases: ['commands']
  parents:
    description:
      - The ordered set of parents that uniquely identify the section or hierarchy
        the commands should be checked against.  If the parents argument
        is omitted, the commands are checked against the set of top
        level or global commands.
  src:
    description:
      - Specifies the source path to the file that contains the configuration
        or configuration template to load.  The path to the source file can
        either be the full path on the Ansible control host or a relative
        path from the playbook or role root directory.  This argument is mutually
        exclusive with I(lines), I(parents).
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
        stack if a change needs to be made.  Just like with I(before) this
        allows the playbook designer to append a set of commands to be
        executed after the command set.
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
    default: line
    choices: ['line', 'block']
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made. If the C(backup_options) value is not given,
        the backup file is written to the C(backup) folder in the
        playbook root directory. If the directory does not exist, it is created.
    type: bool
    default: 'no'
  config:
    description:
      - The C(config) argument allows the playbook designer to supply
        the base configuration to be used to validate configuration
        changes necessary.  If this argument is provided, the module
        will not download the running-config from the remote node.
  defaults:
    description:
      - This argument specifies whether or not to collect all defaults
        when getting the remote device running config.  When enabled,
        the module will get the current config by issuing the command
        C(show running-config all).
    type: bool
    default: 'no'
  passwords:
    description:
      - This argument specifies to include passwords in the config
        when retrieving the running-config from the remote device.  This
        includes passwords related to VPN endpoints.  This argument is
        mutually exclusive with I(defaults).
    type: bool
    default: 'no'
  save:
    description:
      - The C(save) argument instructs the module to save the running-
        config to the startup-config at the conclusion of the module
        running.  If check mode is specified, this argument is ignored.
    type: bool
    default: 'no'
  backup_options:
    description:
      - This is a dict object containing configurable options related to backup file path.
        The value of this option is read only when C(backup) is set to I(yes), if C(backup) is set
        to I(no) this option will be silently ignored.
    suboptions:
      filename:
        description:
          - The filename to be used to store the backup configuration. If the the filename
            is not given it will be generated based on the hostname, current time and date
            in format defined by <hostname>_config.<current-date>@<current-time>
      dir_path:
        description:
          - This option provides the path ending with directory name in which the backup
            configuration file will be stored. If the directory does not exist it will be first
            created and the filename is either the value of C(filename) or default filename
            as described in C(filename) options description. If the path value is not given
            in that case a I(backup) directory will be created in the current working directory
            and backup configuration will be copied in C(filename) within I(backup) directory.
        type: path
    type: dict
    version_added: "2.8"
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

- name: attach ASA acl on interface vlan13/nameif cloud13
  asa_config:
    lines:
      - access-group cloud-acl_access_in in interface cloud13
    provider: "{{ cli }}"

- name: configure ASA (>=9.2) default BGP
  asa_config:
    lines:
      - bgp log-neighbor-changes
      - bgp bestpath compare-routerid
    provider: "{{ cli }}"
    parents:
      - router bgp 65002
  register: bgp
  when: bgp_default_config is defined

- name: configure ASA (>=9.2) BGP neighbor in default/single context mode
  asa_config:
    lines:
      - "bgp router-id {{ bgp_router_id }}"
      - "neighbor {{ bgp_neighbor_ip }} remote-as {{ bgp_neighbor_as }}"
      - "neighbor {{ bgp_neighbor_ip }} description {{ bgp_neighbor_name }}"
    provider: "{{ cli }}"
    parents:
      - router bgp 65002
      - address-family ipv4 unicast
  register: bgp
  when: bgp_neighbor_as is defined

- name: configure ASA interface with standby
  asa_config:
    lines:
      - description my cloud interface
      - nameif cloud13
      - security-level 50
      - ip address 192.168.13.1 255.255.255.0 standby 192.168.13.2
    provider: "{{ cli }}"
    parents: ["interface Vlan13"]
  register: interface

- name: Show changes to interface from task above
  debug:
    var: interface

- name: configurable backup path
  asa_config:
    lines:
      - access-group cloud-acl_access_in in interface cloud13
    provider: "{{ cli }}"
    backup: yes
    backup_options:
      filename: backup.cfg
      dir_path: /home/user
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
  type: str
  sample: /playbooks/ansible/backup/asa_config.2016-07-16@22:28:34
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.asa.asa import asa_argument_spec, check_args
from ansible.module_utils.network.asa.asa import get_config, load_config, run_commands
from ansible.module_utils.network.common.config import NetworkConfig, dumps
from ansible.module_utils._text import to_native


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
        contents = module.params['config']
        if not contents:
            contents = get_config(module)
            config = NetworkConfig(indent=1, contents=contents)
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
            load_config(module, commands)
        result['changed'] = True

    if module.params['save']:
        if not module.check_mode:
            run_commands(module, 'write mem')
        result['changed'] = True


def main():
    """ main entry point for module execution
    """
    backup_spec = dict(
        filename=dict(),
        dir_path=dict(type='path')
    )
    argument_spec = dict(
        src=dict(type='path'),

        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block']),
        backup_options=dict(type='dict', options=backup_spec),

        config=dict(),
        defaults=dict(type='bool', default=False),
        passwords=dict(type='bool', default=False),

        backup=dict(type='bool', default=False),
        save=dict(type='bool', default=False),
    )

    argument_spec.update(asa_argument_spec)

    mutually_exclusive = [('lines', 'src'),
                          ('parents', 'src'),
                          ('defaults', 'passwords')]

    required_if = [('match', 'strict', ['lines']),
                   ('match', 'exact', ['lines']),
                   ('replace', 'block', ['lines'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    result = {'changed': False}

    check_args(module)

    config = None

    if module.params['backup']:
        result['__backup__'] = get_config(module)

    run(module, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
