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
---
module: aci_maintenance_policy
short_description: Creates a firmware maintenance policy
version_added: "2.8"
description:
    - Creates a maintenance policy that defines behavior during an ACI upgrade.

notes:
    - A scheduler is required for this module, which could have been created via the UI or the aci_scheduler module.
options:
    name:
        description:
            - name for maintenance policy
        required: true
        aliases: [ maintenancepolicy ]
    runmode:
        description:
            - specifies if the system pauses on error or just continues through it.
            - The default is "pause"
        type: bool
        default: True
        required: false
    graceful:
        description:
            - defines if the system will bring down the nodes gracefully during an upgrade, which reduces traffic lost
        type: bool
        required: false
    scheduler:
        description:
            - name of scheduler that is applied to the policy.
        type: str
        required: true
    upgrade:
        description:
            - will trigger an immediate upgrade for nodes if adminst is set to triggered.
        default: untriggered
        choices: [ 'untriggered', 'triggered' ]
    state:
        description:
            - Use C(present) or C(absent) for adding or removing.
            - Use C(query) for listing an object or multiple objects.
        default: present
        choices: [ 'absent', 'present', 'query']

extends_documentation_fragment:
    - ACI
author:
    - Steven Gerhart (@sgerhart)
'''

EXAMPLES = '''
   - name: maintenance policy
     aci_maintenance_policy:
        host: "{{ inventory_hostname }}"
        username: "{{ user }}"
        password: "{{ pass }}"
        validate_certs: no
        name: maintenancePol1
        scheduler: simpleScheduler
        runmode: False
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
  sample: ?rsp-prop-include=config-only
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


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        name=dict(type='str', aliases=['maintenancepolicy']),  # Not required for querying all objects
        runmode=dict(type='bool', default='true'),
        graceful=dict(type=bool),
        scheduler=dict(type='str'),
        upgrade=dict(type='str', default='untriggered', choices=['untriggered', 'triggered']),
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

    state = module.params['state']
    name = module.params['name']
    runmode = module.params['runmode']
    scheduler = module.params['scheduler']
    adminst = module.params['upgrade']
    graceful = module.params['graceful']

    if runmode:
        mode = 'pauseOnlyOnFailures'
    else:
        mode = 'pauseNever'

    if module.params['graceful']:
        graceful_maint = 'yes'
    else:
        graceful_maint = 'no'

    aci = ACIModule(module)
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
                runMode=mode,
                graceful=graceful_maint,
                adminSt=adminst,
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
