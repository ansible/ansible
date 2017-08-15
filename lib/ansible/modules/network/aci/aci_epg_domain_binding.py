#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_epg_domain_binding
short_description: Manage EPG to Domain bindings on Cisco ACI fabrics
description:
- Manage EPG to Physical and Virtual Domains on Cisco ACI fabrics.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob Mcgill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The C(tenant), C(app_profile), C(epg), and C(domain) used must exist before using this module in your playbook.
  The M(aci_tenant) M(aci_anp), M(aci_epg) M(aci_domain) modules can be used for this.
options:
  allow_useg:
    description:
    - Allows micro-segmentation.
    - The APIC defaults new EPG to Domain bindings to use encap
    choices: [ encap, useg ]
    default: encap
  app_profile:
    description:
    - Name of an existing application network profile, that will contain the EPGs.
    aliases: [ app_profile_name ]
  deploy_immediacy:
    description:
    - Determines when the policy is pushed to hardware Policy CAM.
    - The APIC defaults new EPG to Domain bindings to lazy.
    choices: [ immediate, lazy ]
    default: lazy
  domain_profile:
    description:
    - Name of the physical or virtual domain being associated with the EPG.
    aliases: [ domain_name ]
  domain_type:
    description:
    - Determines if the Domain is physical (phys) or virtual (vmm).
    choices: [ phys, vmm ]
    aliases: [ domain ]
  encap:
    description:
    - The VLAN encapsulation for the EPG when binding a VMM Domain with static encap_mode.
    - This acts as the secondary encap when using useg.
    choices: [ range from 1 to 4096 ]
  encap_mode:
    description:
    - The ecapsulataion method to be used.
    - The APIC defaults new EPG to Domain bindings to be auto.
    choices: [ auto, vlan, vxlan ]
    default: auto
  epg:
    description:
    - Name of the end point group.
    aliases: [ epg_name ]
  netflow:
    description:
    - Determines if netflow should be enabled.
    - The APIC defaults new EPG to Domain binings to be disabled.
    choices: [ disabled, enabled ]
    default: disabled
  primary_encap:
    description:
    - Determines the primary VLAN ID when using useg.
    choices: [ range from 1 to 4096 ]
  resolution_immediacy:
    description:
    - Determines when the policies should be resolved and available.
    - The APIC defaults new EPG to Domain bindings to lazy.
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
extends_documentation_fragment: aci
'''

EXAMPLES = r''' # '''

RETURN = r''' # '''

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        allow_useg=dict(type='str', choices=['encap', 'useg']),
        app_profile=dict(type='str', aliases=['app_profile_name']),
        deploy_immediacy=dict(type='str', choices=['immediate', 'on-demand']),
        domain_profile=dict(type='str', aliases=['domain_name']),
        domain_type=dict(type='str', choices=['phys', 'vmm'], aliases=['domain']),
        encap=dict(type='int'),
        encap_mode=dict(type='str', choices=['auto', 'vlan', 'vxlan']),
        epg=dict(type='str', aliases=['name', 'epg_name']),
        netflow=dict(type='str', choices=['disabled', 'enabled']),
        primary_encap=dict(type='int'),
        resolution_immediacy=dict(type='str', choices=['immdediate', 'lazy', 'pre-provision']),
        tenant=dict(type='str', aliases=['tenant_name']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['state', 'absent', ['app_profile', 'domain_profile', 'domain_type', 'epg', 'tenant']],
                     ['state', 'present', ['app_profile', 'domain_profile', 'domain_type', 'epg', 'tenant']]]
    )

    allow_useg = module.params['allow_useg']
    # app_profile = module.params['app_profile']
    deploy_immediacy = module.params['deploy_immediacy']
    # domain_profile = module.params['domain_profile']
    domain_type = module.params['domain_type']
    if domain_type == 'vmm':
        module.params["domain_type"] = 'vmmp-VMware/dom'
    encap = module.params['encap']
    if encap is not None:
        if encap in range(1, 4097):
            encap = 'vlan-{}'.format(encap)
        else:
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')
    encap_mode = module.params['encap_mode']
    # epg = module.params['epg']
    # tenant = module.params['tenant']
    netflow = module.params['netflow']
    primary_encap = module.params['primary_encap']
    if primary_encap is not None:
        if primary_encap in range(1, 4097):
            primary_encap = 'vlan-{}'.format(primary_encap)
        else:
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')
    resolution_immediacy = module.params['resolution_immediacy']
    state = module.params['state']

    aci = ACIModule(module)

    # TODO: Add logic to handle multiple input variations when query
    if state != 'query':
        # Work with a specific EPG
        path = ('api/mo/uni/tn-%(tenant)s/ap-%(app_profile)s/epg-%(epg)s/'
                'rsdomAtt-[uni/%(domain_type)s-%(domain_profile)s].json') % module.params
    else:
        # Query all EPGs
        path = 'api/class/fvRsDomAtt.json'

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class='fvRsDomAtt',
                    class_config=dict(classPref=allow_useg, encap=encap, encapMode=encap_mode, instrImedcy=deploy_immediacy,
                                      netflowPref=netflow, primaryEncap=primary_encap, resImedcy=resolution_immediacy))

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fvRsDomAtt')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
