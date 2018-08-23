#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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
module: nxos_banner
version_added: "2.4"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage multiline banners on Cisco NXOS devices
description:
  - This will configure both exec and motd banners on remote devices
    running Cisco NXOS. It allows playbooks to add or remote
    banner text from the active running configuration.
options:
  banner:
    description:
      - Specifies which banner that should be
        configured on the remote device.
    required: true
    choices: ['exec', 'motd']
  text:
    description:
      - The banner text that should be
        present in the remote device running configuration. This argument
        accepts a multiline string, with no empty lines. Requires I(state=present).
  state:
    description:
      - Specifies whether or not the configuration is present in the current
        devices active running configuration.
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: nxos
"""

EXAMPLES = """
- name: configure the exec banner
  nxos_banner:
    banner: exec
    text: |
      this is my exec banner
      that contains a multiline
      string
    state: present
- name: remove the motd banner
  nxos_banner:
    banner: motd
    state: absent
- name: Configure banner from file
  nxos_banner:
    banner:  motd
    text: "{{ lookup('file', './config_partial/raw_banner.cfg') }}"
    state: present
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - banner exec
    - this is my exec banner
    - that contains a multiline
    - string
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
import re


def execute_show_command(module, command):
    format = 'json'
    cmds = [{
        'command': command,
        'output': format,
    }]
    output = run_commands(module, cmds, check_rc='retry_json')
    return output


def map_obj_to_commands(want, have, module):
    commands = list()
    state = module.params['state']
    platform_regex = 'Nexus.*Switch'

    if state == 'absent':
        if (have.get('text') and not ((have.get('text') == 'User Access Verification') or re.match(platform_regex, have.get('text')))):
            commands.append('no banner %s' % module.params['banner'])

    elif state == 'present' and want.get('text') != have.get('text'):
        banner_cmd = 'banner %s @\n%s\n@' % (module.params['banner'], want['text'].strip())
        commands.append(banner_cmd)

    return commands


def map_config_to_obj(module):
    command = 'show banner %s' % module.params['banner']
    output = execute_show_command(module, command)[0]

    if "Invalid command" in output:
        module.fail_json(msg="banner: %s may not be supported on this platform.  Possible values are : exec | motd" % module.params['banner'])

    if isinstance(output, dict):
        output = list(output.values())
        if output != []:
            output = output[0]
        else:
            output = ''
        if isinstance(output, dict):
            output = list(output.values())
            if output != []:
                output = output[0]
            else:
                output = ''
    else:
        output = output.rstrip()

    obj = {'banner': module.params['banner'], 'state': 'absent'}
    if output:
        obj['text'] = output
        obj['state'] = 'present'
    return obj


def map_params_to_obj(module):
    text = module.params['text']
    if text:
        text = str(text).strip()

    return {
        'banner': module.params['banner'],
        'text': text,
        'state': module.params['state']
    }


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        banner=dict(required=True, choices=['exec', 'motd']),
        text=dict(),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(nxos_argument_spec)

    required_if = [('state', 'present', ('text',))]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()

    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings
    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            msgs = load_config(module, commands, True)
            if msgs:
                for item in msgs:
                    if item:
                        if isinstance(item, dict):
                            err_str = item['clierror']
                        else:
                            err_str = item
                        if 'more than 40 lines' in err_str or 'buffer overflowed' in err_str:
                            load_config(module, commands)

        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
