#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_aaa_user
short_description: Manage AAA users (aaa:User)
description:
- Manage AAA users on Cisco ACI fabrics.
notes:
- This module is not idempotent when C(aaa_password) is being used
  (even if that password was already set identically). This
  appears to be an inconsistency wrt. the idempotent nature
  of the APIC REST API. The vendor has been informed.
- More information in :ref:`the ACI documentation <aci_guide_known_issues>`.
- More information about the internal APIC class B(aaa:User) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Dag Wieers (@dagwieers)
requirements:
  - python-dateutil
version_added: '2.5'
options:
  aaa_password:
    description:
    - The password of the locally-authenticated user.
  aaa_password_lifetime:
    description:
    - The lifetime of the locally-authenticated user password.
    type: int
  aaa_password_update_required:
    description:
    - Whether this account needs password update.
    type: bool
  aaa_user:
    description:
    - The name of the locally-authenticated user user to add.
    aliases: [ name, user ]
  clear_password_history:
    description:
    - Whether to clear the password history of a locally-authenticated user.
    type: bool
  description:
    description:
    - Description for the AAA user.
    aliases: [ descr ]
  email:
    description:
    - The email address of the locally-authenticated user.
  enabled:
    description:
    - The status of the locally-authenticated user account.
    type: bool
  expiration:
    description:
    - The expiration date of the locally-authenticated user account.
  expires:
    description:
    - Whether to enable an expiration date for the locally-authenticated user account.
    type: bool
  first_name:
    description:
    - The first name of the locally-authenticated user.
  last_name:
    description:
    - The last name of the locally-authenticated user.
  phone:
    description:
    - The phone number of the locally-authenticated user.
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a user
  aci_aaa_user:
    host: apic
    username: admin
    password: SomeSecretPassword
    aaa_user: dag
    aaa_password: AnotherSecretPassword
    expiration: never
    expires: no
    email: dag@wieers.com
    phone: 1-234-555-678
    first_name: Dag
    last_name: Wieers
    state: present

- name: Remove a user
  aci_aaa_user:
    host: apic
    username: admin
    password: SomeSecretPassword
    aaa_user: dag
    state: absent

- name: Query a user
  aci_aaa_user:
    host: apic
    username: admin
    password: SomeSecretPassword
    aaa_user: dag
    state: query

- name: Query all users
  aci_aaa_user:
    host: apic
    username: admin
    password: SomeSecretPassword
    state: query
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
  type: string
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
  type: string
  sample: '?rsp-prop-include=config-only'
method:
  description: The HTTP method used for the request to the APIC
  returned: failure or debug
  type: string
  sample: POST
response:
  description: The HTTP response from the APIC
  returned: failure or debug
  type: string
  sample: OK (30 bytes)
status:
  description: The HTTP status from the APIC
  returned: failure or debug
  type: int
  sample: 200
url:
  description: The HTTP url used for the request to the APIC
  returned: failure or debug
  type: string
  sample: https://10.11.12.13/api/mo/uni/tn-production.json
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

try:
    from dateutil.tz import tzutc
    import dateutil.parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        aaa_password=dict(type='str', no_log=True),
        aaa_password_lifetime=dict(type='int'),
        aaa_password_update_required=dict(type='bool'),
        aaa_user=dict(type='str', required=True, aliases=['name']),  # Not required for querying all objects
        clear_password_history=dict(type='bool'),
        description=dict(type='str', aliases=['descr']),
        email=dict(type='str'),
        enabled=dict(type='bool'),
        expiration=dict(type='str'),
        expires=dict(type='bool'),
        first_name=dict(type='str'),
        last_name=dict(type='str'),
        phone=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['aaa_user']],
            ['state', 'present', ['aaa_user']],
            ['expires', True, ['expiration']],
        ],
    )

    aci = ACIModule(module)

    if not HAS_DATEUTIL:
        module.fail_json(msg='dateutil required for this module')

    aaa_password = module.params['aaa_password']
    aaa_password_lifetime = module.params['aaa_password_lifetime']
    aaa_password_update_required = aci.boolean(module.params['aaa_password_update_required'])
    aaa_user = module.params['aaa_user']
    clear_password_history = module.params['clear_password_history']
    description = module.params['description']
    email = module.params['email']
    enabled = aci.boolean(module.params['enabled'], 'active', 'inactive')
    expires = aci.boolean(module.params['expires'])
    first_name = module.params['first_name']
    last_name = module.params['last_name']
    phone = module.params['phone']
    state = module.params['state']

    expiration = module.params['expiration']
    if expiration is not None and expiration != 'never':
        try:
            expiration = aci.iso8601_format(dateutil.parser.parse(expiration).replace(tzinfo=tzutc()))
        except Exception as e:
            module.fail_json(msg="Failed to parse date format '%s', %s" % (module.params['expiration'], e))

    aci.construct_url(
        root_class=dict(
            aci_class='aaaUser',
            aci_rn='userext/user-{0}'.format(aaa_user),
            filter_target='eq(aaaUser.name, "{0}")'.format(aaa_user),
            module_object=aaa_user,
        ),
    )
    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='aaaUser',
            class_config=dict(
                accountStatus=enabled,
                clearPwdHistory=clear_password_history,
                email=email,
                expiration=expiration,
                expires=expires,
                firstName=first_name,
                lastName=last_name,
                name=aaa_user,
                phone=phone,
                pwd=aaa_password,
                pwdLifeTime=aaa_password_lifetime,
                pwdUpdateRequired=aaa_password_update_required,
            ),
        )

        aci.get_diff(aci_class='aaaUser')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
