#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2018, Adrien Fleury <fleu42@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: tower_workflow_template
author: "Adrien Fleury (@fleu42)"
version_added: "2.7"
short_description: create, update, or destroy Ansible Tower workflow template.
description:
    - Create, update, or destroy Ansible Tower workflows. See
      U(https://www.ansible.com/tower) for an overview.
options:
    allow_simultaneous:
      description:
        - If enabled, simultaneous runs of this job template will be allowed.
      type: bool
    ask_extra_vars:
      description:
        - Prompt user for (extra_vars) on launch.
      type: bool
      version_added: "2.9"
    ask_inventory:
      description:
        - Prompt user for inventory on launch.
      type: bool
      version_added: "2.9"
    description:
      description:
        - The description to use for the workflow.
    extra_vars:
      description:
        - Extra variables used by Ansible in YAML or key=value format.
    inventory:
      description:
        - Name of the inventory to use for the job template.
      version_added: "2.9"
    name:
      description:
        - The name to use for the workflow.
      required: True
    organization:
      description:
        - The organization the workflow is linked to.
    schema:
      description:
        - >
          The schema is a JSON- or YAML-formatted string defining the
          hierarchy structure that connects the nodes. Refer to Tower
          documentation for more information.
    survey_enabled:
      description:
        - Setting that variable will prompt the user for job type on the
          workflow launch.
      type: bool
    survey:
      description:
        - The definition of the survey associated to the workflow.
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- tower_workflow_template:
    name: Workflow Template
    description: My very first Workflow Template
    organization: My optional Organization
    schema: "{{ lookup('file', 'my_workflow.json') }}"

- tower_worflow_template:
    name: Workflow Template
    state: absent
'''


RETURN = ''' # '''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ansible_tower import (
    TowerModule,
    tower_auth_config,
    tower_check_mode
)

try:
    import tower_cli
    import tower_cli.exceptions as exc
    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(required=False),
        extra_vars=dict(required=False),
        organization=dict(required=False),
        allow_simultaneous=dict(type='bool', required=False),
        schema=dict(required=False),
        survey=dict(required=False),
        survey_enabled=dict(type='bool', required=False),
        inventory=dict(required=False),
        ask_inventory=dict(type='bool', required=False),
        ask_extra_vars=dict(type='bool', required=False),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    name = module.params.get('name')
    state = module.params.get('state')

    schema = None
    if module.params.get('schema'):
        schema = module.params.get('schema')

    if schema and state == 'absent':
        module.fail_json(
            msg='Setting schema when state is absent is not allowed',
            changed=False
        )

    json_output = {'workflow_template': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        wfjt_res = tower_cli.get_resource('workflow')
        params = {}
        params['name'] = name

        if module.params.get('description'):
            params['description'] = module.params.get('description')

        if module.params.get('organization'):
            organization_res = tower_cli.get_resource('organization')
            try:
                organization = organization_res.get(
                    name=module.params.get('organization'))
                params['organization'] = organization['id']
            except exc.NotFound as excinfo:
                module.fail_json(
                    msg='Failed to update organization source,'
                    'organization not found: {0}'.format(excinfo),
                    changed=False
                )

        if module.params.get('survey'):
            params['survey_spec'] = module.params.get('survey')

        if module.params.get('ask_extra_vars'):
            params['ask_variables_on_launch'] = module.params.get('ask_extra_vars')

        if module.params.get('ask_inventory'):
            params['ask_inventory_on_launch'] = module.params.get('ask_inventory')

        for key in ('allow_simultaneous', 'extra_vars', 'inventory',
                    'survey_enabled', 'description'):
            if module.params.get(key):
                params[key] = module.params.get(key)

        try:
            if state == 'present':
                params['create_on_missing'] = True
                result = wfjt_res.modify(**params)
                json_output['id'] = result['id']
                if schema:
                    wfjt_res.schema(result['id'], schema)
            elif state == 'absent':
                params['fail_on_missing'] = False
                result = wfjt_res.delete(**params)
        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update workflow template: \
                    {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
