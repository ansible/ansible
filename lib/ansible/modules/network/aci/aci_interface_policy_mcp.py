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
module: aci_interface_policy_mcp
short_description: Manage MCP interface policies (mcp:IfPol)
description:
- Manage MCP interface policies on Cisco ACI fabrics.
notes:
- More information about the internal APIC class B(mcp:IfPol) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Dag Wieers (@dagwieers)
version_added: '2.4'
options:
  mcp:
    description:
    - The name of the MCP interface.
    required: yes
    aliases: [ mcp_interface, name ]
  description:
    description:
    - The description for the MCP interface.
    aliases: [ descr ]
  admin_state:
    description:
    - Enable or disable admin state.
    - The APIC defaults to C(enable) when unset during creation.
    choices: [ disable, enable ]
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
- aci_interface_policy_mcp:
    host: '{{ hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    mcp: '{{ mcp }}'
    description: '{{ descr }}'
    admin_state: '{{ admin_state }}'
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
        mcp=dict(type='str', required=False, aliases=['mcp_interface', 'name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        admin_state=dict(type='raw'),  # Turn into a boolean in v2.9
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['mcp']],
            ['state', 'present', ['mcp']],
        ],
    )

    aci = ACIModule(module)

    mcp = module.params['mcp']
    description = module.params['description']
    admin_state = aci.boolean(module.params['admin_state'], 'enabled', 'disabled')
    state = module.params['state']

    aci.construct_url(
        root_class=dict(
            aci_class='mcpIfPol',
            aci_rn='infra/mcpIfP-{0}'.format(mcp),
            filter_target='eq(mcpIfPol.name, "{0}")'.format(mcp),
            module_object=mcp,
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='mcpIfPol',
            class_config=dict(
                name=mcp,
                descr=description,
                adminSt=admin_state,
            ),
        )

        aci.get_diff(aci_class='mcpIfPol')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
