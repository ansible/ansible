#!/usr/bin/python
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.


try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_user
short_description: Manage OpenStack Identity Users
extends_documentation_fragment: openstack
version_added: "2.0"
description:
    - Manage OpenStack Identity users. Users can be created,
      updated or deleted using this module. A user will be updated
      if I(name) matches an existing user and I(state) is present.
      The value for I(name) cannot be updated without deleting and
      re-creating the user.
options:
   name:
     description:
        - Username for the user
     required: true
   password:
     description:
        - Password for the user
     required: true when I(state) is present
     default: None
   email:
     description:
        - Email address for the user
     required: false
     default: None
   default_project:
     description:
        - Project name or ID that the user should be associated with by default
     required: false
     default: None
   domain:
     description:
        - Domain to create the user in if the cloud supports domains
     required: false
     default: None
   enabled:
     description:
        - Is the user enabled
     required: false
     default: True
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Create a user
- os_user:
    cloud: mycloud
    state: present
    name: demouser
    password: secret
    email: demo@example.com
    domain: default
    default_project: demo

# Delete a user
- os_user:
    cloud: mycloud
    state: absent
    name: demouser
'''


RETURN = '''
user:
    description: Dictionary describing the user.
    returned: On success when I(state) is 'present'
    type: dictionary
    contains:
        default_project_id:
            description: User default project ID. Only present with Keystone >= v3.
            type: string
            sample: "4427115787be45f08f0ec22a03bfc735"
        domain_id:
            description: User domain ID. Only present with Keystone >= v3.
            type: string
            sample: "default"
        email:
            description: User email address
            type: string
            sample: "demo@example.com"
        id:
            description: User ID
            type: string
            sample: "f59382db809c43139982ca4189404650"
        name:
            description: User name
            type: string
            sample: "demouser"
'''

def _needs_update(module, user):
    keys = ('email', 'default_project', 'domain', 'enabled')
    for key in keys:
        if module.params[key] is not None and module.params[key] != user.get(key):
            return True

    # We don't get password back in the user object, so assume any supplied
    # password is a change.
    if module.params['password'] is not None:
        return True

    return False

def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        password=dict(required=False, default=None),
        email=dict(required=False, default=None),
        default_project=dict(required=False, default=None),
        domain=dict(required=False, default=None),
        enabled=dict(default=True, type='bool'),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(
        argument_spec,
        required_if=[
            ('state', 'present', ['password'])
        ],
        **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params['name']
    password = module.params['password']
    email = module.params['email']
    default_project = module.params['default_project']
    domain = module.params['domain']
    enabled = module.params['enabled']
    state = module.params['state']

    try:
        cloud = shade.openstack_cloud(**module.params)
        user = cloud.get_user(name)

        project_id = None
        if default_project:
            project = cloud.get_project(default_project)
            if not project:
                module.fail_json(msg='Default project %s is not valid' % default_project)
            project_id = project['id']

        if state == 'present':
            if user is None:
                user = cloud.create_user(
                    name=name, password=password, email=email,
                    default_project=default_project, domain_id=domain,
                    enabled=enabled)
                changed = True
            else:
                if _needs_update(module, user):
                    user = cloud.update_user(
                        user['id'], password=password, email=email,
                        default_project=project_id, domain_id=domain,
                        enabled=enabled)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed, user=user)

        elif state == 'absent':
            if user is None:
                changed=False
            else:
                cloud.delete_user(user['id'])
                changed=True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)

from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *


if __name__ == '__main__':
    main()
