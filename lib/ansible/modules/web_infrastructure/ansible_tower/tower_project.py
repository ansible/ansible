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
module: tower_project
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower projects
description:
    - Create, update, or destroy Ansible Tower projects. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name string to use for the project.
      required: True
      default: null
    description:
      description:
        - String to use for the project.
      required: False
      default: null
    scm_type:
      description:
        - Type of scm resource.
      required: False
      default: "manual"
      choices: ["manual", "git", "hg", "svn"]
    scm_url:
      description:
        - URL of scm resource.
      required: False
      default: null
    local_path:
      description:
        - The server playbook directory for manual projects.
      required: False
      default: null
    scm_branch:
      description:
        - The branch to use for the scm resource.
      required: False
      default: null
    scm_credential:
      description:
        - Name of the credential to use with this scm resource.
      required: False
      default: null
    scm_clean:
      description:
        - Remove local modifications before updating.
      required: False
      default: False
    scm_delete_on_update:
      description:
        - Remove the repository completely before updating.
      required: False
      default: False
    scm_update_on_launch:
      description:
        - Before an update to the local repository before launching a job with this project.
      required: False
      default: False
    organization:
      description:
        - Primary key of organization for project.
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
    tower_project:
        name: "Foo"
        description: "Foo bar project"
        organization: "test"
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


def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(),
            description = dict(),
            organization = dict(),
            scm_type = dict(choices=['manual', 'git', 'hg', 'svn'], default='manual'),
            scm_url = dict(),
            scm_branch = dict(),
            scm_credential = dict(),
            scm_clean = dict(type='bool', default=False),
            scm_delete_on_update = dict(type='bool', default=False),
            scm_update_on_launch = dict(type='bool', default=False),
            local_path = dict(),
            config_file = dict(),
            state = dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=False
    )

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    name = module.params.get('name')
    description = module.params.get('description')
    organization = module.params.get('organization')
    scm_type = module.params.get('scm_type')
    if scm_type == "manual":
        scm_type = ""
    scm_url = module.params.get('scm_url')
    local_path = module.params.get('local_path')
    scm_branch = module.params.get('scm_branch')
    scm_credential = module.params.get('scm_credential')
    scm_clean = module.params.get('scm_clean')
    scm_delete_on_update = module.params.get('scm_delete_on_update')
    scm_update_on_launch = module.params.get('scm_update_on_launch')
    state = module.params.get('state')

    json_output = {'project': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        project = tower_cli.get_resource('project')
        try:
            if state == 'present':
                org_res = tower_cli.get_resource('organization')
                org = org_res.get(name=organization)

                result = project.modify(name=name, description=description,
                                        organization=org['id'],
                                        scm_type=scm_type, scm_url=scm_url, local_path=local_path,
                                        scm_branch=scm_branch, scm_clean=scm_clean, scm_credential=scm_credential,
                                        scm_delete_on_update=scm_delete_on_update,
                                        scm_update_on_launch=scm_update_on_launch,
                                        create_on_missing=True)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = project.delete(name=name)
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='{} Organization {}'.format(excinfo, organization), changed=False)
        except (exc.ConnectionError, exc.BadRequest) as excinfo:
            module.fail_json(msg='{}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
