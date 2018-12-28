#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2018, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: tower_inventory_source_update
author: "John Westcott IV (@john-westcott-iv)"
version_added: "2.8"
short_description: Upate a Tower inventory source
description:
    - Update an inventory source. See
      U(https://www.ansible.com/tower) for an overview.
options:
    inventory:
      description:
       - The inventory which contains the source
      required: True
    source:
      description:
        - The source to update within the inventory
      required: True
    timeout:
      description:
        - The ammount of time to wait for the source to update
      required: False
      default: 300
extends_documentation_fragment: tower
'''

EXAMPLES = '''
- name: Update a source called 'My Source' in 'My Inventory'
  update_inventory_source:
    inventory: "My Inventory"
    source: "My Source"
    type: int
'''

RETURN = '''
changed:
    description: If the update changed Tower
    returned: success
    type: bool
    sample: True
details:
    description: The results of the source update
    returned: success
    type: list
    sample: [
        "Line 1",
        "Line 2"
    ]
'''

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli

    from tower_cli.conf import settings
    from tower_cli.api import client
    from tower_cli.exceptions import ServerError, ConnectionError, BadRequest, TowerCLIError
except ImportError:
    pass


def main():
    argument_spec = dict(
        inventory=dict(required=True),
        source=dict(required=True),
        timeout=dict(required=False, type=int, default=300),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    inventory = module.params.get('inventory')
    source = module.params.get('source')
    timeout = module.params.get('timeout')
    result = {'inventory': inventory, 'source': source}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        # We are going to do more than just a ping chack on this module
        # tower_check_mode(module)

        # First we will do a standard ping check
        try:
            ping_result = client.get('/ping').json()
            # Stuff the version into the results as an FYI
            result['tower_version'] = ping_result['version']
        except(ServerError, ConnectionError, BadRequest) as excinfo:
            result['msg'] = "Failed to reach Tower: {0}".format(excinfo)
            module.fail_json(**result)

        # Now that we know we can connect, lets verify that we can resolve the inventory
        try:
            inventory_object = tower_cli.get_resource("inventory").get(**{'name': inventory})
            result['inventory_id'] = inventory_object['id']
        except TowerCLIError as e:
            result['msg'] = "Failed to find inventory: {0}".format(e)
            module.fail_json(**result)

        # Since we were able to find the inventory, we can now check for the inventory source
        source_resource = tower_cli.get_resource('inventory_source')
        try:
            source_object = source_resource.get(name=source, inventory=inventory_object['id'])
            result['source_id'] = source_object['id']
        except TowerCLIError as e:
            result['msg'] = "Failed to find inventory source: {0}".format(e)
            module.fail_json(**result)

        # if we are in check mode we can return now
        if module.check_mode:
            result['msg'] = "Check mode passed"
            module.exit_json(**result)

        try:
            update_response = source_resource.update(source_object['id'], monitor=False, wait=True, timeout=timeout)
        except Exception as e:
            result['msg'] = 'Failed to update inventory'
            result['exception'] = e.message
            module.fail_json(**result)

        result['changed'] = update_response['changed']
        result['details'] = update_response['result_stdout'].split('\\n')

    module.exit_json(**result)


if __name__ == '__main__':
    main()
