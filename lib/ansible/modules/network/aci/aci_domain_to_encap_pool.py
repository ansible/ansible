#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_domain_to_encap_pool
short_description: Bind Domain to Encap Pools (infra:RsVlanNs)
description:
- Bind Domain to Encap Pools on Cisco ACI fabrics.
notes:
- The C(domain) and C(encap_pool) parameters should exist before using this module.
  The M(aci_domain) and M(aci_encap_pool) can be used for these.
- More information about the internal APIC class B(infra:RsVlanNs) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Dag Wieers (@dagwieers)
version_added: '2.5'
options:
  domain:
    description:
    - Name of the domain being associated with the Encap Pool.
    aliases: [ domain_name, domain_profile ]
  domain_type:
    description:
    - Determines if the Domain is physical (phys) or virtual (vmm).
    choices: [ fc, l2dom, l3dom, phys, vmm ]
  pool:
    description:
    - The name of the pool.
    aliases: [ pool_name ]
  pool_allocation_mode:
    description:
    - The method used for allocating encaps to resources.
    - Only vlan and vsan support allocation modes.
    choices: [ dynamic, static]
    aliases: [ allocation_mode, mode ]
  pool_type:
    description:
    - The encap type of C(pool).
    required: yes
    choices: [ vlan, vsan, vxlan ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
  vm_provider:
    description:
    - The VM platform for VMM Domains.
    - Support for Kubernetes was added in ACI v3.0.
    - Support for CloudFoundry, OpenShift and Red Hat was added in ACI v3.1.
    choices: [ cloudfoundry, kubernetes, microsoft, openshift, openstack, redhat, vmware ]
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add domain to VLAN pool binding
  aci_domain_to_encap_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    domain: phys_dom
    domain_type: phys
    pool: test_pool
    pool_type: vlan
    pool_allocation_mode: dynamic
    state: present

- name: Remove domain to VLAN pool binding
  aci_domain_to_encap_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    domain: phys_dom
    domain_type: phys
    pool: test_pool
    pool_type: vlan
    pool_allocation_mode: dynamic
    state: absent

- name: Query our domain to VLAN pool binding
  aci_domain_to_encap_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    domain: phys_dom
    pool: test_pool
    pool_type: vlan
    pool_allocation_mode: dynamic
    state: query

- name: Query all domain to VLAN pool bindings
  aci_domain_to_encap_pool:
    host: apic
    username: admin
    password: SomeSecretPassword
    domain_type: phys
    pool_type: vlan
    pool_allocation_mode: dynamic
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

VM_PROVIDER_MAPPING = dict(
    cloudfoundry='CloudFoundry',
    kubernetes='Kubernetes',
    microsoft='Microsoft',
    openshift='OpenShift',
    openstack='OpenStack',
    redhat='Redhat',
    vmware='VMware',
)

POOL_MAPPING = dict(
    vlan=dict(
        aci_mo='uni/infra/vlanns-{0}',
        child_class='infraRsVlanNs',
    ),
    vxlan=dict(
        aci_mo='uni/infra/vxlanns-{0}',
        child_class='vmmRsVxlanNs',
    ),
    vsan=dict(
        aci_mo='uni/infra/vsanns-{0}',
        child_class='fcRsVsanNs',
    ),
)


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        domain=dict(type='str', aliases=['domain_name', 'domain_profile']),
        domain_type=dict(type='str', choices=['fc', 'l2dom', 'l3dom', 'phys', 'vmm']),
        pool=dict(type='str', aliases=['pool_name']),
        pool_allocation_mode=dict(type='str', aliases=['allocation_mode', 'mode'], choices=['dynamic', 'static']),
        pool_type=dict(type='str', required=True, choices=['vlan', 'vsan', 'vxlan']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        vm_provider=dict(type='str', choices=['cloudfoundry', 'kubernetes', 'microsoft', 'openshift', 'openstack', 'redhat', 'vmware']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['domain_type', 'vmm', ['vm_provider']],
            ['state', 'absent', ['domain', 'domain_type', 'pool', 'pool_type']],
            ['state', 'present', ['domain', 'domain_type', 'pool', 'pool_type']],
        ],
    )

    domain = module.params['domain']
    domain_type = module.params['domain_type']
    pool = module.params['pool']
    pool_allocation_mode = module.params['pool_allocation_mode']
    pool_type = module.params['pool_type']
    vm_provider = module.params['vm_provider']
    state = module.params['state']

    # Report when vm_provider is set when type is not virtual
    if domain_type != 'vmm' and vm_provider is not None:
        module.fail_json(msg="Domain type '{0}' cannot have a 'vm_provider'".format(domain_type))

    # ACI Pool URL requires the allocation mode for vlan and vsan pools (ex: uni/infra/vlanns-[poolname]-static)
    pool_name = pool
    if pool_type != 'vxlan' and pool is not None:
        if pool_allocation_mode is not None:
            pool_name = '[{0}]-{1}'.format(pool, pool_allocation_mode)
        else:
            module.fail_json(msg="ACI requires the 'pool_allocation_mode' for 'pool_type' of 'vlan' and 'vsan' when 'pool' is provided")

    # Vxlan pools do not support allocation modes
    if pool_type == 'vxlan' and pool_allocation_mode is not None:
        module.fail_json(msg='vxlan pools do not support setting the allocation_mode; please remove this parameter from the task')

    # Compile the full domain for URL building
    if domain_type == 'fc':
        domain_class = 'fcDomP'
        domain_mo = 'uni/fc-{0}'.format(domain)
        domain_rn = 'fc-{0}'.format(domain)
    elif domain_type == 'l2ext':
        domain_class = 'l2extDomP'
        domain_mo = 'uni/l2dom-{0}'.format(domain)
        domain_rn = 'l2dom-{0}'.format(domain)
    elif domain_type == 'l3ext':
        domain_class = 'l3extDomP'
        domain_mo = 'uni/l3dom-{0}'.format(domain)
        domain_rn = 'l3dom-{0}'.format(domain)
    elif domain_type == 'phys':
        domain_class = 'physDomP'
        domain_mo = 'uni/phys-{0}'.format(domain)
        domain_rn = 'phys-{0}'.format(domain)
    elif domain_type == 'vmm':
        domain_class = 'vmmDomP'
        domain_mo = 'uni/vmmp-{0}/dom-{1}'.format(VM_PROVIDER_MAPPING[vm_provider], domain)
        domain_rn = 'vmmp-{0}/dom-{1}'.format(VM_PROVIDER_MAPPING[vm_provider], domain)

    # Ensure that querying all objects works when only domain_type is provided
    if domain is None:
        domain_mo = None

    pool_mo = POOL_MAPPING[pool_type]['aci_mo'].format(pool_name)
    child_class = POOL_MAPPING[pool_type]['child_class']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class=domain_class,
            aci_rn=domain_rn,
            filter_target='eq({0}.name, "{1}")'.format(domain_class, domain),
            module_object=domain_mo,
        ),
        child_classes=[child_class],
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module params with null values
        aci.payload(
            aci_class=domain_class,
            class_config=dict(name=domain),
            child_configs=[
                {child_class: {'attributes': {'tDn': pool_mo}}},
            ]
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class=domain_class)

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
