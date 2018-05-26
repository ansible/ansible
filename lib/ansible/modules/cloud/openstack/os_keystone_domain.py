#!/usr/bin/python
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_keystone_domain
short_description: Manage OpenStack Identity Domains
author:
    - Monty
    - Haneef Ali
extends_documentation_fragment: openstack
version_added: "2.1"
description:
    - Create, update, or delete OpenStack Identity domains. If a domain
      with the supplied name already exists, it will be updated with the
      new description and enabled attributes.
options:
   name:
     description:
        - Name that has to be given to the instance
     required: true
   description:
     description:
        - Description of the domain
   enabled:
     description:
        - Is the domain enabled
     type: bool
     default: 'yes'
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''

EXAMPLES = '''
# Create a domain
- os_keystone_domain:
     cloud: mycloud
     state: present
     name: demo
     description: Demo Domain

# Delete a domain
- os_keystone_domain:
     cloud: mycloud
     state: absent
     name: demo
'''

RETURN = '''
domain:
    description: Dictionary describing the domain.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        id:
            description: Domain ID.
            type: string
            sample: "474acfe5-be34-494c-b339-50f06aa143e4"
        name:
            description: Domain name.
            type: string
            sample: "demo"
        description:
            description: Domain description.
            type: string
            sample: "Demo Domain"
        enabled:
            description: Domain description.
            type: boolean
            sample: True

id:
    description: The domain ID.
    returned: On success when I(state) is 'present'
    type: string
    sample: "474acfe5-be34-494c-b339-50f06aa143e4"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _needs_update(module, domain):
    if module.params['description'] is not None and \
       domain.description != module.params['description']:
        return True
    if domain.enabled != module.params['enabled']:
        return True
    return False


def _system_state_change(module, domain):
    state = module.params['state']
    if state == 'absent' and domain:
        return True

    if state == 'present':
        if domain is None:
            return True
        return _needs_update(module, domain)

    return False


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        description=dict(default=None),
        enabled=dict(default=True, type='bool'),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    name = module.params['name']
    description = module.params['description']
    enabled = module.params['enabled']
    state = module.params['state']

    sdk, cloud = openstack_cloud_from_module(module)
    try:

        domains = cloud.search_domains(filters=dict(name=name))

        if len(domains) > 1:
            module.fail_json(msg='Domain name %s is not unique' % name)
        elif len(domains) == 1:
            domain = domains[0]
        else:
            domain = None

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, domain))

        if state == 'present':
            if domain is None:
                domain = cloud.create_domain(
                    name=name, description=description, enabled=enabled)
                changed = True
            else:
                if _needs_update(module, domain):
                    domain = cloud.update_domain(
                        domain.id, name=name, description=description,
                        enabled=enabled)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed, domain=domain, id=domain.id)

        elif state == 'absent':
            if domain is None:
                changed = False
            else:
                cloud.delete_domain(domain.id)
                changed = True
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
