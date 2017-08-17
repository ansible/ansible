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
module: aci_epg
short_description: Manage End Point Groups (EPG) on Cisco ACI fabrics (fv:AEPg)
description:
- Manage End Point Groups (EPG) on Cisco ACI fabrics.
- More information from the internal APIC class
  I(fv:AEPg) at U(https://developer.cisco.com/media/mim-ref/MO-fvAEPg.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob Mcgill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The C(tenant) and C(app_profile) used must exist before using this module in your playbook.
  The M(aci_tenant) and M(aci_ap) modules can be used for this.
options:
  tenant:
    description:
    - Name of an existing tenant.
    aliases: [ tenant_name ]
  app_profile:
    description:
    - Name of an existing application network profile, that will contain the EPGs.
    required: yes
    aliases: [ app_profile_name ]
  epg:
    description:
    - Name of the end point group.
    required: yes
    aliases: [ name, epg_name ]
  bridge_domain:
    description:
    - Name of the bridge domain being associated with the EPG.
    required: yes
    aliases: [ bd_name ]
  priority:
    description:
    - QoS class.
    choices: [ level1, level2, level3, unspecified ]
    default: unspecified
  intra_epg_isolation:
    description:
    - Intra EPG Isolation.
    choices: [ enforced, unenforced ]
    default: unenforced
  description:
    description:
    - Description for the EPG.
    aliases: [ descr ]
  fwd_control:
    description:
    - The forwarding control used by the EPG.
    - The APIC defaults new EPGs to none.
    choices: [ none, proxy-arp ]
    default: none
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new EPG
  aci_epg:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    app_profile: default
    epg: app_epg
    description: application EPG
    bridge_domain: vlan_bd
    priority: unspecified
    intra_epg_isolation: unenforced
    state: present

- name: Remove an EPG
  aci_epg:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    app_profile: default
    epg: app_epg
    state: absent

- name: Query an EPG
  aci_epg:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    app_profile: default
    epg: app_epg
    state: query

- name: Query all EPgs
  aci_epg:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: query
'''

RETURN = r'''
#
'''

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        epg=dict(type='str', aliases=['name', 'epg_name']),
        bridge_domain=dict(type='str', aliases=['bd_name']),
        app_profile=dict(type='str', aliases=['app_profile_name']),
        tenant=dict(type='str', aliases=['tenant_name']),
        description=dict(type='str', aliases=['descr']),
        priority=dict(type='str', choices=['level1', 'level2', 'level3', 'unspecified']),
        intra_epg_isolation=dict(choices=['enforced', 'unenforced']),
        fwd_control=dict(type='str', choices=['none', 'proxy-arp']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['state', 'absent', ['app_profile', 'epg', 'tenant']],
                     ['state', 'present', ['app_profile', 'epg', 'tenant']]]
    )

    epg = module.params['epg']
    # app_profile = module.params['app_profile']
    # tenant = module.params['tenant']
    bridge_domain = module.params['bridge_domain']
    description = module.params['description']
    priority = module.params['priority']
    intra_epg_isolation = module.params['intra_epg_isolation']
    fwd_control = module.params['fwd_control']
    state = module.params['state']

    aci = ACIModule(module)

    # TODO: Add logic to handle multiple input variations when query
    if state != 'query':
        # Work with a specific EPG
        path = 'api/mo/uni/tn-%(tenant)s/ap-%(app_profile)s/epg-%(epg)s.json' % module.params
        filter_string = '?rsp-subtree=children&rsp-subtree-class=fvRsBd&rsp-prop-include=config-only'
    else:
        # Query all EPGs
        path = 'api/class/fvAEPg.json'
        filter_string = '?rsp-subtree=children&rsp-subtree-class=fvRsBd'

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing(filter_string=filter_string)

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class='fvAEPg', class_config=dict(name=epg, descr=description, prio=priority, pcEnfPref=intra_epg_isolation,
                                                          fwdCtrl=fwd_control),
                    child_configs=[dict(fvRsBd=dict(attributes=dict(tnFvBDName=bridge_domain)))])

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fvAEPg')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
