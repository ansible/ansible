#!/usr/bin/python
#
# Copyright (C) 2017 Lenovo, Inc.
# (c) 2017, Ansible by Red Hat, inc
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
# Module to send banner commands to Lenovo Switches
# Two types of banners are supported login and motd
# Lenovo Networking
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: cnos_banner
version_added: "2.8"
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage multiline banners on Lenovo CNOS devices
description:
  - This will configure both login and motd banners on remote devices
    running Lenovo CNOS.  It allows playbooks to add or remote
    banner text from the active running configuration.
notes:
  - Tested against CNOS 10.8.1
options:
  banner:
    description:
      - Specifies which banner should be configured on the remote device.
        In Ansible 2.8 and earlier only I(login) and I(motd) were supported.
    required: true
    choices: ['login', 'motd']
  text:
    description:
      - The banner text that should be
        present in the remote device running configuration.  This argument
        accepts a multiline string, with no empty lines. Requires
        I(state=present).
  state:
    description:
      - Specifies whether or not the configuration is
        present in the current devices active running configuration.
    default: present
    choices: ['present', 'absent']
  provider:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using
         C(connection: network_cli)."
      - For more information please see the
        L(CNOS Platform Options guide, ../network/user_guide/platform_cnos.html).
      - HORIZONTALLINE
      - A dict object containing connection details.
    version_added: "2.8"
    suboptions:
      host:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            device over the specified transport.  The value of host is used as
            the destination address for the transport.
        required: true
      port:
        description:
          - Specifies the port to use when building the connection to the
            remote device.
        default: 22
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote device.  This value is used to authenticate
            the SSH session. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_USERNAME) will be used
            instead.
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote device.   This value is used to authenticate
            the SSH session. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_PASSWORD) will be used
            instead.
      timeout:
        description:
          - Specifies the timeout in seconds for communicating with the network
            device for either connecting or sending commands.  If the timeout
            is exceeded before the operation is completed, the module will
            error.
        default: 10
      ssh_keyfile:
        description:
          - Specifies the SSH key to use to authenticate the connection to
            the remote device.   This value is the path to the
            key used to authenticate the SSH session. If the value is not
            specified in the task, the value of environment variable
            C(ANSIBLE_NET_SSH_KEYFILE)will be used instead.
      authorize:
        description:
          - Instructs the module to enter privileged mode on the remote device
            before sending any commands.  If not specified, the device will
            attempt to execute all commands in non-privileged mode. If the
            value is not specified in the task, the value of environment
            variable C(ANSIBLE_NET_AUTHORIZE) will be used instead.
        type: bool
        default: 'no'
      auth_pass:
        description:
          - Specifies the password to use if required to enter privileged mode
            on the remote device.  If I(authorize) is false, then this argument
            does nothing. If the value is not specified in the task, the value
            of environment variable C(ANSIBLE_NET_AUTH_PASS) will be used
            instead.
"""

EXAMPLES = """
- name: configure the login banner
  cnos_banner:
    banner: login
    text: |
      this is my login banner
      that contains a multiline
      string
    state: present

- name: remove the motd banner
  cnos_banner:
    banner: motd
    state: absent

- name: Configure banner from file
  cnos_banner:
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
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network.cnos.cnos import load_config, run_commands
from ansible.module_utils.network.cnos.cnos import check_args
from ansible.module_utils.network.cnos.cnos import cnos_argument_spec
from ansible.module_utils._text import to_text
import re


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    state = module.params['state']

    if state == 'absent' and 'text' in have.keys() and have['text']:
        commands.append('no banner %s' % module.params['banner'])

    elif state == 'present':
        if want['text'] and (want['text'] != have.get('text')):
            banner_cmd = 'banner %s ' % module.params['banner']
            for bline in want['text'].strip().splitlines():
                final_cmd = banner_cmd + bline.strip()
                commands.append(final_cmd)

    return commands


def map_config_to_obj(module):
    rc, out, err = exec_command(module,
                                'show banner %s' % module.params['banner'])
    if rc == 0:
        output = out
    else:
        rc, out, err = exec_command(module,
                                    'show running-config | include banner %s'
                                    % module.params['banner'])
        if out:
            output = re.search(r'\^C(.*)\^C', out, re.S).group(1).strip()
        else:
            output = None
    obj = {'banner': module.params['banner'], 'state': 'absent'}
    if output:
        obj['text'] = output
        obj['state'] = 'present'
    return obj


def map_params_to_obj(module):
    text = module.params['text']
    if text:
        text = to_text(text).strip()

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

    argument_spec.update(cnos_argument_spec)

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
        if not module.check_mode:
            response = load_config(module, commands)

        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
