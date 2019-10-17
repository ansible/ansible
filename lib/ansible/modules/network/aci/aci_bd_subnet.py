#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: aci_bd_subnet
short_description: Manage Subnets (fv:Subnet)
description:
- Manage Subnets on Cisco ACI fabrics.
version_added: '2.4'
options:
  bd:
    description:
    - The name of the Bridge Domain.
    type: str
    aliases: [ bd_name ]
  description:
    description:
    - The description for the Subnet.
    type: str
    aliases: [ descr ]
  enable_vip:
    description:
    - Determines if the Subnet should be treated as a VIP; used when the BD is extended to multiple sites.
    - The APIC defaults to C(no) when unset during creation.
    type: bool
  gateway:
    description:
    - The IPv4 or IPv6 gateway address for the Subnet.
    type: str
    aliases: [ gateway_ip ]
  mask:
    description:
    - The subnet mask for the Subnet.
    - This is the number associated with CIDR notation.
    - For IPv4 addresses, accepted values range between C(0) and C(32).
    - For IPv6 addresses, accepted Values range between C(0) and C(128).
    type: int
    aliases: [ subnet_mask ]
  nd_prefix_policy:
    description:
    - The IPv6 Neighbor Discovery Prefix Policy to associate with the Subnet.
    type: str
  preferred:
    description:
    - Determines if the Subnet is preferred over all available Subnets. Only one Subnet per Address Family (IPv4/IPv6).
      can be preferred in the Bridge Domain.
    - The APIC defaults to C(no) when unset during creation.
    type: bool
  route_profile:
    description:
    - The Route Profile to the associate with the Subnet.
    type: str
  route_profile_l3_out:
    description:
    - The L3 Out that contains the associated Route Profile.
    type: str
  scope:
    description:
    - Determines the scope of the Subnet.
    - The C(private) option only allows communication with hosts in the same VRF.
    - The C(public) option allows the Subnet to be advertised outside of the ACI Fabric, and allows communication with
      hosts in other VRFs.
    - The shared option limits communication to hosts in either the same VRF or the shared VRF.
    - The value is a list of options, C(private) and C(public) are mutually exclusive, but both can be used with C(shared).
    - The APIC defaults to C(private) when unset during creation.
    type: list
    choices:
      - private
      - public
      - shared
  subnet_control:
    description:
    - Determines the Subnet's Control State.
    - The C(querier_ip) option is used to treat the gateway_ip as an IGMP querier source IP.
    - The C(nd_ra) option is used to treat the gateway_ip address as a Neighbor Discovery Router Advertisement Prefix.
    - The C(no_gw) option is used to remove default gateway functionality from the gateway address.
    - The APIC defaults to C(nd_ra) when unset during creation.
    type: str
    choices: [ nd_ra, no_gw, querier_ip, unspecified ]
  subnet_name:
    description:
    - The name of the Subnet.
    type: str
    aliases: [ name ]
  tenant:
    description:
    - The name of the Tenant.
    type: str
    aliases: [ tenant_name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
notes:
- The C(gateway) parameter is the root key used to access the Subnet (not name), so the C(gateway)
  is required when the state is C(absent) or C(present).
- The C(tenant) and C(bd) used must exist before using this module in your playbook.
  The M(aci_tenant) module and M(aci_bd) can be used for these.
seealso:
- module: aci_bd
- module: aci_tenant
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(fv:Subnet).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Jacob McGill (@jmcgill298)
'''

EXAMPLES = r'''
- name: Create a tenant
  aci_tenant:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    state: present
  delegate_to: localhost

- name: Create a bridge domain
  aci_bd:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    bd: database
    state: present
  delegate_to: localhost

- name: Create a subnet
  aci_bd_subnet:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    bd: database
    gateway: 10.1.1.1
    mask: 24
    state: present
  delegate_to: localhost

- name: Create a subnet with options
  aci_bd_subnet:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    bd: database
    subnet_name: sql
    gateway: 10.1.2.1
    mask: 23
    description: SQL Servers
    scope: public
    route_profile_l3_out: corp
    route_profile: corp_route_profile
    state: present
  delegate_to: localhost

- name: Update a subnets scope to private and shared
  aci_bd_subnet:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    bd: database
    gateway: 10.1.1.1
    mask: 24
    scope: [private, shared]
    state: present
  delegate_to: localhost

- name: Get all subnets
  aci_bd_subnet:
    host: apic
    username: admin
    password: SomeSecretPassword
    state: query
  delegate_to: localhost

- name: Get all subnets of specific gateway in specified tenant
  aci_bd_subnet:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    gateway: 10.1.1.1
    mask: 24
    state: query
  delegate_to: localhost
  register: query_result

- name: Get specific subnet
  aci_bd_subnet:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    bd: database
    gateway: 10.1.1.1
    mask: 24
    state: query
  delegate_to: localhost
  register: query_result

- name: Delete a subnet
  aci_bd_subnet:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    bd: database
    gateway: 10.1.1.1
    mask: 24
    state: absent
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

SUBNET_CONTROL_MAPPING = dict(
    nd_ra='nd',
    no_gw='no-default-gateway',
    querier_ip='querier',
    unspecified='',
)


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        bd=dict(type='str', aliases=['bd_name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        enable_vip=dict(type='bool'),
        gateway=dict(type='str', aliases=['gateway_ip']),  # Not required for querying all objects
        mask=dict(type='int', aliases=['subnet_mask']),  # Not required for querying all objects
        subnet_name=dict(type='str', aliases=['name']),
        nd_prefix_policy=dict(type='str'),
        preferred=dict(type='bool'),
        route_profile=dict(type='str'),
        route_profile_l3_out=dict(type='str'),
        scope=dict(type='list', choices=['private', 'public', 'shared']),
        subnet_control=dict(type='str', choices=['nd_ra', 'no_gw', 'querier_ip', 'unspecified']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        tenant=dict(type='str', aliases=['tenant_name']),  # Not required for querying all objects
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[['gateway', 'mask']],
        required_if=[
            ['state', 'present', ['bd', 'gateway', 'mask', 'tenant']],
            ['state', 'absent', ['bd', 'gateway', 'mask', 'tenant']],
        ],
    )

    aci = ACIModule(module)

    description = module.params['description']
    enable_vip = aci.boolean(module.params['enable_vip'])
    tenant = module.params['tenant']
    bd = module.params['bd']
    gateway = module.params['gateway']
    mask = module.params['mask']
    if mask is not None and mask not in range(0, 129):
        # TODO: split checks between IPv4 and IPv6 Addresses
        module.fail_json(msg='Valid Subnet Masks are 0 to 32 for IPv4 Addresses and 0 to 128 for IPv6 addresses')
    if gateway is not None:
        gateway = '{0}/{1}'.format(gateway, str(mask))
    subnet_name = module.params['subnet_name']
    nd_prefix_policy = module.params['nd_prefix_policy']
    preferred = aci.boolean(module.params['preferred'])
    route_profile = module.params['route_profile']
    route_profile_l3_out = module.params['route_profile_l3_out']
    scope = module.params['scope']
    if scope is not None:
        if 'private' in scope and 'public' in scope:
            module.fail_json(msg="Parameter 'scope' cannot be both 'private' and 'public', got: %s" % scope)
        else:
            scope = ','.join(sorted(scope))
    state = module.params['state']
    subnet_control = module.params['subnet_control']
    if subnet_control:
        subnet_control = SUBNET_CONTROL_MAPPING[subnet_control]

    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{0}'.format(tenant),
            module_object=tenant,
            target_filter={'name': tenant},
        ),
        subclass_1=dict(
            aci_class='fvBD',
            aci_rn='BD-{0}'.format(bd),
            module_object=bd,
            target_filter={'name': bd},
        ),
        subclass_2=dict(
            aci_class='fvSubnet',
            aci_rn='subnet-[{0}]'.format(gateway),
            module_object=gateway,
            target_filter={'ip': gateway},
        ),
        child_classes=['fvRsBDSubnetToProfile', 'fvRsNdPfxPol'],
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='fvSubnet',
            class_config=dict(
                ctrl=subnet_control,
                descr=description,
                ip=gateway,
                name=subnet_name,
                preferred=preferred,
                scope=scope,
                virtual=enable_vip,
            ),
            child_configs=[
                {'fvRsBDSubnetToProfile': {'attributes': {'tnL3extOutName': route_profile_l3_out, 'tnRtctrlProfileName': route_profile}}},
                {'fvRsNdPfxPol': {'attributes': {'tnNdPfxPolName': nd_prefix_policy}}},
            ],
        )

        aci.get_diff(aci_class='fvSubnet')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
