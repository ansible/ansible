#!/usr/bin/python

from __future__ import absolute_import, division, print_function
__metaclass__ = type
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: aci_firmware_group

short_description: This module creates a firmware group

version_added: "2.8"

description:
    - This module creates a firmware group, so that you can apply firmware policy to nodes.
    
dependancies:
    - This module is dependent on the aci_firmware_policy, so that must be created in conjunction with this module. 
    The object, firmwareFwGrp is created with this module as well as sub-class firmwareRsFwgrpp. The sub-class, 
    firmwareRsFwgrpp, references the firmwareFwP (Firmware Policy) which was created with aci_firmware_policy. When 
    the firmware group is deleted using this current module, the class firmwareFwP is also deleted. 

options:
    group:
        description:
            - This the name of the firmware group
        required: true
    firmwarepol:
        description:
            - This is the name of the firmware policy, which was create by aci_firmware_policy. It is important that
            you use the same name as the policy created with aci_firmware_policy
        required: false
    state:
        description:
            - Use C(present) or C(absent) for adding or removing.
            - Use C(query) for listing an object or multiple objects.
        default: present
        choices: [ absent, present, query ]

extends_documentation_fragment:
    - ACI
    
issues: 
    - With this release, you are unable to remove the firmware group, the absent state currently does not work.
    If the firmware group needs to be removed, please use the UI

author:
    - Steven Gerhart (@sgerhart)
'''

EXAMPLES = '''
- description:
  This example create a firmware group - Please make sure that you create a firmware policy with aci_firmware_policy 
  and name the option firmwarepol the same name as the policy
  - name: firmware group
     aci_firmware_group:
        host: "{{ inventory_hostname }}"
        username: "{{ user }}"
        password: "{{ pass }}"
        validate_certs: no
        group: testingfwgrp
        firmwarepol: test2FrmPol
        state: present
        
- description
  This example creates a firmware policy and group - Note that the firmware policy is calling the
  aci_firmware_policy. Also, notice that the firmware policy name is the same as the firmware group firmwarepol. These 
  have to match or there will be no firmware associated with the firmware group
   - name: firmware policy
     aci_firmware_policy:
        host: "{{ inventory_hostname }}"
        username: "{{ user }}"
        password: "{{ pass }}"
        validate_certs: no
        name: test2FrmPol
        version: n9000-13.2(1m)
        ignoreCompat: False
        state: present
   - name: firmware group
     aci_firmware_group:
        host: "{{ inventory_hostname }}"
        username: "{{ user }}"
        password: "{{ pass }}"
        validate_certs: no
        group: testingfwgrp
        firmwarepol: test2FrmPol
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

import json
from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        group=dict(type='str', aliases=['name', 'group_name']),  # Not required for querying all objects
        firmwarepol=dict(type='str', aliases=['firmware']),  # Not required for querying all objects
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['group']],
            ['state', 'present', ['group', 'firmwarepol']],
        ],
    )

    state = module.params['state']
    group = module.params['group']
    firmwarepol = module.params['firmwarepol']


    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='firmwareFwGrp',
            aci_rn='fabric/fwgrp-{0}'.format(group),
            filter_target='eq(firmwareFwGrp.name, "{0}")'.format(group),
            module_object=group,
        ),
        child_classes=['firmwareRsFwgrpp'],
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='firmwareFwGrp',
            class_config=dict(
                name=group,
            ),
            child_configs=[
                dict(
                    firmwareRsFwgrpp=dict(
                        attributes=dict(
                            tnFirmwareFwPName=firmwarepol,
                        ),
                    ),
                ),
            ],

        )

        aci.get_diff(aci_class='firmwareFwGrp')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()


    aci.exit_json()


if __name__ == "__main__":
    main()
