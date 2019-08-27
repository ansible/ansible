#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: aci_maintenance_group
short_description: This creates an ACI maintenance group
version_added: "2.8"
notes:
    - a maintenance policy (aci_maintenance_policy must be created prior to creating an aci maintenance group
description:
    - This modules creates an ACI maintenance group
options:
    group:
        description:
            - This is the name of the group
        required: true
    policy:
        description:
            - This is the name of the policy that was created using aci_maintenance_policy
        required: true
    state:
        description:
            - Use C(present) or C(absent) for adding or removing.
            - Use C(query) for listing an object or multiple objects.
        default: present
        choices: ['absent', 'present', 'query']
extends_documentation_fragment:
    - aci
author:
    - Steven Gerhart (@sgerhart)
'''

EXAMPLES = '''
- name: maintenance group
  aci_maintenance_group:
    host: "{{ inventory_hostname }}"
    username: "{{ user }}"
    password: "{{ pass }}"
    validate_certs: no
    group: maintenancegrp1
    policy: maintenancePol1
    state: present
'''

RETURN = '''
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

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        group=dict(type='str'),  # Not required for querying all objects
        policy=dict(type='str'),  # Not required for querying all objects
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['group']],
            ['state', 'present', ['group']],
        ],
    )

    state = module.params['state']
    group = module.params['group']
    policy = module.params['policy']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='maintMaintGrp',
            aci_rn='fabric/maintgrp-{0}'.format(group),
            target_filter={'name': group},
            module_object=group,
        ),
        child_classes=['maintRsMgrpp'],
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='maintMaintGrp',
            class_config=dict(
                name=group,
            ),
            child_configs=[
                dict(
                    maintRsMgrpp=dict(
                        attributes=dict(
                            tnMaintMaintPName=policy,
                        ),
                    ),
                ),
            ],

        )

        aci.get_diff(aci_class='maintMaintGrp')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
