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
module: tower_job_template
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower job template.
description:
    - Create, update, or destroy Ansible Tower job templates. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the job template.
      required: True
    description:
      description:
        - Description to use for the job template.
    job_type:
      description:
        - The job type to use for the job template.
      required: True
      choices: ["run", "check", "scan"]
    inventory:
      description:
        - Name of the inventory to use for the job template.
    project:
      description:
        - Name of the project to use for the job template.
      required: True
    playbook:
      description:
        - Path to the playbook to use for the job template within the project provided.
      required: True
    credential:
      description:
        - Name of the credential to use for the job template.
      version_added: 2.7
    vault_credential:
      description:
        - Name of the vault credential to use for the job template.
      version_added: 2.7
    forks:
      description:
        - The number of parallel or simultaneous processes to use while executing the playbook.
    limit:
      description:
        - A host pattern to further constrain the list of hosts managed or affected by the playbook
    verbosity:
      description:
        - Control the output level Ansible produces as the playbook runs. 0 - Normal, 1 - Verbose, 2 - More Verbose, 3 - Debug, 4 - Connection Debug.
      choices: [0, 1, 2, 3, 4]
      default: 0
    extra_vars_path:
      description:
        - Path to the C(extra_vars) YAML file.
    job_tags:
      description:
        - Comma separated list of the tags to use for the job template.
    force_handlers_enabled:
      description:
        - Enable forcing playbook handlers to run even if a task fails.
      version_added: 2.7
      type: bool
      default: 'no'
    skip_tags:
      description:
        - Comma separated list of the tags to skip for the job template.
    start_at_task:
      description:
        - Start the playbook at the task matching this name.
      version_added: 2.7
    diff_mode_enabled:
      description:
        - Enable diff mode for the job template.
      version_added: 2.7
      type: bool
      default: 'no'
    fact_caching_enabled:
      description:
        - Enable use of fact caching for the job template.
      version_added: 2.7
      type: bool
      default: 'no'
    host_config_key:
      description:
        - Allow provisioning callbacks using this host config key.
    ask_diff_mode:
      description:
        - Prompt user to enable diff mode (show changes) to files when supported by modules.
      version_added: 2.7
      type: bool
      default: 'no'
    ask_extra_vars:
      description:
        - Prompt user for (extra_vars) on launch.
      type: bool
      default: 'no'
    ask_limit:
      description:
        - Prompt user for a limit on launch.
      version_added: 2.7
      type: bool
      default: 'no'
    ask_tags:
      description:
        - Prompt user for job tags on launch.
      type: bool
      default: 'no'
    ask_skip_tags:
      description:
        - Prompt user for job tags to skip on launch.
      version_added: 2.7
      type: bool
      default: 'no'
    ask_job_type:
      description:
        - Prompt user for job type on launch.
      type: bool
      default: 'no'
    ask_verbosity:
      description:
        - Prompt user to choose a verbosity level on launch.
      version_added: 2.7
      type: bool
      default: 'no'
    ask_inventory:
      description:
        - Propmt user for inventory on launch.
      type: bool
      default: 'no'
    ask_credential:
      description:
        - Prompt user for credential on launch.
      type: bool
      default: 'no'
    survey_enabled:
      description:
        - Enable a survey on the job template.
      version_added: 2.7
      type: bool
      default: 'no'
    survey_spec:
      description:
        - JSON/YAML dict formatted survey definition.
      version_added: 2.8
      type: dict
      required: False
    become_enabled:
      description:
        - Activate privilege escalation.
      type: bool
      default: 'no'
    concurrent_jobs_enabled:
      description:
        - Allow simultaneous runs of the job template.
      version_added: 2.7
      type: bool
      default: 'no'
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
extends_documentation_fragment: tower
notes:
  - JSON for survey_spec can be found in Tower API Documentation. See
    U(https://docs.ansible.com/ansible-tower/latest/html/towerapi/api_ref.html#/Job_Templates/Job_Templates_job_templates_survey_spec_create)
    for POST operation payload example.
'''


EXAMPLES = '''
- name: Create tower Ping job template
  tower_job_template:
    name: "Ping"
    job_type: "run"
    inventory: "Local"
    project: "Demo"
    playbook: "ping.yml"
    credential: "Local"
    state: "present"
    tower_config_file: "~/tower_cli.cfg"
    survey_enabled: yes
    survey_spec: "{{ lookup('file', 'my_survey.json') }}"
'''

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def update_fields(p):
    '''This updates the module field names
    to match the field names tower-cli expects to make
    calling of the modify/delete methods easier.
    '''
    params = p.copy()
    field_map = {
        'fact_caching_enabled': 'use_fact_cache',
        'ask_diff_mode': 'ask_diff_mode_on_launch',
        'ask_extra_vars': 'ask_variables_on_launch',
        'ask_limit': 'ask_limit_on_launch',
        'ask_tags': 'ask_tags_on_launch',
        'ask_skip_tags': 'ask_skip_tags_on_launch',
        'ask_verbosity': 'ask_verbosity_on_launch',
        'ask_inventory': 'ask_inventory_on_launch',
        'ask_credential': 'ask_credential_on_launch',
        'ask_job_type': 'ask_job_type_on_launch',
        'diff_mode_enabled': 'diff_mode',
        'concurrent_jobs_enabled': 'allow_simultaneous',
        'force_handlers_enabled': 'force_handlers',
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
        'credential': 'name',
        'vault_credential': 'name',
    }
    for k, v in identity_map.items():
        try:
            if params[k]:
                key = 'credential' if '_credential' in k else k
                result = tower_cli.get_resource(key).get(**{v: params[k]})
                params[k] = result['id']
            elif k in params:
                # unset empty parameters to avoid ValueError: invalid literal for int() with base 10: ''
                del(params[k])
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update job template: {0}'.format(excinfo), changed=False)
    return params


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(default=''),
        job_type=dict(choices=['run', 'check', 'scan'], required=True),
        inventory=dict(default=''),
        project=dict(required=True),
        playbook=dict(required=True),
        credential=dict(default=''),
        vault_credential=dict(default=''),
        forks=dict(type='int'),
        limit=dict(default=''),
        verbosity=dict(type='int', choices=[0, 1, 2, 3, 4], default=0),
        extra_vars_path=dict(type='path', required=False),
        job_tags=dict(default=''),
        force_handlers_enabled=dict(type='bool', default=False),
        skip_tags=dict(default=''),
        start_at_task=dict(default=''),
        timeout=dict(type='int', default=0),
        fact_caching_enabled=dict(type='bool', default=False),
        host_config_key=dict(default=''),
        ask_diff_mode=dict(type='bool', default=False),
        ask_extra_vars=dict(type='bool', default=False),
        ask_limit=dict(type='bool', default=False),
        ask_tags=dict(type='bool', default=False),
        ask_skip_tags=dict(type='bool', default=False),
        ask_job_type=dict(type='bool', default=False),
        ask_verbosity=dict(type='bool', default=False),
        ask_inventory=dict(type='bool', default=False),
        ask_credential=dict(type='bool', default=False),
        survey_enabled=dict(type='bool', default=False),
        survey_spec=dict(type='dict', required=False),
        become_enabled=dict(type='bool', default=False),
        diff_mode_enabled=dict(type='bool', default=False),
        concurrent_jobs_enabled=dict(type='bool', default=False),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params.get('name')
    state = module.params.pop('state')
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
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update job template: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
