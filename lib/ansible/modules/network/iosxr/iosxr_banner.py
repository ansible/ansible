#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = """
---
module: iosxr_banner
version_added: "2.4"
author: "Trishna Guha (@trishnag)"
short_description: Manage multiline banners on Cisco IOS XR devices
description:
  - This will configure both exec and motd banners on remote devices
    running Cisco IOS XR. It allows playbooks to add or remote
    banner text from the active running configuration.
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
        present in the remote device running configuration. This argument
        accepts a multiline string, with no empty lines. Requires I(state=present).
    default: null
  state:
    description:
      - Specifies whether or not the configuration is present in the current
        devices active running configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure the login banner
  iosxr_banner:
    banner: login
    text: |
      this is my login banner
      that contains a multiline
      string
    state: present
- name: remove the motd banner
  iosxr_banner:
    banner: motd
    state: absent
- name: Configure banner from file
  iosxr_banner:
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
    - banner login
    - this is my login banner
    - that contains a multiline
    - string
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.iosxr import get_config, load_config
from ansible.module_utils.iosxr import iosxr_argument_spec, check_args


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    state = module.params['state']

    if state == 'absent':
        if have.get('state') != 'absent' and ('text' in have.keys() and have['text']):
            commands.append('no banner %s' % module.params['banner'])

    elif state == 'present':
        if (want['text'] and
                want['text'].encode().decode('unicode_escape').strip("'") != have.get('text')):
            banner_cmd = 'banner %s ' % module.params['banner']
            banner_cmd += want['text'].strip()
            commands.append(banner_cmd)

    return commands


def map_config_to_obj(module):
    flags = 'banner %s' % module.params['banner']
    output = get_config(module, flags=[flags])

    match = re.search(r'banner (\S+) (.*)', output, re.DOTALL)
    if match:
        text = match.group(2).strip("'")
    else:
        text = None

    obj = {'banner': module.params['banner'], 'state': 'absent'}

    if output:
        obj['text'] = text
        obj['state'] = 'present'

    return obj


def map_params_to_obj(module):
    text = module.params['text']
    if text:
        text = "%r" % (str(text).strip())

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

    argument_spec.update(iosxr_argument_spec)

    required_if = [('state', 'present', ('text',))]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands, result['warnings'], commit=True)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
