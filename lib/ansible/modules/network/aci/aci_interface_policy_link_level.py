#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Vasily Prokopov (@vasilyprokopov)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: aci_interface_policy_link_level
short_description: Manage Link Level interface policies (fabric:HIfPol)
description:
- The host interface policy specifies the layer 1 parameters of host facing ports.
version_added: '2.10'
options:
  link_level_policy:
    description:
    - The name of the Link Level interface policy.
    type: str
    required: yes
    aliases: [ name ]
  description:
    description:
    - The description of the Link Level interface policy.
    type: str
    aliases: [ descr ]
  auto_negotiation:
    description:
    - Auto-negotiation enables devices to automatically exchange information over a link about speed and duplex abilities.
    - The APIC defaults to C(on) when unset during creation.
    type: bool
  speed:
    description:
    - Determines the interface policy administrative port speed.
    - The APIC defaults to C(inherit) when unset during creation.
    type: str
    choices: [ unknown, 100M, 1G, 10G, 25G, 40G, 100G, inherit ]
  link_debounce_interval:
    description:
    - Enables the debounce timer for physical interface ports and sets it for a specified amount of time in milliseconds.
    - The APIC defaults to C(100) when unset during creation.
    type: int
  forwarding_error_correction:
    description:
    - Determines the forwarding error correction (FEC) mode.
    - The APIC defaults to C(inherit) when unset during creation.
    type: str
    choices: [ cl91-rs-fec, cl74-fc-fec, disable-fec, ieee-rs-fec, cons16-rs-fec ]
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
  description: More information about the internal APIC class B(fabric:HIfPol).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Vasily Prokopov (@vasilyprokopov)
'''

EXAMPLES = r'''
- aci_interface_policy_link_level:
    host: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    link_level_policy: '{{ link_level_policy }}'
    description: '{{ description }}'
    auto_negotiation: on
    speed: '{{ speed }}'
    link_debounce_interval: '{{ link_debounce_interval }}'
    forwarding_error_correction: '{{ forwarding_error_correction }}'
    state: present
  delegate_to: localhost
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


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        link_level_policy=dict(type='str', aliases=['name']),
        description=dict(type='str', aliases=['descr']),
        auto_negotiation=dict(type='bool'),
        speed=dict(type='str', choices=['unknown', '100M', '1G', '10G', '25G', '40G', '100G', 'inherit']),
        link_debounce_interval=dict(type='int'),
        forwarding_error_correction=dict(type='str', choices=['cl91-rs-fec', 'cl74-fc-fec', 'disable-fec', 'ieee-rs-fec', 'cons16-rs-fec']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['link_level_policy']],
            ['state', 'present', ['link_level_policy']],
        ],
    )

    aci = ACIModule(module)

    link_level_policy = module.params['link_level_policy']
    description = module.params['description']
    auto_negotiation = aci.boolean(module.params['auto_negotiation'], 'on', 'off')
    speed = module.params['speed']
    link_debounce_interval = module.params['link_debounce_interval']
    if link_debounce_interval is not None and link_debounce_interval not in range(0, 5001):
        module.fail_json(msg='The "link_debounce_interval" must be a value between 0 and 5000')
    forwarding_error_correction = module.params['forwarding_error_correction']
    state = module.params['state']

    aci.construct_url(
        root_class=dict(
            aci_class='fabricHIfPol',
            aci_rn='infra/hintfpol-{0}'.format(link_level_policy),
            module_object=link_level_policy,
            target_filter={'name': link_level_policy},
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='fabricHIfPol',
            class_config=dict(
                name=link_level_policy,
                descr=description,
                autoNeg=auto_negotiation,
                speed=speed,
                linkDebounce=link_debounce_interval,
                fecMode=forwarding_error_correction,
            ),
        )

        aci.get_diff(aci_class='fabricHIfPol')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
