#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_login
short_description: Login to ACI to get a token
description:
- Logs into ACI and returns a token which can be used when working with the other ACI modules.
author:
- Patrick Ogenstad (@ogenstad)
version_added: '2.6'
options:
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Login
  aci_login:
    host: apic
    username: admin
    password: SomeSecretPassword
  register: token

- name: Remove a tenant
  aci_tenant:
    host: apic
    token: '{{ token.aci_token }}'
    tenant: production
    state: absent
'''

RETURN = r'''
aci_token:
  description: The authentication token from a successful login.
  returned: success
  type: string
  sample: APIC-cookie=6y+wLG1kIkICqvp84LNQ; path=/; HttpOnly; HttpOnly; Secure
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    aci = ACIModule(module)
    aci_token = aci.headers['Cookie']

    module.exit_json(aci_token=aci_token)


if __name__ == "__main__":
    main()
