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
    credential:
      description:
        - Credential to use for the group.
    source:
      description:
        - The source to use for this group.
      choices: ["manual", "file", "ec2", "rax", "vmware", "gce", "azure", "azure_rm", "openstack", "satellite6" , "cloudforms", "custom"]
    source_regions:
      description:
        - Regions for cloud provider.
    source_vars:
      description:
        - Override variables from source with variables from this field.
    instance_filters:
      description:
        - Comma-separated list of filter expressions for matching hosts.
    group_by:
      description:
        - Limit groups automatically created from inventory source.
    source_script:
      description:
        - Inventory script to be used when group type is C(custom).
    overwrite:
      description:
        - Delete child groups and hosts not found in source.
      type: bool
      default: 'no'
    overwrite_vars:
      description:
        - Override vars in child groups and hosts with those from external source.
    update_on_launch:
      description:
        - Refresh inventory data from its source each time a job is run.
      type: bool
      default: 'no'
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


from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode, sanitise_and_merge_variables

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings

    FAILED_TOWER_IMPORT = False
except ImportError:
    FAILED_TOWER_IMPORT = True


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        inventory=dict(required=True),
        variables=dict(),
        credential=dict(),
        source=dict(choices=["manual", "file", "ec2", "rax", "vmware",
                             "gce", "azure", "azure_rm", "openstack",
                             "satellite6", "cloudforms", "custom"], default="manual"),
        source_regions=dict(),
        source_vars=dict(),
        instance_filters=dict(),
        group_by=dict(),
        source_script=dict(),
        overwrite=dict(type='bool', default=False),
        overwrite_vars=dict(),
        update_on_launch=dict(type='bool', default=False),
        merge_variables=dict(required=False, default=False, type='bool'),
        parent_groups=dict(required=False, default=[], type='list'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    if FAILED_TOWER_IMPORT:
        module.fail_json(msg="Failed to import tower_cli. Try installing via Pip using 'pip install ansible-tower-cli'")

    name = module.params.get('name')
    inventory = module.params.get('inventory')
    credential = module.params.get('credential')
    state = module.params.pop('state')
    merge_variables = module.params.pop('merge_variables')
    parent_groups = module.params.pop('parent_groups')

    variables = module.params.get('variables')

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
            module.fail_json(msg='Parent group {0} does not exist: {1}'.format(p_group, excinfo),
                             changed=False)

        try:
            existing_group = group.get(name=name, inventory=inv['id'])
        except exc.NotFound:
            existing_group = None
            json_output['created'] = True
            module.log("Existing group not found, will create")

        try:
            if merge_variables and existing_group:
                params['variables'] = sanitise_and_merge_variables(existing_group['variables'], variables)
            else:
                params['variables'] = sanitise_and_merge_variables(variables)
        except TypeError as excinfo:
            module.fail_json(msg='Invalid variable data {0}'.format(excinfo))

        try:
            if credential:
                cred_res = tower_cli.get_resource('credential')
                cred = cred_res.get(name=credential)
                params['credential'] = cred['id']

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
                json_output['changed'] = result['changed']
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update the group: {0}'.format(excinfo), changed=False)

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
