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
module: tower_job_template
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower job_template.
description:
    - Create, update, or destroy Ansible Tower job templates. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name string to use for the job_template.
      required: True
      default: null
    description:
      description:
        - Description to use for the job_template.
      required: False
      default: null
    job_type:
      description:
        - The job_type to use for the job_template.
      required: True
      choices: ["run", "check", "scan"]
      default: null
    inventory:
      description:
        - Inventory to use for the job_template.
      required: False
      default: null
    project:
      description:
        - Project to use for the job_template.
      required: True
      default: null
    playbook:
      description:
        - Playbook to use for the job_template.
      required: True
      default: null
    machine_credential:
      description:
        - Machine_credential to use for the job_template.
      required: False
      default: null
    cloud_credential:
      description:
        - Cloud_credential to use for the job_template.
      required: False
      default: null
    network_credential:
      description:
        - The network_credential to use for the job_template.
      required: False
      default: null
    forks:
      description:
        - The number of parallel or simultaneous processes to use while executing the playbook.
      required: False
      default: null
    limit:
      description:
        - A host pattern to further constrain the list of hosts managed or affected by the playbook
      required: False
      default: null
    verbosity:
      description:
        - Control the output level Ansible produces as the playbook runs.
      required: False
      choices: ["verbose", "debug"]
      default: null
    job_tags:
      description:
        - The job_tags to use for the job_template.
      required: False
      default: null
    skip_tags:
      description:
        - The skip_tags to use for the job_template.
      required: False
      default: null
    extra_vars:
      description:
        - The extra_vars to use for the job_template. Use '@' for a file.
      required: False
      default: null
    ask_extra_vars:
      description:
        - Prompt user for extra_vars on launch.
      required: False
      default: False
    ask_tags:
      description:
        - Prompt user for job tags on launch.
      required: False
      default: False
    ask_job_type:
      description:
        - Prompt user for job type on launch.
      required: False
      default: False
    ask_inventory:
      description:
        - Propmt user for inventory on launch.
      required: False
      default: False
    ask_credential:
      description:
        - Prompt user for credential on launch.
      required: False
      default: False
    become_enabled:
      description:
        - Should become_enabled.
      required: False
      default: False
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
    tower_job_template:
        name: Team Name
        description: Team Description
        organization: test-org
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


def update_fields(p):
    '''This updates the module field names
    to match the field names tower-cli expects to make
    calling of the modify/delete methods easier.
    '''
    params = p.copy()
    field_map = {
        'ask_extra_vars': 'ask_variables_on_launch',
        'ask_limit' :'ask_limit_on_launch',
        'ask_tags': 'ask_tags_on_launch',
        'ask_job_type': 'ask_job_type_on_launch',
    }

    params_update = {}
    for old_k, new_k in field_map.items():
        v = params.pop(old_k)
        params_update[new_k] = v
    params.update(params_update)
    return params


def update_resources(module, p):
    params = p.copy()
    identity_map = {
        'project': 'name',
        'machine_credential': 'name',
        'network_credential': 'name',
        'cloud_credential': 'name',
        'inventory': 'name',
    }
    for k,v in identity_map.items():
        try:
            if params[k]:
                key = 'credential' if '_credential' in k else k
                result = tower_cli.get_resource(key).get(**{v:params[k]})
                params[k] = result['id']
        except (exc.NotFound) as excinfo:
                module.fail_json(msg='{} {} {}'.format(excinfo, k, params[k]), changed=False)
    return params


def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            description = dict(),
            job_type = dict(choices=['run', 'check', 'scan'], required=True),
            inventory = dict(),
            project = dict(required=True),
            playbook = dict(required=True),
            machine_credential = dict(),
            cloud_credential = dict(),
            network_credential = dict(),
            forks = dict(type='int'),
            limit = dict(),
            verbosity = dict(choices=['verbose', 'debug']),
            job_tags = dict(),
            skip_tags = dict(),
            extra_vars = dict(type='list', required=False),
            ask_extra_vars = dict(type='bool', default=False),
            ask_limit = dict(type='bool', default=False),
            ask_tags = dict(type='bool', default=False),
            ask_job_type = dict(type='bool', default=False),
            ask_inventory = dict(type='bool', default=False),
            ask_credential = dict(type='bool', default=False),
            become_enabled = dict(type='bool', default=False),
            config_file = dict(),
            state = dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=False
    )

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    name = module.params.get('name')
    state = module.params.get('state')

    json_output = {'job_template': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        jt = tower_cli.get_resource('job_template')

        params = update_fields(module.params)
        params = update_resources(module, params)
        params['create_on_missing'] = True

        try:
            if state == 'present':
                result = jt.modify(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = jt.delete(**params)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='{}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
