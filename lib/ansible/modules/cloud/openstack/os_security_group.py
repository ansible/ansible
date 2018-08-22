#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_security_group
short_description: Add/Delete security groups from an OpenStack cloud.
extends_documentation_fragment: openstack
author: "Monty Taylor (@emonty)"
version_added: "2.0"
description:
   - Add or Remove security groups from an OpenStack cloud.
options:
   name:
     description:
        - Name that has to be given to the security group. This module
          requires that security group names be unique.
     required: true
   description:
     description:
        - Long description of the purpose of the security group
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   project:
     description:
        - Unique name or ID of the project.
     required: false
     version_added: "2.7"
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
'''

EXAMPLES = '''
# Create a security group
- os_security_group:
    cloud: mordred
    state: present
    name: foo
    description: security group for foo servers

# Update the existing 'foo' security group description
- os_security_group:
    cloud: mordred
    state: present
    name: foo
    description: updated description for the foo security group

# Create a security group for a given project
- os_security_group:
    cloud: mordred
    state: present
    name: foo
    project: myproj
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _needs_update(module, secgroup):
    """Check for differences in the updatable values.

    NOTE: We don't currently allow name updates.
    """
    if secgroup['description'] != module.params['description']:
        return True
    return False


def _system_state_change(module, secgroup):
    state = module.params['state']
    if state == 'present':
        if not secgroup:
            return True
        return _needs_update(module, secgroup)
    if state == 'absent' and secgroup:
        return True
    return False


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        description=dict(default=''),
        state=dict(default='present', choices=['absent', 'present']),
        project=dict(default=None),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    name = module.params['name']
    state = module.params['state']
    description = module.params['description']
    project = module.params['project']

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        if project is not None:
            proj = cloud.get_project(project)
            if proj is None:
                module.fail_json(msg='Project %s could not be found' % project)
            project_id = proj['id']
        else:
            project_id = cloud.current_project_id

        if project_id:
            filters = {'tenant_id': project_id}
        else:
            filters = None

        secgroup = cloud.get_security_group(name, filters=filters)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, secgroup))

        changed = False
        if state == 'present':
            if not secgroup:
                kwargs = {}
                if project_id:
                    kwargs['project_id'] = project_id
                secgroup = cloud.create_security_group(name, description,
                                                       **kwargs)
                changed = True
            else:
                if _needs_update(module, secgroup):
                    secgroup = cloud.update_security_group(
                        secgroup['id'], description=description)
                    changed = True
            module.exit_json(
                changed=changed, id=secgroup['id'], secgroup=secgroup)

        if state == 'absent':
            if secgroup:
                cloud.delete_security_group(secgroup['id'])
                changed = True
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
