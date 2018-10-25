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

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        inventory=dict(required=True),
        variables=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params.get('name')
    inventory = module.params.get('inventory')
    state = module.params.pop('state')

    variables = module.params.get('variables')
    if variables:
        if variables.startswith('@'):
            filename = os.path.expanduser(variables[1:])
            with open(filename, 'r') as f:
                variables = f.read()

    json_output = {'group': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        group = tower_cli.get_resource('group')
        try:
            params = module.params.copy()
            params['create_on_missing'] = True
            params['variables'] = variables

            inv_res = tower_cli.get_resource('inventory')
            inv = inv_res.get(name=inventory)
            params['inventory'] = inv['id']

            if state == 'present':
                result = group.modify(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = group.delete(**params)
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update the group, inventory not found: {0}'.format(excinfo), changed=False)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update the group: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
