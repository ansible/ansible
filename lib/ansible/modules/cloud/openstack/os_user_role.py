#!/usr/bin/python
# Copyright (c) 2016 IBM
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_user_role
short_description: Associate OpenStack Identity users and roles
extends_documentation_fragment: openstack
author: "Monty Taylor (@emonty), David Shrewsbury (@Shrews)"
version_added: "2.1"
description:
    - Grant and revoke roles in either project or domain context for
      OpenStack Identity Users.
options:
   role:
     description:
        - Name or ID for the role.
     required: true
   user:
     description:
        - Name or ID for the user. If I(user) is not specified, then
          I(group) is required. Both may not be specified.
   group:
     description:
        - Name or ID for the group. Valid only with keystone version 3.
          If I(group) is not specified, then I(user) is required. Both
          may not be specified.
   project:
     description:
        - Name or ID of the project to scope the role association to.
          If you are using keystone version 2, then this value is required.
   domain:
     description:
        - ID of the domain to scope the role association to. Valid only with
          keystone version 3, and required if I(project) is not specified.
   state:
     description:
       - Should the roles be present or absent on the user.
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
# Grant an admin role on the user admin in the project project1
- os_user_role:
    cloud: mycloud
    user: admin
    role: admin
    project: project1

# Revoke the admin role from the user barney in the newyork domain
- os_user_role:
    cloud: mycloud
    state: absent
    user: barney
    role: admin
    domain: newyork
'''

RETURN = '''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _system_state_change(state, assignment):
    if state == 'present' and not assignment:
        return True
    elif state == 'absent' and assignment:
        return True
    return False


def _build_kwargs(user, group, project, domain):
    kwargs = {}
    if user:
        kwargs['user'] = user
    if group:
        kwargs['group'] = group
    if project:
        kwargs['project'] = project
    if domain:
        kwargs['domain'] = domain
    return kwargs


def main():
    argument_spec = openstack_full_argument_spec(
        role=dict(required=True),
        user=dict(required=False),
        group=dict(required=False),
        project=dict(required=False),
        domain=dict(required=False),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs(
        required_one_of=[
            ['user', 'group']
        ])
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    role = module.params.get('role')
    user = module.params.get('user')
    group = module.params.get('group')
    project = module.params.get('project')
    domain = module.params.get('domain')
    state = module.params.get('state')

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        filters = {}

        r = cloud.get_role(role)
        if r is None:
            module.fail_json(msg="Role %s is not valid" % role)
        filters['role'] = r['id']

        if domain:
            d = cloud.get_domain(domain)
            if d is None:
                module.fail_json(msg="Domain %s is not valid" % domain)
            filters['domain'] = d['id']
        if user:
            if domain:
                u = cloud.get_user(user, domain_id=filters['domain'])
            else:
                u = cloud.get_user(user)

            if u is None:
                module.fail_json(msg="User %s is not valid" % user)
            filters['user'] = u['id']
        if group:
            g = cloud.get_group(group)
            if g is None:
                module.fail_json(msg="Group %s is not valid" % group)
            filters['group'] = g['id']
        if project:
            if domain:
                p = cloud.get_project(project, domain_id=filters['domain'])
                # OpenStack won't allow us to use both a domain and project as
                # filter. Once we identified the project (using the domain as
                # a filter criteria), we need to remove the domain itself from
                # the filters list.
                filters.pop('domain')
            else:
                p = cloud.get_project(project)

            if p is None:
                module.fail_json(msg="Project %s is not valid" % project)
            filters['project'] = p['id']

        assignment = cloud.list_role_assignments(filters=filters)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(state, assignment))

        changed = False

        if state == 'present':
            if not assignment:
                kwargs = _build_kwargs(user, group, project, domain)
                cloud.grant_role(role, **kwargs)
                changed = True

        elif state == 'absent':
            if assignment:
                kwargs = _build_kwargs(user, group, project, domain)
                cloud.revoke_role(role, **kwargs)
                changed = True

        module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
