#!/usr/bin/env python
#coding: utf-8 -*-

# (c) 2016, Wayne Witzel III <wayne@riotousliving.com>
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

DOCUMENTATION = '''
---
module: tower_role
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower role.
description:
    - Create, update, or destroy Ansible Tower roles. See
      U(https://www.ansible.com/tower) for an overview.
options:
    user:
      description:
        - User that receives the permissions specified by the role.
      required: False
      default: null
    team:
      description:
        - Team that receives the permissions specified by the role.
      required: False
      default: null
    role:
      description:
        - The role type to grant/revoke.
      required: True
      choices: ["admin", "read", "member", "owner", "execute", "adhoc", "update", "use", "auditor"]
    target_team:
      description:
        - Team that the role acts on.
      required: False
      default: null
    inventory:
      description:
        - Inventory the role acts on.
      required: False
      default: null
    job_template:
      description:
        - The job_template the role acts on.
      required: False
      default: null
    credential:
      description:
        - Credential the role acts on.
      required: False
      default: null
    organization:
      description:
        - Organiation the role acts on.
      required: False
      default: null
    project:
      description:
        - Project the role acts on.
      required: False
      default: null
    state:
      description:
        - Desired state of the resource.
      required: False
      default: "present"
      choices: ["present", "absent"]
    config_file:
      description:
        - Path to the Tower config file. See notes.
      required: False
      default: null


requirements:
  - "ansible-tower-cli >= 3.0.3"

notes:
  - If no I(config_file) is provided we will attempt to use the tower-cli library
    defaults to find your Tower host information.
  - I(config_file) should contain Tower configuration in the following format:
      host=hostname
      username=username
      password=password
'''


EXAMPLES = '''
# Adding user "jdoe" as a member of the team "My Team"
    tower_role:
        user: jdoe
        target_team: "My Team"
        role: member
        state: present
        config_file: "~/tower_cli.cfg"
'''

import os

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc
    from tower_cli.utils import parser
    from tower_cli.conf import settings

    HAS_TOWER_CLI = True
except ImportError:
    HAS_TOWER_CLI = False


def tower_auth_config(module):
    config_file = module.params.get('config_file')
    if not config_file:
        return {}

    config_file = os.path.expanduser(config_file)
    if not os.path.exists(config_file):
        module.fail_json(msg='file not found: %s' % config_file)
    if os.path.isdir(config_file):
        module.fail_json(msg='directory can not be used as config file: %s' % config_file)

    with open(config_file, 'rb') as f:
        return parser.string_to_dict(f.read())


def update_resources(module, p):
    '''update_resources attempts to fetch any of the resources given
    by name using their unique field (identity)
    '''
    params = p.copy()
    identity_map = {
        'user':'username',
        'team':'name',
        'target_team':'name',
        'inventory':'name',
        'job_template':'name',
        'credential':'name',
        'organization':'name',
        'project':'name',
    }
    for k,v in identity_map.items():
        try:
            if params[k]:
                key = 'team' if k == 'target_team' else k
                result = tower_cli.get_resource(key).get(**{v:params[k]})
                params[k] = result['id']
        except (exc.NotFound) as excinfo:
                module.fail_json(msg='{} {} {}'.format(excinfo, k, params[k]), changed=False)
    return params


def main():
    module = AnsibleModule(
        argument_spec = dict(
            user = dict(),
            team = dict(),
            role = dict(choices=["admin", "read", "member", "owner", "execute", "adhoc", "update", "use", "auditor"]),
            target_team = dict(),
            inventory = dict(),
            job_template = dict(),
            credential = dict(),
            organization = dict(),
            project = dict(),
            config_file = dict(),
            state = dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=False
    )

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    role_type = module.params.pop('role')
    state = module.params.get('state')

    json_output = {'role': role_type, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        role = tower_cli.get_resource('role')

        params = update_resources(module, module.params)
        params['type'] = role_type

        try:
            if state == 'present':
                result = role.grant(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = role.revoke(**params)
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='{}'.format(excinfo), changed=False)
        except (exc.ConnectionError, exc.BadRequest) as excinfo:
            module.fail_json(msg='{}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
