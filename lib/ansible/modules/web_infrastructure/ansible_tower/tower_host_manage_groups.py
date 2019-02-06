#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2019, Andrew J. Huffman <huffy@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_host_manage_groups
author: "Andrew J. Huffman (@ahuffman)"
version_added: "2.8"
short_description: adds/removes an inventory host to/from an inventory group
description:
    - Associate/disassociate an existing Ansible Tower/AWX inventory host to/from an existing Ansible Tower/AWX inventory group.
options:
    name:
      description:
        - The name of the existing inventory host to associate/disassociate with the inventory group.
      required: True
    group:
      description:
        - The name of the existing inventory group to associate/disassociate the  existing inventory host to.
      required: True
    inventory:
      description:
        - The name of the inventory that the host and group belong to.
      required: True
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: "Add a host to a tower group"
  tower_host_manage_groups:
    name: "webhost1"
    group: "Web servers"
    inventory: "My Servers"
    tower_username: "admin"
    tower_password: "{{ pass_from_my_vault }}"
    tower_host: "https://mytowerserver.mydomain.com"
    tower_verify_ssl: False
    tower_config_file: "~/tower_cli.cfg"
    state: "present"

- name: "Remove a host from a tower group"
  tower_host_manage_groups:
    name: "webhost1"
    group: "Web servers"
    inventory: "My Servers"
    tower_username: "admin"
    tower_password: "{{ pass_from_my_vault }}"
    tower_host: "https://mytowerserver.mydomain.com"
    tower_verify_ssl: False
    tower_config_file: "~/tower_cli.cfg"
    state: "absent"
'''

RETURN = ''' # '''


from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        name=dict(required=True),
        group=dict(required=True),
        inventory=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params.get('name')
    group = module.params.get('group')
    inventory = module.params.get('inventory')
    state = module.params.pop('state')

    json_output = {'name': name, 'group': group, 'inventory': inventory, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        try:
            params = module.params.copy()

            # Get existing resources
            inventories = tower_cli.get_resource('inventory')
            hosts = tower_cli.get_resource('host')
            groups = tower_cli.get_resource('group')

            # Find specific inventory
            inv = inventories.get(name=inventory)

            # Find specific host
            host = hosts.get(name=name, inventory=inv['id'])
            params['host'] = host['id']

            # Find specific group
            grp = groups.get(name=group, inventory=inv['id'])
            params['group'] = grp['id']

            if state == "present":
                result = hosts.associate(**params)
                if result['changed']:
                    result['msg'] = 'Successfully associated ' + name + ' with ' + group
                elif not result['changed']:
                    result['msg'] = name + ' is already associated with ' + group
            elif state == "absent":
                result = hosts.disassociate(**params)
                if result['changed']:
                    result['msg'] = 'Successfully disassociated ' + name + ' with ' + group
                elif not result['changed']:
                    result['msg'] = name + ' is already disassociated with ' + group
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update the host, not found: {0}'.format(excinfo), changed=False)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update the host: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    json_output['msg'] = result['msg']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
