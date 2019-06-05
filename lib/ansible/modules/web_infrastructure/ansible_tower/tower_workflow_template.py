#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2018, Adrien Fleury <fleu42@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_workflow_template
author: "Adrien Fleury (@fleu42)"
version_added: "2.7"
short_description: create, update, or destroy Ansible Tower workflow job template.
description:
    - Create, update, or destroy Ansible Tower workflow job templates. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the workflow job template.
      required: True
    description:
      description:
        - Description to use for the workflow job template.
    organization:
      description:
        - The organization the workflow is linked to.
    inventory:
      description:
        - Name of the inventory to use for the workflow job template.
      version_added: 2.9
    extra_vars:
      description:
        - Specify C(extra_vars) for the template.
      type: dict
    ask_extra_vars:
      description:
        - Prompt user for (extra_vars) on launch.
      version_added: 2.9
      type: bool
      default: 'no'
    ask_inventory:
      description:
        - Prompt user for inventory on launch.
      version_added: 2.9
      type: bool
      default: 'no'
    survey_enabled:
      description:
        - Enable a survey on the workflow job template.
      type: bool
      default: 'no'
    survey_spec:
      description:
        - Survey definition
      version_added: 2.9
      type: dict
      required: False
    survey:
      description:
        - The definition of the survey associated to the workflow.
        - Deprecated in 2.9, will be removed in 2.13. Use parameter C(survey_spec) instead.
      type: dict
    schema:
      description:
        - >
          The schema is YAML-formatted list defining the
          hierarchy structure that connects the nodes. Refer to Tower
          documentation for more information.
      type: list
      required: False
    concurrent_jobs_enabled:
      description:
        - Allow simultaneous runs of the workflow job template.
      version_added: 2.9
      type: bool
      default: 'no'
    allow_simultaneous:
      description:
        - If enabled, simultaneous runs of this job template will be allowed.
        - Deprecated in 2.9, will be removed in 2.13. Use parameter C(concurrent_jobs_enabled) instead.
      type: bool
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
extends_documentation_fragment: tower
notes:
  - JSON for survey_spec can be found in Tower API documentation. See
    U(https://docs.ansible.com/ansible-tower/latest/html/towerapi/api_ref.html)
    for POST operation payload example.
  - Documentation of schema format can be found in tower-cli documentation API reference. See
    U(https://tower-cli.readthedocs.io/en/latest/api_ref/resources/workflow.html) for details.
'''


EXAMPLES = '''
- name: Create workflow template
  tower_workflow_template:
    name: Workflow Template
    description: My very first Workflow Template
    organization: My optional Organization
    schema:
      - job_template: "my-job-1"
        success:
          - job_template: "my-job-2"

- name: Create workflow template with survey
  tower_workflow_template:
    name: workflow-1
    survey_spec:
      name: test survey
      description: test description
      spec:
        - index: 0
          question_name: "my question"
          default: "mydef"
          variable: "myvar"
          type: "text"
          required: false
    schema:
      - job_template: "my-job-1"
        success:
          - job_template: "my-job-2"

- tower_worflow_template:
    name: workflow template
    state: absent
'''

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode, tower_dump_yaml

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass

from ansible.module_utils._text import to_text


def update_fields(module, p):
    '''This updates the module field names
    to match the field names tower-cli expects to make
    calling of the modify/delete methods easier.
    '''
    params = p.copy()
    field_map = {
        'ask_extra_vars': 'ask_variables_on_launch',
        'ask_inventory': 'ask_inventory_on_launch',
        'concurrent_jobs_enabled': 'allow_simultaneous',
    }

    params_update = {}
    for old_k, new_k in field_map.items():
        v = params.pop(old_k)
        params_update[new_k] = v

    extra_vars = params.get('extra_vars')
    schema = params.get('schema')

    if extra_vars is not None:
        params_update['extra_vars'] = [tower_dump_yaml(extra_vars)]

    if schema is not None:
        params_update['schema'] = to_text(schema)

    params.update(params_update)
    return params


def update_resources(module, p):
    params = p.copy()
    identity_map = {
        'inventory': 'name',
        'organization': 'name',
    }

    for k, v in identity_map.items():
        try:
            if params[k]:
                result = tower_cli.get_resource(k).get(**{v: params[k]})
                params[k] = result['id']
            elif k in params:
                # unset empty parameters to avoid ValueError: invalid literal for int() with base 10: ''
                del(params[k])
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update workflow job template: {0}'.format(excinfo), changed=False)
    return params


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(default=''),
        organization=dict(required=False),
        inventory=dict(default=''),
        extra_vars=dict(type='dict', required=False),
        ask_extra_vars=dict(type='bool', default=False),
        ask_inventory=dict(type='bool', default=False),
        schema=dict(type='list', required=False),
        survey_enabled=dict(type='bool', default=False),
        survey_spec=dict(type='dict', required=False),
        survey=dict(type='dict', required=False),
        concurrent_jobs_enabled=dict(type='bool', default=False),
        allow_simultaneous=dict(type='bool', default=False),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    if module.params.get('allow_simultaneous'):
        module.params['concurrent_jobs_enabled'] = module.params['allow_simultaneous']
        module.deprecate("The 'allow_simultaneous' option is being replaced by 'concurrent_jobs_enabled'", version="2.14")

    if module.params.get('survey'):
        module.params['survey_spec'] = module.params['survey']
        module.deprecate("The 'survey' option is being replaced by 'survey_spec'", version="2.14")

    module.params.pop('survey')
    module.params.pop('allow_simultaneous')

    name = module.params.get('name')
    state = module.params.pop('state')
    json_output = {'workflow_template': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        wfjt = tower_cli.get_resource('workflow')

        params = update_resources(module, module.params)
        params = update_fields(module, params)
        params['create_on_missing'] = True

        try:
            if state == 'present':
                result = wfjt.modify(**params)
                json_output['id'] = result['id']
                if params['schema']:
                    wfjt.schema(result['id'], params['schema'])
            elif state == 'absent':
                result = wfjt.delete(**params)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update workflow job template: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
