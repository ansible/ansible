#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ingate Systems AB
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ingate_operational_mode
short_description: Set mode to siparator or firewall.
description:
  - Set mode to siparator or firewall. Requires a reboot to be applied.
version_added: 2.8
extends_documentation_fragment: ingate
options:
  mode:
    description:
      - The operational mode.
    choices: [siparator, firewall]
    required: true
notes:
  - On change, a reboot is required in order for the change to take effect.
author:
  - Ingate Systems AB (@ingatesystems)
'''

EXAMPLES = '''
- name: Set operational mode to siparator
  ingate_operational_mode:
    client:
      version: v1
      scheme: http
      address: 192.168.1.1
      username: alice
      password: foobar
    mode: siparator
'''

RETURN = '''
operational-mode:
  description: The status of the operational mode change
  returned: success
  type: complex
  contains:
    msg:
      description: The command status message
      returned: success
      type: string
      sample: Operational mode set to siparator.
'''

try:
    from ingate import ingatesdk
    HAS_INGATESDK = True
except ImportError:
    HAS_INGATESDK = False


def main():
    argument_spec = ingate_argument_spec(
        mode=dict(type='str', choices=['siparator', 'firewall'], required=True)
    )
    mutually_exclusive = []
    required_if = []
    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=False)
    if not HAS_INGATESDK:
        module.fail_json(msg='The Ingate Python SDK module is required')

    result = dict(changed=False)
    try:
        # Create client and authenticate.
        api_client = ingate_create_client(**module.params)

        # Get the current operational mode.
        mode = module.params['mode']
        response = api_client.unit_information()
        info = response[0].get('unit-information')
        if info:
            if info['mode'].lower() == mode.lower():
                result.update(
                    {'operational-mode':
                     {'msg': 'Operational mode is already %s.' % mode}})
                module.exit_json(**result)

        # Change the operational mode.
        response = api_client.operational_mode(mode=mode)
        result.update(response[0])
        result['changed'] = True

    except ingatesdk.SdkError as e:
        module.fail_json(msg=str(e))
    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.network.ingate.common import *

if __name__ == '__main__':
    main()
