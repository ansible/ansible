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
module: aci_epg_to_domain
short_description: Bind EPGs to Domains (fv:RsDomAtt)
description:
- Bind EPGs to Physical and Virtual Domains on Cisco ACI fabrics.
notes:
- The C(tenant), C(ap), C(epg), and C(domain) used must exist before using this module in your playbook.
  The M(aci_tenant) M(aci_ap), M(aci_epg) M(aci_domain) modules can be used for this.
- OpenStack VMM domains must not be created using this module. The OpenStack VMM domain is created directly
  by the Cisco APIC Neutron plugin as part of the installation and configuration.
  This module can be used to query status of an OpenStack VMM domain.
- More information about the internal APIC class B(fv:RsDomAtt) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Jacob McGill (@jmcgill298)
version_added: '2.4'
options:
  allow_useg:
    description:
    - Allows micro-segmentation.
    - The APIC defaults to C(encap) when unset during creation.
    choices: [ encap, useg ]
  ap:
    description:
    - Name of an existing application network profile, that will contain the EPGs.
    aliases: [ app_profile, app_profile_name ]
  deploy_immediacy:
    description:
    - Determines when the policy is pushed to hardware Policy CAM.
    - The APIC defaults to C(lazy) when unset during creation.
    choices: [ immediate, lazy ]
  domain:
    description:
    - Name of the physical or virtual domain being associated with the EPG.
    aliases: [ domain_name, domain_profile ]
  domain_type:
    description:
    - Determines if the Domain is physical (phys) or virtual (vmm).
    choices: [ phys, vmm ]
    aliases: [ type ]
  encap:
    description:
    - The VLAN encapsulation for the EPG when binding a VMM Domain with static encap_mode.
    - This acts as the secondary encap when using useg.
    choices: [ range from 1 to 4096 ]
  encap_mode:
    description:
    - The ecapsulataion method to be used.
    - The APIC defaults to C(auto) when unset during creation.
    choices: [ auto, vlan, vxlan ]
  epg:
    description:
    - Name of the end point group.
    aliases: [ epg_name, name ]
  netflow:
    description:
    - Determines if netflow should be enabled.
    - The APIC defaults to C(no) when unset during creation.
    type: bool
  primary_encap:
    description:
    - Determines the primary VLAN ID when using useg.
    choices: [ range from 1 to 4096 ]
  resolution_immediacy:
    description:
    - Determines when the policies should be resolved and available.
    - The APIC defaults to C(lazy) when unset during creation.
    choices: [ immediate, lazy, pre-provision ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
  tenant:
    description:
    - Name of an existing tenant.
    aliases: [ tenant_name ]
  vm_provider:
    description:
    - The VM platform for VMM Domains.
    - Support for Kubernetes was added in ACI v3.0.
    - Support for CloudFoundry, OpenShift and Red Hat was added in ACI v3.1.
    choices: [ cloudfoundry, kubernetes, microsoft, openshift, openstack, redhat, vmware ]
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new physical domain to EPG binding
  aci_epg_to_domain:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: anstest
    ap: anstest
    epg: anstest
    domain: anstest
    domain_type: phys
    state: present

- name: Remove an existing physical domain to EPG binding
  aci_epg_to_domain:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: anstest
    ap: anstest
    epg: anstest
    domain: anstest
    domain_type: phys
    state: absent

- name: Query a specific physical domain to EPG binding
  aci_epg_to_domain:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: anstest
    ap: anstest
    epg: anstest
    domain: anstest
    domain_type: phys
    state: query

- name: Query all domain to EPG bindings
  aci_epg_to_domain:
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
        allow_useg=dict(type='str', choices=['encap', 'useg']),
        ap=dict(type='str', aliases=['app_profile', 'app_profile_name']),  # Not required for querying all objects
        deploy_immediacy=dict(type='str', choices=['immediate', 'on-demand']),
        domain=dict(type='str', aliases=['domain_name', 'domain_profile']),  # Not required for querying all objects
        domain_type=dict(type='str', choices=['phys', 'vmm'], aliases=['type']),  # Not required for querying all objects
        encap=dict(type='int'),
        encap_mode=dict(type='str', choices=['auto', 'vlan', 'vxlan']),
        epg=dict(type='str', aliases=['name', 'epg_name']),  # Not required for querying all objects
        netflow=dict(type='raw'),  # Turn into a boolean in v2.9
        primary_encap=dict(type='int'),
        resolution_immediacy=dict(type='str', choices=['immediate', 'lazy', 'pre-provision']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        tenant=dict(type='str', aliases=['tenant_name']),  # Not required for querying all objects
        vm_provider=dict(type='str', choices=['cloudfoundry', 'kubernetes', 'microsoft', 'openshift', 'openstack', 'redhat', 'vmware']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['domain_type', 'vmm', ['vm_provider']],
            ['state', 'absent', ['ap', 'domain', 'domain_type', 'epg', 'tenant']],
            ['state', 'present', ['ap', 'domain', 'domain_type', 'epg', 'tenant']],
        ],
    )

    aci = ACIModule(module)

    allow_useg = module.params['allow_useg']
    ap = module.params['ap']
    deploy_immediacy = module.params['deploy_immediacy']
    domain = module.params['domain']
    domain_type = module.params['domain_type']
    vm_provider = module.params['vm_provider']
    encap = module.params['encap']
    if encap is not None:
        if encap in range(1, 4097):
            encap = 'vlan-{0}'.format(encap)
        else:
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')
    encap_mode = module.params['encap_mode']
    epg = module.params['epg']
    netflow = aci.boolean(module.params['netflow'], 'enabled', 'disabled')
    primary_encap = module.params['primary_encap']
    if primary_encap is not None:
        if primary_encap in range(1, 4097):
            primary_encap = 'vlan-{0}'.format(primary_encap)
        else:
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')
    resolution_immediacy = module.params['resolution_immediacy']
    state = module.params['state']
    tenant = module.params['tenant']

    if domain_type == 'phys' and vm_provider is not None:
        module.fail_json(msg="Domain type 'phys' cannot have a 'vm_provider'")

    # Compile the full domain for URL building
    if domain_type == 'vmm':
        epg_domain = 'uni/vmmp-{0}/dom-{1}'.format(VM_PROVIDER_MAPPING[vm_provider], domain)
    elif domain_type is not None:
        epg_domain = 'uni/phys-{0}'.format(domain)
    else:
        epg_domain = None

    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{0}'.format(tenant),
            filter_target='eq(fvTenant.name, "{0}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='fvAp',
            aci_rn='ap-{0}'.format(ap),
            filter_target='eq(fvAp.name, "{0}")'.format(ap),
            module_object=ap,
        ),
        subclass_2=dict(
            aci_class='fvAEPg',
            aci_rn='epg-{0}'.format(epg),
            filter_target='eq(fvTenant.name, "{0}")'.format(epg),
            module_object=epg,
        ),
        subclass_3=dict(
            aci_class='fvRsDomAtt',
            aci_rn='rsdomAtt-[{0}]'.format(epg_domain),
            filter_target='eq(fvRsDomAtt.tDn, "{0}")'.format(epg_domain),
            module_object=epg_domain,
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='fvRsDomAtt',
            class_config=dict(
                classPref=allow_useg,
                encap=encap,
                encapMode=encap_mode,
                instrImedcy=deploy_immediacy,
                netflowPref=netflow,
                primaryEncap=primary_encap,
                resImedcy=resolution_immediacy,
            ),
        )

        aci.get_diff(aci_class='fvRsDomAtt')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
