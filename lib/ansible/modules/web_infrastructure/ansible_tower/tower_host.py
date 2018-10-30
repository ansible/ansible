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
module: tower_host
version_added: "2.3"
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Ansible Tower host.
description:
    - Create, update, or destroy Ansible Tower hosts. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the host.
      required: True
    description:
      description:
        - The description to use for the host.
    inventory:
      description:
        - Inventory the host should be made a member of.
      required: True
    enabled:
      description:
        - If the host should be enabled.
      type: bool
      default: 'yes'
    variables:
      description:
        - Variables to use for the host. Use C(@) for a file.
    merge_variables:
      description:
        - If set to true will attempt to merge the variables from an existing Host of the same name and inventory.
      required: False
      default: 'no'
      type: bool
      version_added: 2.8
    groups:
      description:
        - List of groups to put this host in.
      required: False
      default: []
      type: list
      version_added: 2.8
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: Add tower host
  tower_host:
    name: localhost
    description: "Local Host Group"
    inventory: "Local Inventory"
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''


import os

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode, sanitise_and_merge_variables

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        inventory=dict(required=True),
        enabled=dict(type='bool', default=True),
        variables=dict(),
        merge_variables=dict(required=False, default=False, type='bool'),
        groups=dict(required=False, default=[], type='list'),
        state=dict(choices=['present', 'absent'], default='present'),
    )
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params.get('name')
    inventory = module.params.get('inventory')
    state = module.params.pop('state')
    merge_variables = module.params.pop('merge_variables')
    groups = module.params.pop('groups')

    variables = module.params.get('variables')

    json_output = {'host': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        host = tower_cli.get_resource('host')
        group_res = tower_cli.get_resource('group')
        params = module.params.copy()
        params['create_on_missing'] = True

        try:
            inv_res = tower_cli.get_resource('inventory')
            inv = inv_res.get(name=inventory)
            params['inventory'] = inv['id']
        except exc.notFound as excinfo:
            module.fail_json(msg='Failed to update the host, inventory not found: {0}'.format(excinfo), changed=False)

        group_ids = []
        try:
            for group in groups:
                group_ids.append(group_res.get(name=group, inventory=params['inventory'])['id'])
        except exc.NotFound as excinfo:
            module.fail_json(msg='Group {0} does not exist: {1}'.format(group, excinfo), changed=False)

        try:
            existing_host = host.get(name=name, inventory=params['inventory'])
        except exc.NotFound:
            existing_host = None
            json_output['created'] = True
            module.log("Existing host not found, will create")

        try:
            if merge_variables and existing_host:
                params['variables'] = sanitise_and_merge_variables(existing_host['variables'], variables)
            else:
                params['variables'] = sanitise_and_merge_variables(variables)
        except TypeError as excinfo:
            module.fail_json(msg='Invalid variable data {0}'.format(excinfo))

        try:
            if state == 'present':
                result = host.modify(**params)
                json_output['id'] = result['id']
                json_output['changed'] = result['changed']
                for group in group_ids:
                    res = host.associate(host=result['id'], group=group)
                    if res['changed']:
                        json_output['changed'] = True
            elif state == 'absent':
                result = host.delete(name=name, inventory=inv['id'])
                json_output['changed'] = result['changed']
        except (exc.ConnectionError, exc.BadRequest) as excinfo:
            module.fail_json(msg='Failed to update host: {0}'.format(excinfo), changed=False)

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
