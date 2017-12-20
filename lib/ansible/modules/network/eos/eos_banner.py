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
module: eos_banner
version_added: "2.3"
author: "Peter Sprygada (@privateip)"
short_description: Manage multiline banners on Arista EOS devices
description:
  - This will configure both login and motd banners on remote devices
    running Arista EOS.  It allows playbooks to add or remote
    banner text from the active running configuration.
extends_documentation_fragment: eos
notes:
  - Tested against EOS 4.15
options:
  banner:
    description:
      - Specifies which banner that should be
        configured on the remote device.
    required: true
    default: null
    choices: ['login', 'motd']
  text:
    description:
      - The banner text that should be
        present in the remote device running configuration.  This argument
        accepts a multiline string. Requires I(state=present).
    default: null
  state:
    description:
      - Specifies whether or not the configuration is
        present in the current devices active running configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure the login banner
  eos_banner:
    banner: login
    text: |
      this is my login banner
      that contains a multiline
      string
    state: present

- name: remove the motd banner
  eos_banner:
    banner: motd
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - banner login
    - this is my login banner
    - that contains a multiline
    - string
    - EOF
session_name:
  description: The EOS config session name used to load the configuration
  returned: if changes
  type: str
  sample: ansible_1479315771
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.eos.eos import load_config, run_commands
from ansible.module_utils.network.eos.eos import eos_argument_spec, check_args
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    state = module.params['state']

    if state == 'absent' and have.get('text'):
        if isinstance(have['text'], str):
            commands.append('no banner %s' % module.params['banner'])
        elif have['text'].get('loginBanner') or have['text'].get('motd'):
            commands.append({'cmd': 'no banner %s' % module.params['banner']})

    elif state == 'present':
        if isinstance(have['text'], string_types):
            if want['text'] != have['text']:
                commands.append('banner %s' % module.params['banner'])
                commands.extend(want['text'].strip().split('\n'))
                commands.append('EOF')
        else:
            have_text = have['text'].get('loginBanner') or have['text'].get('motd')
            if have_text:
                have_text = have_text.strip()

            if to_text(want['text']) != have_text or not have_text:
                # For EAPI we need to construct a dict with cmd/input
                # key/values for the banner
                commands.append({'cmd': 'banner %s' % module.params['banner'],
                                 'input': want['text'].strip('\n')})

    return commands


def map_config_to_obj(module):
    output = run_commands(module, ['show banner %s' % module.params['banner']])
    obj = {'banner': module.params['banner'], 'state': 'absent'}
    if output:
        if module.params['transport'] == 'eapi':
            # On EAPI we need to extract the banner text from dict key
            # 'loginBanner'
            if module.params['banner'] == 'login':
                banner_response_key = 'loginBanner'
            else:
                banner_response_key = 'motd'
            if isinstance(output[0], dict) and banner_response_key in output[0].keys():
                obj['text'] = output[0]
        else:
            obj['text'] = output[0]
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
        banner=dict(required=True, choices=['login', 'motd']),
        text=dict(),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(eos_argument_spec)

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

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        response = load_config(module, commands, commit=commit)
        if response.get('diff') and module._diff:
            result['diff'] = {'prepared': response.get('diff')}
        result['session_name'] = response.get('session')
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
