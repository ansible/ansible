#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: awplus_banner
author: Cheng Yi Kok (@cyk19)
short_description: Manage multiline banners on AlliedWare Plus devices
description:
  - This will configure both login and motd banners on remote devices
    running AlliedWare Plus.  It allows playbooks to add or remote
    banner text from the active running configuration.
version_added: "2.10"
options:
  banner:
    description:
      - Specifies which banner should be configured on the remote device.
        In Ansible 2.4 and earlier only I(login) and I(motd) were supported.
    required: true
    choices: ['motd', 'exec']
  text:
    description:
      - The banner text that should be
        present in the remote device running configuration.  This argument
        accepts a multiline string, with no empty lines. Requires I(state=present).
  state:
    description:
      - Specifies whether or not the configuration is
        present in the current devices active running configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
      - name: configure motd banner
        awplus_banner:
          banner: motd
          text: Configured by Ansible
          state: present

      - name: remove motd banner
        awplus_banner:
          banner: motd
          state: absent

      - name: Configure banner from file
        awplus_banner:
          banner: exec
          text: "{{ lookup('file', './raw_banner.cfg') }}"
          state: present
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - ["banner motd Configured by Ansible"]
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.awplus.awplus import get_config, load_config
from ansible.module_utils.network.awplus.awplus import awplus_argument_spec


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    state = module.params['state']

    if state == 'absent' and 'text' in have.keys() and have['text']:
        commands.append('no banner %s' % module.params['banner'])

    elif state == 'present':
        if want['text'] and (want['text'] != have.get('text')):
            banner_cmd = 'banner %s ' % module.params['banner']
            banner_cmd += want['text']
            commands.append(banner_cmd)

    return commands


def map_config_to_obj(module):
    """
    This function gets the banner config without stripping any whitespaces,
    and then fetches the required banner from it.
    :param module:
    :return: banner config dict object.
    """
    out = get_config(module, flags='| begin banner %s' % module.params['banner'])
    if out:
        regex = 'banner ' + module.params['banner'] + ' (.+)'
        match = re.search(regex, out, re.M)
        if match:
            output = match.group(1).strip()
        else:
            output = None
    else:
        output = None
    obj = {'banner': module.params['banner'], 'state': 'absent'}
    if output:
        obj['text'] = output
        obj['state'] = 'present'
    return obj


def map_params_to_obj(module):
    text = module.params['text']
    return {
        'banner': module.params['banner'],
        'text': text,
        'state': module.params['state']
    }


def main():
    """
    main entry point for module execution
    """
    argument_spec = dict(
        banner=dict(required=True, choices=['motd', 'exec']),
        text=dict(),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(awplus_argument_spec)

    required_if = [('state', 'present', ('text',))]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings
    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)

        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
