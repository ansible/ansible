#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: icx_banner
version_added: "2.9"
author: "Ruckus Wireless (@Commscope)"
short_description: Manage multiline banners on Ruckus ICX 7000 series switches
description:
  - This will configure both login and motd banners on remote
    ruckus ICX 7000 series switches. It allows playbooks to add or remove
    banner text from the active running configuration.
notes:
  - Tested against ICX 10.1
options:
  banner:
    description:
      - Specifies which banner should be configured on the remote device.
    type: str
    required: true
    choices: ['motd', 'exec', 'incoming']
  text:
    description:
      - The banner text that should be
        present in the remote device running configuration.
        This argument accepts a multiline string, with no empty lines.
    type: str
  state:
    description:
      - Specifies whether or not the configuration is
        present in the current devices active running configuration.
    type: str
    default: present
    choices: ['present', 'absent']
  enterkey:
    description:
      - Specifies whether or not the motd configuration should accept
        the require-enter-key
    type: bool
    default: no
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable.
       Module will use environment variable value(default:True), unless it is overridden,
       by specifying it as module parameter.
    type: bool
    default: yes

"""

EXAMPLES = """
- name: configure the motd banner
  icx_banner:
    banner: motd
    text: |
        this is my motd banner
        that contains a multiline
        string
    state: present

- name: remove the motd banner
  icx_banner:
    banner: motd
    state: absent

- name: configure require-enter-key for motd
  icx_banner:
    banner: motd
    enterkey: True

- name: remove require-enter-key for motd
  icx_banner:
    banner: motd
    enterkey: False
"""

RETURN = """
commands:
 description: The list of configuration mode commands to send to the device
 returned: always
 type: list
 sample:
    - banner motd
    - this is my motd banner
    - that contains a multiline
    - string
"""

import re
from ansible.module_utils._text import to_text
from ansible.module_utils.connection import exec_command
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.icx.icx import load_config, get_config
from ansible.module_utils.connection import Connection, ConnectionError


def map_obj_to_commands(updates, module):
    commands = list()
    state = module.params['state']
    want, have = updates

    if module.params['banner'] != 'motd' and module.params['enterkey']:
        module.fail_json(msg=module.params['banner'] + " banner can have text only, got enterkey")

    if state == 'absent':
        if 'text' in have.keys() and have['text']:
            commands.append('no banner %s' % module.params['banner'])
        if(module.params['enterkey'] is False):
            commands.append('no banner %s require-enter-key' % module.params['banner'])

    elif state == 'present':
        if module.params['text'] is None and module.params['enterkey'] is None:
            module.fail_json(msg=module.params['banner'] + " one of the following is required: text, enterkey:only if motd")

        if module.params["banner"] == "motd" and want['enterkey'] != have['enterkey']:
            if(module.params['enterkey']):
                commands.append('banner %s require-enter-key' % module.params['banner'])

        if want['text'] and (want['text'] != have.get('text')):
            module.params["enterkey"] = None
            banner_cmd = 'banner %s' % module.params['banner']
            banner_cmd += ' $\n'
            banner_cmd += module.params['text'].strip()
            banner_cmd += '\n$'
            commands.append(banner_cmd)
    return commands


def map_config_to_obj(module):
    compare = module.params.get('check_running_config')
    obj = {'banner': module.params['banner'], 'state': 'absent', 'enterkey': False}
    exec_command(module, 'skip')
    output_text = ''
    output_re = ''
    out = get_config(module, flags=['| begin banner %s'
                                    % module.params['banner']], compare=module.params['check_running_config'])
    if out:
        try:
            output_re = re.search(r'banner %s( require-enter-key)' % module.params['banner'], out, re.S).group(0)
            obj['enterkey'] = True
        except BaseException:
            pass
        try:
            output_text = re.search(r'banner %s (\$([^\$])+\$){1}' % module.params['banner'], out, re.S).group(1).strip('$\n')
        except BaseException:
            pass

    else:
        output_text = None
    if output_text:
        obj['text'] = output_text
        obj['state'] = 'present'
    if module.params['check_running_config'] is False:
        obj = {'banner': module.params['banner'], 'state': 'absent', 'enterkey': False, 'text': 'JUNK'}
    return obj


def map_params_to_obj(module):
    text = module.params['text']
    if text:
        text = str(text).strip()

    return {
        'banner': module.params['banner'],
        'text': text,
        'state': module.params['state'],
        'enterkey': module.params['enterkey']
    }


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        banner=dict(required=True, choices=['motd', 'exec', 'incoming']),
        text=dict(),
        enterkey=dict(type='bool'),
        state=dict(default='present', choices=['present', 'absent']),
        check_running_config=dict(default=True, type='bool', fallback=(env_fallback, ['ANSIBLE_CHECK_ICX_RUNNING_CONFIG']))
    )

    required_one_of = [['text', 'enterkey', 'state']]
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           supports_check_mode=True)

    warnings = list()
    results = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands((want, have), module)
    results['commands'] = commands

    if commands:
        if not module.check_mode:
            response = load_config(module, commands)

        results['changed'] = True

    module.exit_json(**results)


if __name__ == '__main__':
    main()
