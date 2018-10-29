#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

# import pydevd
# pydevd.settrace('localhost', port=40015, stdoutToServer=True, stderrToServer=True)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_group
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower group.
description:
    - Create, update, or destroy Ansible Tower groups. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the group.
      required: True
    description:
      description:
        - The description to use for the group.
    inventory:
      description:
        - Inventory the group should be made a member of.
      required: True
    variables:
      description:
        - Variables to use for the group, use C(@) for a file.
    merge_variables:
      description:
        - If set to true will attempt to merge the variables from an existing Group of the same name and inventory.
      required: False
      default: 'no'
      type: bool
      version_added: 2.8
    parent_groups:
      description:
        - List of groups to nest this group under.
      required: False
      default: []
      type: list
      version_added: 2.8
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: Add tower group
  tower_group:
    name: localhost
    description: "Local Host Group"
    inventory: "Local Inventory"
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

import os
import json

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode
from ansible.module_utils.common.dict_transformations import dict_merge

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings

    FAILED_TOWER_IMPORT = False
except ImportError:
    FAILED_TOWER_IMPORT = True

try:
    import yaml

    FAILED_YAML_IMPORT = False
except ImportError:
    FAILED_YAML_IMPORT = True


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        inventory=dict(required=True),
        variables=dict(),
        merge_variables=dict(required=False, default=False, type='bool'),
        parent_groups=dict(required=False, default=[], type='list'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    if FAILED_TOWER_IMPORT:
        module.fail_json(msg="Failed to import tower_cli. Try installing via Pip using 'pip install ansible-tower-cli'")
    if FAILED_YAML_IMPORT:
        module.fail_json(msg="Failed to import yaml. Try installing via Pip using 'pip install PyYAML'")

    name = module.params.get('name')
    inventory = module.params.get('inventory')
    state = module.params.pop('state')
    merge_variables = module.params.pop('merge_variables')
    parent_groups = module.params.pop('parent_groups')

    variables = module.params.get('variables')
    if variables:
        if variables.startswith('@'):
            filename = os.path.expanduser(variables[1:])
            with open(filename, 'r') as f:
                variables = f.read()
    else:
        variables = '{}'

    variables = yaml.safe_load(variables)  # parse in variables so we can later use json.dumps to export RFC compatible json

    json_output = {'group': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        group = tower_cli.get_resource('group')
        params = module.params.copy()
        params['create_on_missing'] = True

        try:
            inv_res = tower_cli.get_resource('inventory')
            inv = inv_res.get(name=inventory)
            params['inventory'] = inv['id']
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update the group, inventory not found: {0}'.format(excinfo), changed=False)

        try:
            for p_group in parent_groups:
                group.get(name=p_group, inventory=params['inventory'])
        except exc.NotFound as excinfo:
            module.fail_json(msg='Failed to associate parent {0}: {1}'.format(p_group, excinfo),
                             changed=False)

        if merge_variables:
            try:
                existing_group = group.get(name=name, inventory=inv['id'])
                existing_vars = yaml.safe_load(existing_group['variables'])
                if not existing_vars:
                    existing_vars = {}
                variables = dict_merge(existing_vars, variables)
            except exc.NotFound:
                json_output['created'] = True
                module.log("Existing group not found, will create")

        params['variables'] = json.dumps(variables)  # export RFC compatible json

        try:
            if state == 'present':
                result = group.modify(**params)
                json_output['id'] = result['id']
                json_output['changed'] = result['changed']
                for p_group in parent_groups:
                    res = group.associate(group=result['id'], parent=p_group, inventory=params['inventory'])
                    if res['changed']:
                        json_output['changed'] = True
            elif state == 'absent':
                result = group.delete(**params)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update the group: {0}'.format(excinfo), changed=False)

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
