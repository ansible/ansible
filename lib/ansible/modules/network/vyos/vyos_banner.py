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
module: vyos_banner
version_added: "2.4"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage multiline banners on VyOS devices
description:
  - This will configure both pre-login and post-login banners on remote
    devices running VyOS. It allows playbooks to add or remote
    banner text from the active running configuration.
notes:
  - Tested against VyOS 1.1.8 (helium).
  - This module works with connection C(network_cli). See L(the VyOS OS Platform Options,../network/user_guide/platform_vyos.html).
options:
  banner:
    description:
      - Specifies which banner that should be
        configured on the remote device.
    required: true
    choices: ['pre-login', 'post-login']
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
extends_documentation_fragment: vyos
"""

EXAMPLES = """
- name: configure the pre-login banner
  vyos_banner:
    banner: pre-login
    text: |
      this is my pre-login banner
      that contains a multiline
      string
    state: present
- name: remove the post-login banner
  vyos_banner:
    banner: post-login
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - banner pre-login
    - this is my pre-login banner
    - that contains a multiline
    - string
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.vyos.vyos import get_config, load_config
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec


def spec_to_commands(updates, module):
    commands = list()
    want, have = updates
    state = module.params['state']

    if state == 'absent':
        if have.get('state') != 'absent' or (have.get('state') != 'absent' and
                                             'text' in have.keys() and have['text']):
            commands.append('delete system login banner %s' % module.params['banner'])

    elif state == 'present':
        if want['text'] and want['text'].encode().decode('unicode_escape') != have.get('text'):
            banner_cmd = 'set system login banner %s ' % module.params['banner']
            banner_cmd += want['text'].strip()
            commands.append(banner_cmd)

    return commands


def config_to_dict(module):
    data = get_config(module)
    output = None
    obj = {'banner': module.params['banner'], 'state': 'absent'}

    for line in data.split('\n'):
        if line.startswith('set system login banner %s' % obj['banner']):
            match = re.findall(r'%s (.*)' % obj['banner'], line, re.M)
            output = match
    if output:
        obj['text'] = output[0].encode().decode('unicode_escape')
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
        banner=dict(required=True, choices=['pre-login', 'post-login']),
        text=dict(),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(vyos_argument_spec)

    required_if = [('state', 'present', ('text',))]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = config_to_dict(module)

    commands = spec_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        load_config(module, commands, commit=commit)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
