#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: aci_aaa_user_certificate
short_description: Manage AAA user certificates (aaa:UserCert)
description:
- Manage AAA user certificates on Cisco ACI fabrics.
version_added: '2.5'
options:
  aaa_user:
    description:
    - The name of the user to add a certificate to.
    type: str
    required: yes
  aaa_user_type:
    description:
    - Whether this is a normal user or an appuser.
    type: str
    choices: [ appuser, user ]
    default: user
  certificate:
    description:
    - The PEM format public key extracted from the X.509 certificate.
    type: str
    aliases: [ cert_data, certificate_data ]
  certificate_name:
    description:
    - The name of the user certificate entry in ACI.
    type: str
    aliases: [ cert_name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
notes:
- The C(aaa_user) must exist before using this module in your playbook.
  The M(aci_aaa_user) module can be used for this.
seealso:
- module: aci_aaa_user
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(aaa:UserCert).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Add a certificate to user
  aci_aaa_user_certificate:
    host: apic
    username: admin
    password: SomeSecretPassword
    aaa_user: admin
    certificate_name: admin
    certificate_data: '{{ lookup("file", "pki/admin.crt") }}'
    state: present
  delegate_to: localhost

- name: Remove a certificate of a user
  aci_aaa_user_certificate:
    host: apic
    username: admin
    password: SomeSecretPassword
    aaa_user: admin
    certificate_name: admin
    state: absent
  delegate_to: localhost

- name: Query a certificate of a user
  aci_aaa_user_certificate:
    host: apic
    username: admin
    password: SomeSecretPassword
    aaa_user: admin
    certificate_name: admin
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all certificates of a user
  aci_aaa_user_certificate:
    host: apic
    username: admin
    password: SomeSecretPassword
    aaa_user: admin
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
current:
  description: The existing configuration from the APIC after the module has finished
  returned: success
  type: list
  sample:
    [
        {
            "fvTenant": {
                "attributes": {
                    "descr": "Production environment",
                    "dn": "uni/tn-production",
                    "name": "production",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": ""
                }
            }
        }
    ]
error:
  description: The error information as returned from the APIC
  returned: failure
  type: dict
  sample:
    {
        "code": "122",
        "text": "unknown managed object class foo"
    }
raw:
  description: The raw output returned by the APIC REST API (xml or json)
  returned: parse error
  type: str
  sample: '<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1"><error code="122" text="unknown managed object class foo"/></imdata>'
sent:
  description: The actual/minimal configuration pushed to the APIC
  returned: info
  type: list
  sample:
    {
        "fvTenant": {
            "attributes": {
                "descr": "Production environment"
            }
        }
    }
previous:
  description: The original configuration from the APIC before the module has started
  returned: info
  type: list
  sample:
    [
        {
            "fvTenant": {
                "attributes": {
                    "descr": "Production",
                    "dn": "uni/tn-production",
                    "name": "production",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": ""
                }
            }
        }
    ]
proposed:
  description: The assembled configuration from the user-provided parameters
  returned: info
  type: dict
  sample:
    {
        "fvTenant": {
            "attributes": {
                "descr": "Production environment",
                "name": "production"
            }
        }
    }
filter_string:
  description: The filter string used for the request
  returned: failure or debug
  type: str
  sample: ?rsp-prop-include=config-only
method:
  description: The HTTP method used for the request to the APIC
  returned: failure or debug
  type: str
  sample: POST
response:
  description: The HTTP response from the APIC
  returned: failure or debug
  type: str
  sample: OK (30 bytes)
status:
  description: The HTTP status from the APIC
  returned: failure or debug
  type: int
  sample: 200
url:
  description: The HTTP url used for the request to the APIC
  returned: failure or debug
  type: str
  sample: https://10.11.12.13/api/mo/uni/tn-production.json
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec

ACI_MAPPING = dict(
    appuser=dict(
        aci_class='aaaAppUser',
        aci_mo='userext/appuser-',
    ),
    user=dict(
        aci_class='aaaUser',
        aci_mo='userext/user-',
    ),
)


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        aaa_user=dict(type='str', required=True),
        aaa_user_type=dict(type='str', default='user', choices=['appuser', 'user']),
        certificate=dict(type='str', aliases=['cert_data', 'certificate_data']),
        certificate_name=dict(type='str', aliases=['cert_name']),  # Not required for querying all objects
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['aaa_user', 'certificate_name']],
            ['state', 'present', ['aaa_user', 'certificate', 'certificate_name']],
        ],
    )

    aaa_user = module.params['aaa_user']
    aaa_user_type = module.params['aaa_user_type']
    certificate = module.params['certificate']
    certificate_name = module.params['certificate_name']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class=ACI_MAPPING[aaa_user_type]['aci_class'],
            aci_rn=ACI_MAPPING[aaa_user_type]['aci_mo'] + aaa_user,
            module_object=aaa_user,
            target_filter={'name': aaa_user},
        ),
        subclass_1=dict(
            aci_class='aaaUserCert',
            aci_rn='usercert-{0}'.format(certificate_name),
            module_object=certificate_name,
            target_filter={'name': certificate_name},
        ),
    )
    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='aaaUserCert',
            class_config=dict(
                data=certificate,
                name=certificate_name,
            ),
        )

        aci.get_diff(aci_class='aaaUserCert')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
