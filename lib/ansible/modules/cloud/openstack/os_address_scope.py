#!/usr/bin/python

# Copyright (c) 2019 Dario Zanzico (git@dariozanzico.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_address_scope
short_description: Manage an openstack address scope
extends_documentation_fragment: openstack
author: "Dario Zanzico (@dariko)"
version_added: "2.8"
description:
- Address scopes can be created, updated and deleted.
- If I(state) is 'query' the module will return informations about all the
  address scopes matching either C(scope_id) or C(name).
- If I(state) is 'present' or 'absent' the module will try to find a resource
  matching C(id) (if given). Failing this it will try to match by (name).
  If more than a single resource is found the module will fail.
options:
  name:
    description:
    - Name that has to be given to the address scope. This module requires
      address scope names to be unique.
  ip_version:
    default: 4
    choices: [4, 6]
    description:
    - IP protocol version for the address scope.
  project_id:
    default: ""
    description:
    - ID of the address scope project.
    - Can not be updated on a existing address scope.
    - Only administrators can create an address scope in a specific project.
  shared:
    description:
    - Whether this address scope is shared or not.
    - Can only be set by administrators.
    - Can't be changed from true to false
    type: bool
  state:
    default: present
    description:
    - Should the resource be present or absent.
    choices:
    - present
    - absent
  availability_zone:
     description:
       - Ignored. Present for backwards compatibility
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''

EXAMPLES = '''
# Create an address scope
- os_address_scope:
    cloud: mycloud
    state: present
    shared: false
    name: testscope
    ip_version: 4

# Share an address scope
- os_address_scope:
    cloud: mycloud
    state: present
    shared: true
    name: testscope
    ip_version: 4

# Delete an address scope
- os_address_scope:
    cloud: mycloud
    state: absent
    name: testscope
'''


RETURN = '''
address_scope:
    description: Dictionary describing the address scope.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        id:
            description: ID of the address scope
            type: string
            sample: "7485d34e-3234-4fe7-86cf-ea9b41a81a47"
        ip_version:
            description: Address scope ip version
            type: int
            sample: 4
        is_shared:
            description: Whether this address scope is shared or not.
            type: bool
            sample: false
        location:
            description: Location information for the address scope
            type: complex
            sample:
                cloud: mycloud
                project:
                    domain_id: default
                    domain_name: Default
                    id: 085ca762378442899f65110062eaf85e
                    name: admin
                region_name: RegionOne
                zone: null
        name:
            description: name of the address scope
            type: string
            sample: "testscope"
        project_id:
            description: ID of the address scope project
            type: string
            sample: "085ca762378442899f65110062eaf85e"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _get_default_project_id(cloud, default_project, module):
    project = cloud.get_project(default_project)
    if not project:
        module.fail_json(msg='Default project %s is not valid' % default_project)

    return project['id']


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        ip_version=dict(default=4, type='int', choices=[4, 6]),
        project_id=dict(required=False, default=None),
        shared=dict(required=False, default=None, type='bool'),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(
        argument_spec,
        **module_kwargs)

    name = module.params['name']
    ip_version = module.params['ip_version']
    project_id = module.params.get('project_id', None)
    shared = module.params.get('shared', None)
    state = module.params['state']

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        address_scope = cloud.network.find_address_scope(name)
        changed = False

        if state == 'present':
            if address_scope is None:
                os_args = {'ip_version': ip_version}
                if project_id:
                    os_args['project_id'] = project_id
                if name:
                    os_args['name'] = name
                if shared:
                    os_args['shared'] = shared
                address_scope = cloud.network.create_address_scope(**os_args)
                changed = True
            else:
                if (project_id is not None) and \
                        (address_scope.project_id != project_id):
                    module.fail_json(
                        msg='Address scope %s already present in project '
                        '%s (requested %s)' %
                        (name, address_scope.project_id, project_id))
                if ip_version != address_scope.ip_version:
                    module.fail_json(msg='Cannot change address scope ip version')
                if (shared is not None) and \
                        (address_scope.is_shared != shared):
                    if not shared:
                        module.fail_json(msg='Cannot unshare address scope')
                    else:
                        address_scope = cloud.network.update_address_scope(
                            address_scope, shared=shared)
                        changed = True
            module.exit_json(changed=changed, address_scope=address_scope)
        elif state == 'absent':
            if address_scope is not None:
                cloud.network.delete_address_scope(address_scope['id'])
                changed = True
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == '__main__':
    main()
