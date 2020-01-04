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


DOCUMENTATION = """
---
module: vyos_config
version_added: "2.2"
author: "Nathaniel Case (@Qalthos)"
short_description: Manage VyOS configuration on remote device
description:
  - This module provides configuration file management of VyOS
    devices. It provides arguments for managing both the
    configuration file and state of the active configuration. All
    configuration statements are based on `set` and `delete` commands
    in the device configuration.
extends_documentation_fragment: vyos
notes:
  - Tested against VyOS 1.1.8 (helium).
  - This module works with connection C(network_cli). See L(the VyOS OS Platform Options,../network/user_guide/platform_vyos.html).
options:
  lines:
    description:
      - The ordered set of configuration lines to be managed and
        compared with the existing configuration on the remote
        device.
  src:
    description:
      - The C(src) argument specifies the path to the source config
        file to load.  The source config file can either be in
        bracket format or set format.  The source file can include
        Jinja2 template variables.
  match:
    description:
      - The C(match) argument controls the method used to match
        against the current active configuration.  By default, the
        desired config is matched against the active config and the
        deltas are loaded.  If the C(match) argument is set to C(none)
        the active configuration is ignored and the configuration is
        always loaded.
    default: line
    choices: ['line', 'none']
  backup:
    description:
      - The C(backup) argument will backup the current devices active
        configuration to the Ansible control host prior to making any
        changes. If the C(backup_options) value is not given, the
        backup file will be located in the backup folder in the playbook
        root directory or role root directory, if playbook is part of an
        ansible role. If the directory does not exist, it is created.
    type: bool
    default: 'no'
  comment:
    description:
      - Allows a commit description to be specified to be included
        when the configuration is committed.  If the configuration is
        not changed or committed, this argument is ignored.
    default: 'configured by vyos_config'
  config:
    description:
      - The C(config) argument specifies the base configuration to use
        to compare against the desired configuration.  If this value
        is not specified, the module will automatically retrieve the
        current active configuration from the remote device.
  save:
    description:
      - The C(save) argument controls whether or not changes made
        to the active configuration are saved to disk.  This is
        independent of committing the config.  When set to True, the
        active configuration is saved.
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
- name: configure the remote device
  vyos_config:
    lines:
      - set system host-name {{ inventory_hostname }}
      - set service lldp
      - delete service dhcp-server

- name: backup and load from file
  vyos_config:
    src: vyos.cfg
    backup: yes

- name: render a Jinja2 template onto the VyOS router
  vyos_config:
    src: vyos_template.j2

- name: for idempotency, use full-form commands
  vyos_config:
    lines:
      # - set int eth eth2 description 'OUTSIDE'
      - set interface ethernet eth2 description 'OUTSIDE'

- name: configurable backup path
  vyos_config:
    backup: yes
    backup_options:
      filename: backup.cfg
      dir_path: /home/user
"""

RETURN = """
commands:
  description: The list of configuration commands sent to the device
  returned: always
  type: list
  sample: ['...', '...']
filtered:
  description: The list of configuration commands removed to avoid a load failure
  returned: always
  type: list
  sample: ['...', '...']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: str
  sample: /playbooks/ansible/backup/vyos_config.2016-07-16@22:28:34
filename:
  description: The name of the backup file
  returned: when backup is yes and filename is not specified in backup options
  type: str
  sample: vyos_config.2016-07-16@22:28:34
shortname:
  description: The full path to the backup file excluding the timestamp
  returned: when backup is yes and filename is not specified in backup options
  type: str
  sample: /playbooks/ansible/backup/vyos_config
date:
  description: The date extracted from the backup file name
  returned: when backup is yes
  type: str
  sample: "2016-07-16"
time:
  description: The time extracted from the backup file name
  returned: when backup is yes
  type: str
  sample: "22:28:34"
"""
import re

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.vyos.vyos import load_config, get_config, run_commands
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec, get_connection


DEFAULT_COMMENT = 'configured by vyos_config'

CONFIG_FILTERS = [
    re.compile(r'set system login user \S+ authentication encrypted-password')
]


def get_candidate(module):
    contents = module.params['src'] or module.params['lines']

    if module.params['src']:
        contents = format_commands(contents.splitlines())

    contents = '\n'.join(contents)
    return contents


def format_commands(commands):
    return [line for line in commands if len(line.strip()) > 0]


def diff_config(commands, config):
    config = [str(c).replace("'", '') for c in config.splitlines()]

    updates = list()
    visited = set()

    for line in commands:
        item = str(line).replace("'", '')

        if not item.startswith('set') and not item.startswith('delete'):
            raise ValueError('line must start with either `set` or `delete`')

        elif item.startswith('set') and item not in config:
            updates.append(line)

        elif item.startswith('delete'):
            if not config:
                updates.append(line)
            else:
                item = re.sub(r'delete', 'set', item)
                for entry in config:
                    if entry.startswith(item) and line not in visited:
                        updates.append(line)
                        visited.add(line)

    return list(updates)


def sanitize_config(config, result):
    result['filtered'] = list()
    index_to_filter = list()
    for regex in CONFIG_FILTERS:
        for index, line in enumerate(list(config)):
            if regex.search(line):
                result['filtered'].append(line)
                index_to_filter.append(index)
    # Delete all filtered configs
    for filter_index in sorted(index_to_filter, reverse=True):
        del config[filter_index]


def run(module, result):
    # get the current active config from the node or passed in via
    # the config param
    config = module.params['config'] or get_config(module)

    # create the candidate config object from the arguments
    candidate = get_candidate(module)

    # create loadable config that includes only the configuration updates
    connection = get_connection(module)
    try:
        response = connection.get_diff(candidate=candidate, running=config, diff_match=module.params['match'])
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

    commands = response.get('config_diff')
    sanitize_config(commands, result)

    result['commands'] = commands

    commit = not module.check_mode
    comment = module.params['comment']

    diff = None
    if commands:
        diff = load_config(module, commands, commit=commit, comment=comment)

        if result.get('filtered'):
            result['warnings'].append('Some configuration commands were '
                                      'removed, please see the filtered key')

        result['changed'] = True

    if module._diff:
        result['diff'] = {'prepared': diff}


def main():
    backup_spec = dict(
        filename=dict(),
        dir_path=dict(type='path')
    )
    argument_spec = dict(
        src=dict(type='path'),
        lines=dict(type='list'),

        match=dict(default='line', choices=['line', 'none']),

        comment=dict(default=DEFAULT_COMMENT),

        config=dict(),

        backup=dict(type='bool', default=False),
        backup_options=dict(type='dict', options=backup_spec),
        save=dict(type='bool', default=False),
    )

    argument_spec.update(vyos_argument_spec)

    mutually_exclusive = [('lines', 'src')]

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True
    )

    warnings = list()

    result = dict(changed=False, warnings=warnings)

    if module.params['backup']:
        result['__backup__'] = get_config(module=module)

    if any((module.params['src'], module.params['lines'])):
        run(module, result)

    if module.params['save']:
        diff = run_commands(module, commands=['configure', 'compare saved'])[1]
        if diff != '[edit]':
            run_commands(module, commands=['save'])
            result['changed'] = True
        run_commands(module, commands=['exit'])

    module.exit_json(**result)


if __name__ == '__main__':
    main()
