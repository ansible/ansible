#!/usr/bin/python

# Copyright: (c) 2019, Tim Knipper <tim.knipper@gmail.com>
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
module: aci_interface_policy_cdp
short_description: Manage CDP interface policies (cdp:IfPol)
description:
- Manage CDP interface policies on Cisco ACI fabrics.
version_added: '2.9'
options:
  cdp_policy:
    description:
    - The CDP interface policy name.
    type: str
    required: yes
    aliases: [ cdp_interface, name ]
  description:
    description:
    - The description for the CDP interface policy name.
    type: str
    aliases: [ descr ]
  admin_state:
    description:
    - Enable or Disable CDP state.
    - The APIC defaults to C(yes) when unset during creation.
    type: bool
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
seealso:
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(cdp:IfPol).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Tim Knipper (@tknipper11)
'''

EXAMPLES = r'''
- name: Create CDP Test Policy
  aci_interface_policy_cdp:
    name: Ansible_CDP_Test_Policy
    host: apic.example.com
    username: admin
    password: adminpass
    state: present

- name: Remove CDP Test Policy
  aci_interface_policy_cdp:
    name: Ansible_CDP_Test_Policy
    host: apic.example.com
    username: admin
    password: adminpass
    output_level: debug
    state: absent

- name: Query CDP Policy
  aci_interface_policy_cdp:
    host: apic.example.com
    username: admin
    password: adminpass
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
            "cdpIfPol": {
                "attributes": {
                    "adminSt": "disabled",
                    "annotation": "",
                    "descr": "Ansible Created CDP Test Policy",
                    "dn": "uni/infra/cdpIfP-Ansible_CDP_Test_Policy",
                    "name": "Ansible_CDP_Test_Policy",
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
        cdp_policy=dict(type='str', required=False, aliases=['cdp_interface', 'name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        admin_state=dict(type='bool'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['cdp_policy']],
            ['state', 'present', ['cdp_policy']],
        ],
    )

    aci = ACIModule(module)

    cdp_policy = module.params['cdp_policy']
    description = module.params['description']
    admin_state = aci.boolean(module.params['admin_state'], 'enabled', 'disabled')
    state = module.params['state']

    aci.construct_url(
        root_class=dict(
            aci_class='cdpIfPol',
            aci_rn='infra/cdpIfP-{0}'.format(cdp_policy),
            module_object=cdp_policy,
            target_filter={'name': cdp_policy},
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='cdpIfPol',
            class_config=dict(
                name=cdp_policy,
                descr=description,
                adminSt=admin_state,
            ),
        )

        aci.get_diff(aci_class='cdpIfPol')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == '__main__':
    main()
