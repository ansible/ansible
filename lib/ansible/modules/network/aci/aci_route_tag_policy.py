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
module: aci_route_tag_policy
short_description: Manage route tag policies on Cisco ACI fabrics
description:
- Manage route tag policies on Cisco ACI fabrics.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The tenant used must exist before using this module in your playbook. The M(aci_tenant) module can be used for this.
options:
  rtp:
    description:
    - The name of the route tag policy.
    required: yes
    aliases: [ name, rtp_name ]
  description:
    description:
    - Description for the route tag policy.
    aliases: [ descr ]
  tenant:
    description:
    - The name of the tenant.
    required: yes
    aliases: [ tenant_name ]
  tag:
    description:
    - The value of the route tag (range 0-4294967295).
    default: '4294967295'
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

# FIXME: Add more, better examples
EXAMPLES = r'''
- aci_route_tag_policy:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    rtp: '{{ rtp_name }}'
    tenant: production
    tag: '{{ tag }}'
    description: '{{ description }}'
'''

RETURN = r'''
#
'''

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        rtp=dict(type='str', required=False, aliases=['name', 'rtp_name']),  # Not required for querying all objects
        tenant=dict(type='str', required=False, aliases=['tenant_name']),  # Not required for quering all objects
        description=dict(type='str', aliases=['descr']),
        tag=dict(type='int'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    rtp = module.params['rtp']
    tenant = module.params['tenant']
    description = module.params['description']
    tag = module.params['tag']
    state = module.params['state']

    aci = ACIModule(module)

    if rtp is not None:
        # Work with a specific object
        if tenant is not None:
            path = 'api/mo/uni/tn-%(tenant)s/rttag-%(rtp)s.json' % module.params
        else:
            path = 'api/class/l3extRouteTagPol.json?query-target-filter=eq(l3extRouteTagPol.name,"%(rtp)s")' % module.params
    elif state == 'query':
        # Query all objects
        if tenant is not None:
            path = 'api/mo/uni/tn-%(tenant)s.json?rsp-subtree=children&rsp-subtree-class=l3extRouteTagPol&rsp-subtree-include=no-scoped' % module.params
        else:
            path = 'api/node/class/l3extRouteTagPol.json'
    else:
        module.fail_json(msg="Parameter 'rtp' is required for state 'absent' or 'present'")

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class='l3extRouteTagPol', class_config=dict(name=rtp, descr=description, tag=tag))

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='l3extRouteTagPol')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
