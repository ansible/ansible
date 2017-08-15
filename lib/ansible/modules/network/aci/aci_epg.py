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
module: aci_epg
short_description: Manage End point Groups on Cisco ACI APIC
description:
- Direct access to Cisco ACI APIC APIs to manage mapping applications to the network via End point groups.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob Mcgill (@jmcgill298)
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The tenant used must exist before using this module in your playbook. The M(aci_tenant) module can be used for this.
options:
    tenant:
        description:
        - Name of an existing tenant.
        required: yes
        aliases: ['tenant_name']
    app_profile:
        description:
        - Name of an existing application network profile, that will contain the EPGs.
        required: yes
        aliases: ['app_profile_name']
    epg:
        description:
        - Name of the End Point Group Name.
        required: yes
        aliases: ['name', epg_name']
    bridge_domain:
        description:
        - Name of the Bridge Domain being associated with the EPG.
        required: yes
        aliases: ['bd_name']
    priority:
        description:
        - Qos class.
        default: unspecified
        choices: ['level1', 'level2', 'level3', 'unspecified']
    intra_epg_isolation:
        description:
        - Intra EPG Isolation.
        default: unenforced
        choices: ['enforced', 'unenforced']
    description:
        description:
        - Description for the EPG.
        aliases: ['descr']
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
        epg=dict(type="str", aliases=['name', 'epg_name']),
        bridge_domain=dict(type="str", aliases=['bd_name']),
        app_profile=dict(type="str", aliases=['app_profile_name']),
        tenant=dict(type="str", aliases=['tenant_name']),
        description=dict(type="str", required=False, aliases=['descr']),
        priority=dict(choices=['level1', 'level2', 'level3', 'unspecified'], required=False, default='unspecified'),
        intra_epg_isolation=dict(choices=['enforced', 'unenforced'], default='unenforced'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    epg = module.params['epg']
    app_profile = module.params['app_profile']
    tenant = module.params['tenant']
    bridge_domain = module.params['bridge_domain']
    description = module.params['description']
    priority = module.params['priority']
    intra_epg_isolation = module.params['intra_epg_isolation']
    state = module.params['state']

    aci = ACIModule(module)

    if (tenant, app_profile, epg) is not None:
        # Work with a specific EPG
        path = 'api/mo/uni/tn-%(tenant)s/ap-%(app_profile)s/epg-%(epg)s.json' % module.params
    elif state == 'query':
        # Query all EPGs
        path = 'api/class/fvAEPg.json'
    else:
        module.fail_json(msg="Parameter 'tenant', 'app_profile', 'epg' are required for state 'absent' or 'present'")

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class='fvAEPg', class_config=dict(name=epg, descr=description, prio=priority, pcEnfPref=intra_epg_isolation),
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

