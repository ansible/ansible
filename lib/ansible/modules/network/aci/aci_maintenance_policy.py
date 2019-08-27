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

DOCUMENTATION = r'''
---
module: aci_maintenance_policy
short_description: Manage firmware maintenance policies
version_added: '2.8'
description:
- Manage maintenance policies that defines behavior during an ACI upgrade.
options:
  name:
    description:
    - The name for the maintenance policy.
    required: true
    aliases: [ maintenance_policy ]
  runmode:
    description:
    - Whether the system pauses on error or just continues through it.
    choices: ['pauseOnlyOnFailures', 'pauseNever']
    default: pauseOnlyOnFailures
  graceful:
    description:
    - Whether the system will bring down the nodes gracefully during an upgrade, which reduces traffic lost.
    - The APIC defaults to C(no) when unset during creation.
    type: bool
  scheduler:
    description:
    - The name of scheduler that is applied to the policy.
    type: str
    required: true
  adminst:
    description:
    - Will trigger an immediate upgrade for nodes if adminst is set to triggered.
    choices: [ triggered, untriggered ]
    default: untriggered
  ignoreCompat:
    description:
    - To check whether compatibility checks should be ignored
    - The APIC defaults to C(no) when unset during creation.
    type: bool
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment:
- aci
notes:
- A scheduler is required for this module, which could have been created using the M(aci_fabric_scheduler) module or via the UI.
author:
- Steven Gerhart (@sgerhart)
'''

EXAMPLES = r'''
- name: Ensure maintenance policy is present
  aci_maintenance_policy:
    host: '{{ inventory_hostname }}'
    username: '{{ user }}'
    password: '{{ pass }}'
    validate_certs: no
    name: maintenancePol1
    scheduler: simpleScheduler
    runmode: False
    state: present
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


from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        name=dict(type='str', aliases=['maintenance_policy']),  # Not required for querying all objects
        runmode=dict(type='str', default='pauseOnlyOnFailures', choices=['pauseOnlyOnFailures', 'pauseNever']),
        graceful=dict(type='bool'),
        scheduler=dict(type='str'),
        ignoreCompat=dict(type='bool'),
        adminst=dict(type='str', default='untriggered', choices=['triggered', 'untriggered']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['name']],
            ['state', 'present', ['name', 'scheduler']],
        ],
    )

    aci = ACIModule(module)

    state = module.params['state']
    name = module.params['name']
    runmode = module.params['runmode']
    scheduler = module.params['scheduler']
    adminst = module.params['adminst']
    graceful = aci.boolean(module.params['graceful'])
    ignoreCompat = aci.boolean(module.params['ignoreCompat'])

    aci.construct_url(
        root_class=dict(
            aci_class='maintMaintP',
            aci_rn='fabric/maintpol-{0}'.format(name),
            target_filter={'name': name},
            module_object=name,
        ),
        child_classes=['maintRsPolScheduler']

    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='maintMaintP',
            class_config=dict(
                name=name,
                runMode=runmode,
                graceful=graceful,
                adminSt=adminst,
                ignoreCompat=ignoreCompat,
            ),
            child_configs=[
                dict(
                    maintRsPolScheduler=dict(
                        attributes=dict(
                            tnTrigSchedPName=scheduler,
                        ),
                    ),
                ),
            ],

        )

        aci.get_diff(aci_class='maintMaintP')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
