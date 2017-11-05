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
module: aci_bd_dhcp_label
short_description: Manage DHCP Label on Cisco ACI fabrics (dhcp:Lbl)
description:
- Manage DHCP Label on Cisco ACI fabrics (dhcp:Lbl)
- More information from the internal APIC class
  I(dhcp:Lbl) at U(https://pubhub-prod.s3.amazonaws.com/media/apic-mim-ref/docs/MO-dhcpLbl.html).
author:
- sig9 (sig9@sig9.org)
version_added: '2.5'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- A DHCP relay label contains a name for the label, the scope, and a DHCP option policy.
  The scope is the owner of the relay server and the DHCP option policy supplies DHCP clients
  with configuration parameters such as domain, nameserver, and subnet router addresses.
options:
  bd:
    description:
    - The name of the Bridge Domain.
    required: yes
  description:
    description:
    - Specifies a description of the policy definition.
    required: no
  dhcp_label:
    description:
    - The name of the DHCP Relay Label.
    required: yes
  dhcp_option:
    description:
    - The DHCP option is used to supply DHCP clients with configuration parameters
      such as a domain, name server, subnet, and network address.
    required: no
  owner:
    description:
    - Represents the target relay servers ownership.
    required: yes
    choices: [ infra, tenant ]
    default: infra
  tenant:
    description:
    - The name of the Tenant.
    aliases: [ tenant_name ]
    required: yes
'''

EXAMPLES = r'''
- name: Create a new DHCP Relay Label to a Bridge Domain
  aci_bd_dhcp_label:
    host: "{{ apic }}"
    username: "{{ username }}"
    password: "{{ password }}"
    validate_certs: false
    tenant: "{{ tenant }}"
    bd: "{{ inventory_hostname }}"
    dhcp_label: "{{ dhcp_label }}"
    owner: "{{ owner }}"
    state: "present"

- name: Remove a DHCP Relay Label for a Bridge Domain
  aci_bd_dhcp_label:
    host: "{{ apic }}"
    username: "{{ username }}"
    password: "{{ password }}"
    validate_certs: false
    tenant: "{{ tenant }}"
    bd: "{{ inventory_hostname }}"
    dhcp_label: "{{ dhcp_label }}"
    owner: "{{ owner }}"
    state: "absent"

- name: Query a DHCP Relay Label of a Bridge Domain
  aci_bd_dhcp_label:
    host: "{{ apic }}"
    username: "{{ username }}"
    password: "{{ password }}"
    validate_certs: false
    tenant: "{{ tenant }}"
    bd: "{{ inventory_hostname }}"
    dhcp_label: "{{ dhcp_label }}"
    owner: "{{ owner }}"
    state: "query"
'''

RETURN = r'''
#
'''

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        bd=dict(type='str', aliases=['bd_name']),
        description=dict(type='str', aliases=['descr']),
        dhcp_label=dict(type='str'),
        dhcp_option=dict(type='str'),
        owner=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        tenant=dict(type='str', aliases=['tenant_name']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['bd', 'tenant']],
            ['state', 'present', ['bd', 'tenant']],
        ],
    )

    description = module.params['description']
    dhcp_label = module.params['dhcp_label']
    dhcp_option = module.params['dhcp_option']
    owner = module.params['owner']
    state = module.params['state']

    module.params['bd_dhcp_label'] = dhcp_label

    aci = ACIModule(module)
    aci.construct_url(
        root_class='tenant', subclass_1='bd', subclass_2='bd_dhcp_label',
        child_classes=['dhcpRsDhcpOptionPol'],
    )
    aci.get_existing()

    if state == 'present':
        # Filter out module params with null values
        aci.payload(
            aci_class='dhcpLbl',
            class_config=dict(
                descr=description,
                name=dhcp_label,
                owner=owner,
            ),
            child_configs=[
                {'dhcpRsDhcpOptionPol': {'attributes': {'tnDhcpOptionPolName': dhcp_option}}},
            ],
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='dhcpLbl')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
