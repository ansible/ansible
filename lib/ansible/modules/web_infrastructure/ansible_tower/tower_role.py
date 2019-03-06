#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_role
version_added: "2.3"
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Ansible Tower role.
description:
    - Create, update, or destroy Ansible Tower roles. See
      U(https://www.ansible.com/tower) for an overview.
options:
    user:
      description:
        - User that receives the permissions specified by the role.
    team:
      description:
        - Team that receives the permissions specified by the role.
    role:
      description:
        - The role type to grant/revoke.
      required: True
      choices: ["admin", "read", "member", "execute", "adhoc", "update", "use", "auditor"]
    target_team:
      description:
        - Team that the role acts on.
    inventory:
      description:
        - Inventory the role acts on.
    job_template:
      description:
        - The job template the role acts on.
    credential:
      description:
        - Credential the role acts on.
    organization:
      description:
        - Organization the role acts on.
    project:
      description:
        - Project the role acts on.
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: Add jdoe to the member role of My Team
  tower_role:
    user: jdoe
    target_team: "My Team"
    role: member
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def update_resources(module, p):
    '''update_resources attempts to fetch any of the resources given
    by name using their unique field (identity)
    '''
    params = p.copy()
    identity_map = {
        'user': 'username',
        'team': 'name',
        'target_team': 'name',
        'inventory': 'name',
        'job_template': 'name',
        'credential': 'name',
        'organization': 'name',
        'project': 'name',
    }
    for k, v in identity_map.items():
        try:
            if params[k]:
                key = 'team' if k == 'target_team' else k
                result = tower_cli.get_resource(key).get(**{v: params[k]})
                params[k] = result['id']
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update role, {0} not found: {1}'.format(k, excinfo), changed=False)
    return params


def main():

    argument_spec = dict(
        user=dict(),
        team=dict(),
        role=dict(choices=["admin", "read", "member", "execute", "adhoc", "update", "use", "auditor"]),
        target_team=dict(),
        inventory=dict(),
        job_template=dict(),
        credential=dict(),
        organization=dict(),
        project=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    role_type = module.params.pop('role')
    state = module.params.pop('state')

    json_output = {'role': role_type, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        role = tower_cli.get_resource('role')

        params = update_resources(module, module.params)
        params['type'] = role_type

        try:
            if state == 'present':
                result = role.grant(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = role.revoke(**params)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update role: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
