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
module: aci_interface_policy_port_security
short_description: Manage port security (l2:PortSecurityPol)
description:
- Manage port security on Cisco ACI fabrics.
notes:
- More information about the internal APIC class B(l2:PortSecurityPol) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Dag Wieers (@dagwieers)
version_added: '2.4'
options:
  port_security:
    description:
    - The name of the port security.
    required: yes
    aliases: [ name ]
  description:
    description:
    - The description for the contract.
    aliases: [ descr ]
  max_end_points:
    description:
    - Maximum number of end points (range 0-12000).
    - The APIC defaults to C(0) when unset during creation.
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

# FIXME: Add more, better examples
EXAMPLES = r'''
- aci_interface_policy_port_security:
    host: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    port_security: '{{ port_security }}'
    description: '{{ descr }}'
    max_end_points: '{{ max_end_points }}'
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
        port_security=dict(type='str', required=False, aliases=['name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        max_end_points=dict(type='int'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['port_security']],
            ['state', 'present', ['port_security']],
        ],
    )

    port_security = module.params['port_security']
    description = module.params['description']
    max_end_points = module.params['max_end_points']
    if max_end_points is not None and max_end_points not in range(12001):
        module.fail_json(msg='The "max_end_points" must be between 0 and 12000')
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='l2PortSecurityPol',
            aci_rn='infra/portsecurityP-{0}'.format(port_security),
            filter_target='eq(l2PortSecurityPol.name, "{0}")'.format(port_security),
            module_object=port_security,
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='l2PortSecurityPol',
            class_config=dict(
                name=port_security,
                descr=description,
                maximum=max_end_points,
            ),
        )

        aci.get_diff(aci_class='l2PortSecurityPol')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
