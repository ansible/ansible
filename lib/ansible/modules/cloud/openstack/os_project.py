#!/usr/bin/python
# Copyright (c) 2015 IBM Corporation
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_project
short_description: Manage OpenStack Projects
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Alberto Gireud (@agireud)"
description:
    - Manage OpenStack Projects. Projects can be created,
      updated or deleted using this module. A project will be updated
      if I(name) matches an existing project and I(state) is present.
      The value for I(name) cannot be updated without deleting and
      re-creating the project.
options:
   name:
     description:
        - Name for the project
     required: true
   description:
     description:
        - Description for the project
     required: false
     default: None
   domain_id:
     description:
        - Domain id to create the project in if the cloud supports domains.
          The domain_id parameter requires shade >= 1.8.0
     required: false
     default: None
     aliases: ['domain']
   enabled:
     description:
        - Is the project enabled
     required: false
     default: True
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Create a project
- os_project:
    cloud: mycloud
    state: present
    name: demoproject
    description: demodescription
    domain_id: demoid
    enabled: True

# Delete a project
- os_project:
    cloud: mycloud
    state: absent
    name: demoproject
'''


RETURN = '''
project:
    description: Dictionary describing the project.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        id:
            description: Project ID
            type: string
            sample: "f59382db809c43139982ca4189404650"
        name:
            description: Project name
            type: string
            sample: "demoproject"
        description:
            description: Project description
            type: string
            sample: "demodescription"
        enabled:
            description: Boolean to indicate if project is enabled
            type: bool
            sample: True
'''

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from distutils.version import StrictVersion


def _needs_update(module, project):
    keys = ('description', 'enabled')
    for key in keys:
        if module.params[key] is not None and module.params[key] != project.get(key):
            return True

    return False

def _system_state_change(module, project):
    state = module.params['state']
    if state == 'present':
        if project is None:
            changed = True
        else:
            if _needs_update(module, project):
                changed = True
            else:
                changed = False

    elif state == 'absent':
        if project is None:
            changed=False
        else:
            changed=True

    return changed

def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        description=dict(required=False, default=None),
        domain_id=dict(required=False, default=None, aliases=['domain']),
        enabled=dict(default=True, type='bool'),
        state=dict(default='present', choices=['absent', 'present'])
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        **module_kwargs
    )

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params['name']
    description = module.params['description']
    domain = module.params.pop('domain_id')
    enabled = module.params['enabled']
    state = module.params['state']

    if domain and StrictVersion(shade.__version__) < StrictVersion('1.8.0'):
        module.fail_json(msg="The domain argument requires shade >=1.8.0")

    try:
        if domain:
            opcloud = shade.operator_cloud(**module.params)
            try:
                # We assume admin is passing domain id
                dom = opcloud.get_domain(domain)['id']
                domain = dom
            except:
                # If we fail, maybe admin is passing a domain name.
                # Note that domains have unique names, just like id.
                try:
                    dom = opcloud.search_domains(filters={'name': domain})[0]['id']
                    domain = dom
                except:
                    # Ok, let's hope the user is non-admin and passing a sane id
                    pass

        cloud = shade.openstack_cloud(**module.params)

        if domain:
            project = cloud.get_project(name, domain_id=domain)
        else:
            project = cloud.get_project(name)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, project))

        if state == 'present':
            if project is None:
                project = cloud.create_project(
                    name=name, description=description,
                    domain_id=domain,
                    enabled=enabled)
                changed = True
            else:
                if _needs_update(module, project):
                    project = cloud.update_project(
                        project['id'], description=description,
                        enabled=enabled)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed, project=project)

        elif state == 'absent':
            if project is None:
                changed=False
            else:
                cloud.delete_project(project['id'])
                changed=True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message, extra_data=e.extra_data)

from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
