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
module: aci_ap
short_description: Manage top level Application Profile (AP) objects on Cisco ACI fabrics (fv:Ap)
description:
- Manage top level Application Profile (AP) objects on Cisco ACI fabrics
- More information from the internal APIC class
  I(fv:Ap) at U(https://developer.cisco.com/media/mim-ref/MO-fvAp.html).
notes:
- This module does not manage EPGs, see M(aci_epg) to do this.
- The C(tenant) used must exist before using this module in your playbook.
  The M(aci_tenant) module can be used for this.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
   tenant:
     description:
     - The name of an existing tenant.
     required: yes
     aliases: [ tenant_name ]
   app_profile:
     description:
     - The name of the application network profile.
     required: yes
     aliases: [ ap, app_profile_name, name ]
   descr:
     description:
     - Description for the AP.
   state:
     description:
     - Use C(present) or C(absent) for adding or removing.
     - Use C(query) for listing an object or multiple objects.
     choices: [ absent, present, query ]
     default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new AP
  aci_ap:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    app_profile: default
    description: default ap
    state: present

- name: Remove an AP
  aci_ap:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    app_profile: default
    state: absent

- name: Query an AP
  aci_ap:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    app_profile: default
    state: query

- name: Query all APs
  aci_ap:
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
        tenant=dict(type='str', aliases=['tenant_name']),  # tenant not required for querying all APs
        app_profile=dict(type='str', aliases=['ap', 'app_profile_name', 'name']),
        description=dict(type='str', aliases=['descr'], required=False),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['state', 'absent', ['tenant', 'app_profile']],
                     ['state', 'present', ['tenant', 'app_profile']]]
    )

    tenant = module.params['tenant']
    app_profile = module.params['app_profile']
    description = module.params['description']
    state = module.params['state']

    aci = ACIModule(module)

    if tenant is not None and app_profile is not None:
        path = 'api/mo/uni/tn-%(tenant)s/ap-%(app_profile)s.json' % module.params
        filter_string = ''
    elif tenant is None and app_profile is None:
        path = 'api/class/fvAp.json'
        filter_string = ''
    elif tenant is not None:
        path = 'api/mo/uni/tn-%(tenant)s.json' % module.params
        filter_string = '?rsp-subtree=children&rsp-subtree-class=fvAp&rsp-subtree-include=no-scoped'
    else:
        path = 'api/class/fvAp.json'
        filter_string = '?query-target-filter=eq(fvAp.name, \"%(app_profile)s\")' % module.params

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing(filter_string=filter_string)

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class='fvAp', class_config=dict(name=app_profile, descr=description))

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fvAp')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
