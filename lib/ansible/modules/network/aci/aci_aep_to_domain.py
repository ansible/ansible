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
module: aci_aep_to_domain
short_description: Bind AEPs to Physical or Virtual Domains (infra:RsDomP)
description:
- Bind AEPs to Physical or Virtual Domains on Cisco ACI fabrics.
notes:
- The C(aep) and C(domain) parameters should exist before using this module.
  The M(aci_aep) and M(aci_domain) can be used for these.
- More information about the internal APIC class B(infra:RsDomP) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Dag Wieers (@dagwieers)
version_added: '2.5'
options:
  aep:
    description:
    - The name of the Attachable Access Entity Profile.
    aliases: [ aep_name ]
  domain:
    description:
    - Name of the physical or virtual domain being associated with the AEP.
    aliases: [ domain_name, domain_profile ]
  domain_type:
    description:
    - Determines if the Domain is physical (phys) or virtual (vmm).
    choices: [ fc, l2dom, l3dom, phys, vmm ]
    aliases: [ type ]
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
- name: Add AEP to domain binding
  aci_aep_to_domain: &binding_present
    host: apic
    username: admin
    password: SomeSecretPassword
    aep: test_aep
    domain: phys_dom
    domain_type: phys
    state: present

- name: Remove AEP to domain binding
  aci_aep_to_domain: &binding_absent
    host: apic
    username: admin
    password: SomeSecretPassword
    aep: test_aep
    domain: phys_dom
    domain_type: phys
    state: absent

- name: Query our AEP to domain binding
  aci_aep_to_domain:
    host: apic
    username: admin
    password: SomeSecretPassword
    aep: test_aep
    domain: phys_dom
    domain_type: phys
    state: query

- name: Query all AEP to domain bindings
  aci_aep_to_domain: &binding_query
    host: apic
    username: admin
    password: SomeSecretPassword
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


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        aep=dict(type='str', aliases=['aep_name']),  # Not required for querying all objects
        domain=dict(type='str', aliases=['domain_name', 'domain_profile']),  # Not required for querying all objects
        domain_type=dict(type='str', choices=['fc', 'l2dom', 'l3dom', 'phys', 'vmm'], aliases=['type']),  # Not required for querying all objects
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        vm_provider=dict(type='str', choices=['cloudfoundry', 'kubernetes', 'microsoft', 'openshift', 'openstack', 'redhat', 'vmware']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['domain_type', 'vmm', ['vm_provider']],
            ['state', 'absent', ['aep', 'domain', 'domain_type']],
            ['state', 'present', ['aep', 'domain', 'domain_type']],
        ],
        required_together=[
            ['domain', 'domain_type'],
        ],
    )

    aep = module.params['aep']
    domain = module.params['domain']
    domain_type = module.params['domain_type']
    vm_provider = module.params['vm_provider']
    state = module.params['state']

    # Report when vm_provider is set when type is not virtual
    if domain_type != 'vmm' and vm_provider is not None:
        module.fail_json(msg="Domain type '{0}' cannot have a 'vm_provider'".format(domain_type))

    # Compile the full domain for URL building
    if domain_type == 'fc':
        domain_mo = 'uni/fc-{0}'.format(domain)
    elif domain_type == 'l2dom':
        domain_mo = 'uni/l2dom-{0}'.format(domain)
    elif domain_type == 'l3dom':
        domain_mo = 'uni/l3dom-{0}'.format(domain)
    elif domain_type == 'phys':
        domain_mo = 'uni/phys-{0}'.format(domain)
    elif domain_type == 'vmm':
        domain_mo = 'uni/vmmp-{0}/dom-{1}'.format(VM_PROVIDER_MAPPING[vm_provider], domain)
    else:
        domain_mo = None

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='infraAttEntityP',
            aci_rn='infra/attentp-{0}'.format(aep),
            filter_target='eq(infraAttEntityP.name, "{0}")'.format(aep),
            module_object=aep,
        ),
        subclass_1=dict(
            aci_class='infraRsDomP',
            aci_rn='rsdomP-[{0}]'.format(domain_mo),
            filter_target='eq(infraRsDomP.tDn, "{0}")'.format(domain_mo),
            module_object=domain_mo,
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='infraRsDomP',
            class_config=dict(tDn=domain_mo),
        )

        aci.get_diff(aci_class='infraRsDomP')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
