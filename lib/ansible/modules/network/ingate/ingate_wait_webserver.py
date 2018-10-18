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
module: ingate_wait_webserver
short_description: Wait for the unit to become available.
description:
  - Wait for the unit to become available after e.g. a reboot or the
    installation of licenses or upgrades.
version_added: 2.8
extends_documentation_fragment: ingate
options:
  timeout:
    description:
      - How long the task should wait.
    default: 120
  consecutive:
    description:
      - How many successful requests that should be made before the unit is
        considered available.
    default: 15
author:
  - Ingate Systems AB (@ingatesystems)
'''

EXAMPLES = '''
- name: Wait until the unit is available
  ingate_wait_webserver:
    client:
      version: v1
      scheme: http
      address: 192.168.1.1
      username: alice
      password: foobar
    timeout: 300
'''

RETURN = ''' # '''

try:
    from ingate import ingatesdk
    HAS_INGATESDK = True
except ImportError:
    HAS_INGATESDK = False


def main():
    argument_spec = ingate_argument_spec(
        timeout=dict(default=120, type=int),
        consecutive=dict(default=15, type=int),
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
        # Create client.
        api_client = ingate_create_client_noauth(**module.params)

        # Wait for the unit to become available.
        timeout = module.params.get('timeout')
        consecutive = module.params.get('consecutive')
        api_client.wait_webserver(timeout=timeout, consecutive=consecutive)

    except ingatesdk.SdkError as e:
        module.fail_json(msg=str(e))
    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.network.ingate.common import *

if __name__ == '__main__':
    main()
