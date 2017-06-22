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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: junos_banner
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage multiline banners on Juniper JUNOS devices
description:
  - This will configure both login and motd banners on network devices.
    It allows playbooks to add or remote
    banner text from the active running configuration.
options:
  banner:
    description:
      - Specifies which banner that should be
        configured on the remote device. Value C(login) indicates
        system login message prior to authenticating, C(motd) is login
        announcement after successful authentication.
    required: true
    choices: ['login', 'motd']
  text:
    description:
      - The banner text that should be
        present in the remote device running configuration.  This argument
        accepts a multiline string, with no empty lines. Requires I(state=present).
    default: null
  state:
    description:
      - Specifies whether or not the configuration is
        present in the current devices active running configuration.
    default: present
    choices: ['present', 'absent', 'active', 'suspend']
requirements:
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed
"""

EXAMPLES = """
- name: configure the login banner
  junos_banner:
    banner: login
    text: |
      this is my login banner
      that contains a multiline
      string
    state: present

- name: remove the motd banner
  junos_banner:
    banner: motd
    state: absent

- name: deactivate the motd banner
  junos_banner:
    banner: motd
    state: suspend

- name: activate the motd banner
  junos_banner:
    banner: motd
    state: active

- name: Configure banner from file
  junos_banner:
    banner:  motd
    text: "{{ lookup('file', './config_partial/raw_banner.cfg') }}"
    state: present
"""

RETURN = """
rpc:
  description: load-configuration RPC send to the device
  returned: when configuration is changed on device
  type: string
  sample: >
          <system>
            <login>
                <message>this is my login banner</message>
            </login>
          </system>"
"""
import collections

from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import load_config, map_params_to_obj, map_obj_to_ele

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring

USE_PERSISTENT_CONNECTION = True


def validate_param_values(module, obj):
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(module.params.get(key), module)


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        banner=dict(required=True, choices=['login', 'motd']),
        text=dict(),
        state=dict(default='present', choices=['present', 'absent', 'active', 'suspend'])
    )

    argument_spec.update(junos_argument_spec)

    required_if = [('state', 'present', ('text',))]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    top = 'system/login'

    param_to_xpath_map = collections.OrderedDict()

    param_to_xpath_map.update({
        'text': {'xpath': 'message' if module.params['banner'] == 'login' else 'announcement',
                 'leaf_only': True}
    })

    validate_param_values(module, param_to_xpath_map)

    want = list()
    want.append(map_params_to_obj(module, param_to_xpath_map))
    ele = map_obj_to_ele(module, want, top)

    kwargs = {'commit': not module.check_mode}
    kwargs['action'] = 'replace'

    diff = load_config(module, tostring(ele), warnings, **kwargs)

    if diff:
        result.update({
            'changed': True,
            'diff': {'prepared': diff},
            'rpc': tostring(ele)
        })

    module.exit_json(**result)

if __name__ == "__main__":
    main()
