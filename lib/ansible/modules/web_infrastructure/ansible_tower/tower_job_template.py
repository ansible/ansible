#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_job_template
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower job_template.
description:
    - Create, update, or destroy Ansible Tower job templates. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the job_template.
      required: True
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
    inventory:
      description:
        - Inventory to use for the job_template.
      required: False
      default: null
    project:
      description:
        - Project to use for the job_template.
      required: True
    playbook:
      description:
        - Playbook to use for the job_template.
      required: True
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
    host_config_key:
      description:
        - Allow provisioning callbacks using this host config key.
      required: False
      default: null
    extra_vars_path:
      description:
        - Path to the extra_vars yaml file.
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
    tower_host:
      description:
        - URL to your Tower instance.
      required: False
      default: null
    tower_username:
        description:
          - Username for your Tower instance.
        required: False
        default: null
    tower_password:
        description:
          - Password for your Tower instance.
        required: False
        default: null
    tower_verify_ssl:
        description:
          - Dis/allow insecure connections to Tower. If C(no), SSL certificates will not be validated.
            This should only be used on personally controlled sites using self-signed certificates.
        required: False
        default: True
    tower_config_file:
      description:
        - Path to the Tower config file. See notes.
      required: False
      default: null


requirements:
  - "python >= 2.6"
  - "ansible-tower-cli >= 3.0.3"

notes:
  - If no I(config_file) is provided we will attempt to use the tower-cli library
    defaults to find your Tower host information.
  - I(config_file) should contain Tower configuration in the following format
      host=hostname
      username=username
      password=password
'''


EXAMPLES = '''
- name: Create tower Ping job template
  tower_job_template:
    name: Ping
    job_type: run
    inventory: Local
    project: Demo
    playbook: ping.yml
    machine_credential: Local
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
    from ansible.module_utils.ansible_tower import tower_auth_config, tower_check_mode

    HAS_TOWER_CLI = True
except ImportError:
    HAS_TOWER_CLI = False


def update_fields(p):
    '''This updates the module field names
    to match the field names tower-cli expects to make
    calling of the modify/delete methods easier.
    '''
    params = p.copy()
    field_map = {
        'ask_extra_vars': 'ask_variables_on_launch',
        'ask_limit': 'ask_limit_on_launch',
        'ask_tags': 'ask_tags_on_launch',
        'ask_job_type': 'ask_job_type_on_launch',
        'machine_credential': 'credential',
    }

    params_update = {}
    for old_k, new_k in field_map.items():
        v = params.pop(old_k)
        params_update[new_k] = v

    extra_vars = params.get('extra_vars_path')
    if extra_vars is not None:
        params_update['extra_vars'] = ['@' + extra_vars]

    params.update(params_update)
    return params


def update_resources(module, p):
    params = p.copy()
    identity_map = {
        'project': 'name',
        'inventory': 'name',
        'machine_credential': 'name',
        'network_credential': 'name',
        'cloud_credential': 'name',
    }
    for k, v in identity_map.items():
        try:
            if params[k]:
                key = 'credential' if '_credential' in k else k
                result = tower_cli.get_resource(key).get(**{v: params[k]})
                params[k] = result['id']
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update job template: {0}'.format(excinfo), changed=False)
    return params


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            description=dict(),
            job_type=dict(choices=['run', 'check', 'scan'], required=True),
            inventory=dict(),
            project=dict(required=True),
            playbook=dict(required=True),
            machine_credential=dict(),
            cloud_credential=dict(),
            network_credential=dict(),
            forks=dict(type='int'),
            limit=dict(),
            verbosity=dict(choices=['verbose', 'debug']),
            job_tags=dict(),
            skip_tags=dict(),
            host_config_key=dict(),
            extra_vars_path=dict(type='path', required=False),
            ask_extra_vars=dict(type='bool', default=False),
            ask_limit=dict(type='bool', default=False),
            ask_tags=dict(type='bool', default=False),
            ask_job_type=dict(type='bool', default=False),
            ask_inventory=dict(type='bool', default=False),
            ask_credential=dict(type='bool', default=False),
            become_enabled=dict(type='bool', default=False),
            tower_host=dict(),
            tower_username=dict(),
            tower_password=dict(no_log=True),
            tower_verify_ssl=dict(type='bool', default=True),
            tower_config_file=dict(type='path'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    name = module.params.get('name')
    state = module.params.get('state')
    json_output = {'job_template': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        jt = tower_cli.get_resource('job_template')

        params = update_resources(module, module.params)
        params = update_fields(params)
        params['create_on_missing'] = True

        try:
            if state == 'present':
                result = jt.modify(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = jt.delete(**params)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update job template: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
