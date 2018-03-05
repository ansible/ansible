#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Bruno Calogero <brunocalogero@hotmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_interface_selector_to_switch_policy_leaf_profile
short_description: Bind interface selector profiles to switch policy leaf profiles (infra:RsAccPortP)
description:
- Bind interface selector profiles to switch policy leaf profiles on Cisco ACI fabrics.
notes:
- This module requires an existing leaf profile, the module M(aci_switch_policy_leaf_profile) can be used for this.
- More information about the internal APIC class B(infra:RsAccPortP) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Bruno Calogero (@brunocalogero)
version_added: '2.5'
options:
  leaf_profile:
    description:
    - Name of the Leaf Profile to which we add a Selector.
    aliases: [ leaf_profile_name ]
  interface_selector:
    description:
    - Name of Interface Profile Selector to be added and associated with the Leaf Profile.
    aliases: [ name, interface_selector_name, interface_profile_name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Associating an interface selector profile to a switch policy leaf profile
  aci_interface_selector_to_switch_policy_leaf_profile:
    host: apic
    username: admin
    password: SomeSecretPassword
    leaf_profile: sw_name
    interface_selector: interface_profile_name
    state: present

- name: Remove an interface selector profile associated with a switch policy leaf profile
  aci_interface_selector_to_switch_policy_leaf_profile:
    host: apic
    username: admin
    password: SomeSecretPassword
    leaf_profile: sw_name
    interface_selector: interface_profile_name
    state: absent

- name: Query an interface selector profile associated with a switch policy leaf profile
  aci_interface_selector_to_switch_policy_leaf_profile:
    host: apic
    username: admin
    password: SomeSecretPassword
    leaf_profile: sw_name
    interface_selector: interface_profile_name
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
        leaf_profile=dict(type='str', aliases=['leaf_profile_name']),  # Not required for querying all objects
        interface_selector=dict(type='str', aliases=['interface_profile_name', 'interface_selector_name', 'name']),  # Not required for querying all objects
        state=dict(type='str', default='present', choices=['absent', 'present', 'query'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['leaf_profile', 'interface_selector']],
            ['state', 'present', ['leaf_profile', 'interface_selector']]
        ],
    )

    leaf_profile = module.params['leaf_profile']
    # WARNING: interface_selector accepts non existing interface_profile names and they appear on APIC gui with a state of "missing-target"
    interface_selector = module.params['interface_selector']
    state = module.params['state']

    # Defining the interface profile tDn for clarity
    interface_selector_tDn = 'uni/infra/accportprof-{0}'.format(interface_selector)

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='infraNodeP',
            aci_rn='infra/nprof-{0}'.format(leaf_profile),
            filter_target='eq(infraNodeP.name, "{0}")'.format(leaf_profile),
            module_object=leaf_profile
        ),
        subclass_1=dict(
            aci_class='infraRsAccPortP',
            aci_rn='rsaccPortP-[{0}]'.format(interface_selector_tDn),
            filter_target='eq(infraRsAccPortP.name, "{0}")'.format(interface_selector),
            module_object=interface_selector,
        )
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='infraRsAccPortP',
            class_config=dict(tDn=interface_selector_tDn),
        )

        aci.get_diff(aci_class='infraRsAccPortP')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
