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
short_description: Bind EPGs to Domains on Cisco ACI fabrics (fv:RsDomAtt)
description:
- Bind EPGs to Physical and Virtual Domains on Cisco ACI fabrics.
- More information from the internal APIC class
  I(fv:RsDomAtt) at U(https://developer.cisco.com/media/mim-ref/MO-fvRsDomAtt.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob Mcgill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The C(tenant), C(ap), C(epg), and C(domain) used must exist before using this module in your playbook.
  The M(aci_tenant) M(aci_ap), M(aci_epg) M(aci_domain) modules can be used for this.
options:
  allow_useg:
    description:
    - Allows micro-segmentation.
    - The APIC defaults new EPG to Domain bindings to use C(encap).
    choices: [ encap, useg ]
    default: encap
  ap:
    description:
    - Name of an existing application network profile, that will contain the EPGs.
    aliases: [ app_profile, app_profile_name ]
  deploy_immediacy:
    description:
    - Determines when the policy is pushed to hardware Policy CAM.
    - The APIC defaults new EPG to Domain bindings to C(lazy).
    choices: [ immediate, lazy ]
    default: lazy
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
    - The APIC defaults new EPG to Domain bindings to C(auto).
    choices: [ auto, vlan, vxlan ]
    default: auto
  epg:
    description:
    - Name of the end point group.
    aliases: [ epg_name ]
  netflow:
    description:
    - Determines if netflow should be enabled.
    - The APIC defaults new EPG to Domain binings to C(disabled).
    choices: [ disabled, enabled ]
    default: disabled
  primary_encap:
    description:
    - Determines the primary VLAN ID when using useg.
    choices: [ range from 1 to 4096 ]
  resolution_immediacy:
    description:
    - Determines when the policies should be resolved and available.
    - The APIC defaults new EPG to Domain bindings to C(lazy).
    choices: [ immediate, lazy, pre-provision ]
    default: lazy
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
    choices: [ microsoft, openstack, vmware ]
extends_documentation_fragment: aci
'''

EXAMPLES = r''' # '''

RETURN = r''' # '''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

VM_PROVIDER_MAPPING = dict(microsoft="uni/vmmp-Microsoft/dom-", openstack="uni/vmmp-OpenStack/dom-", vmware="uni/vmmp-VMware/dom-")


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        allow_useg=dict(type='str', choices=['encap', 'useg']),
        ap=dict(type='str', aliases=['app_profile', 'app_profile_name']),
        deploy_immediacy=dict(type='str', choices=['immediate', 'on-demand']),
        domain=dict(type='str', aliases=['domain_name', 'domain_profile']),
        domain_type=dict(type='str', choices=['phys', 'vmm'], aliases=['type']),
        encap=dict(type='int'),
        encap_mode=dict(type='str', choices=['auto', 'vlan', 'vxlan']),
        epg=dict(type='str', aliases=['name', 'epg_name']),
        netflow=dict(type='str', choices=['disabled', 'enabled']),
        primary_encap=dict(type='int'),
        resolution_immediacy=dict(type='str', choices=['immediate', 'lazy', 'pre-provision']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        tenant=dict(type='str', aliases=['tenant_name']),
        vm_provider=dict(type='str', choices=['microsoft', 'openstack', 'vmware']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
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

    allow_useg = module.params['allow_useg']
    ap = module.params['ap']
    deploy_immediacy = module.params['deploy_immediacy']
    domain = module.params['domain']
    domain_type = module.params['domain_type']
    vm_provider = module.params['vm_provider']
    encap = module.params['encap']
    if encap is not None:
        if encap in range(1, 4097):
            encap = 'vlan-{}'.format(encap)
        else:
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')
    encap_mode = module.params['encap_mode']
    epg = module.params['epg']
    netflow = module.params['netflow']
    primary_encap = module.params['primary_encap']
    if primary_encap is not None:
        if primary_encap in range(1, 4097):
            primary_encap = 'vlan-{}'.format(primary_encap)
        else:
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')
    resolution_immediacy = module.params['resolution_immediacy']
    state = module.params['state']
    tenant = module.params['tenant']

    if domain_type == 'phys' and vm_provider is not None:
        module.fail_json(msg="Domain type 'phys' cannot have a 'vm_provider'")

    # Compile the full domain for URL building
    if domain_type == 'vmm':
        epg_domain = '{}{}'.format(VM_PROVIDER_MAPPING[vm_provider], domain)
    elif domain_type is not None:
        epg_domain = 'uni/phys-{}'.format(domain)
    else:
        epg_domain = None

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{}'.format(tenant),
            filter_target='eq(fvTenant.name, "{}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='fvAp',
            aci_rn='ap-{}'.format(ap),
            filter_target='eq(fvAp.name, "{}")'.format(ap),
            module_object=ap,
        ),
        subclass_2=dict(
            aci_class='fvAEPg',
            aci_rn='epg-{}'.format(epg),
            filter_target='eq(fvTenant.name, "{}")'.format(epg),
            module_object=epg,
        ),
        subclass_3=dict(
            aci_class='fvRsDomAtt',
            aci_rn='rsdomAtt-[{}]'.format(epg_domain),
            filter_target='eq(fvRsDomAtt.tDn, "{}")'.format(epg_domain),
            module_object=epg_domain,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
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

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fvRsDomAtt')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
