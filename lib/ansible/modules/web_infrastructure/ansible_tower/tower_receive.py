#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_receive
author: "John Westcott IV (@john-westcott-iv)"
version_added: "2.8"
short_description: Receive assets from Ansible Tower.
description:
    - Receive assets from Ansible Tower. See
      U(https://www.ansible.com/tower) for an overview.
options:
    all:
      description:
        - Export all assets
      type: bool
      default: 'False'
    organization:
      description:
        - List of organization names to export
      default: []
    user:
      description:
        - List of user names to export
      default: []
    team:
      description:
        - List of team names to export
      default: []
    credential_type:
      description:
        - List of credential type names to export
      default: []
    credential:
      description:
        - List of credential names to export
      default: []
    notification_template:
      description:
        - List of notification template names to export
      default: []
    inventory_script:
      description:
        - List of inventory script names to export
      default: []
    inventory:
      description:
        - List of inventory names to export
      default: []
    project:
      description:
        - List of project names to export
      default: []
    job_template:
      description:
        - List of job template names to export
      default: []
    workflow:
      description:
        - List of workflow names to export
      default: []

requirements:
  - "ansible-tower-cli >= 3.3.0"

notes:
  - Specifying a name of "all" for any asset type will export all items of that asset type.

extends_documentation_fragment: tower
'''

EXAMPLES = '''
- name: Export all tower assets
  tower_receive:
    all: True
    tower_config_file: "~/tower_cli.cfg"

- name: Export all inventories
  tower_receive:
    inventory:
      - all

- name: Export a job template named "My Template" and all Credentials
  tower_receive:
    job_template:
      - "My Template"
    credential:
      - all
'''

RETURN = '''
assets:
    description: The exported assets
    returned: success
    type: dict
    sample: [ {}, {} ]
'''

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, HAS_TOWER_CLI

try:
    from tower_cli.cli.transfer.receive import Receiver
    from tower_cli.cli.transfer.common import SEND_ORDER
    from tower_cli.utils.exceptions import TowerCLIError

    from tower_cli.conf import settings
    TOWER_CLI_HAS_EXPORT = True
except ImportError:
    TOWER_CLI_HAS_EXPORT = False


def main():
    argument_spec = dict(
        all=dict(type='bool', default=False),
        credential=dict(type='list', default=[]),
        credential_type=dict(type='list', default=[]),
        inventory=dict(type='list', default=[]),
        inventory_script=dict(type='list', default=[]),
        job_template=dict(type='list', default=[]),
        notification_template=dict(type='list', default=[]),
        organization=dict(type='list', default=[]),
        project=dict(type='list', default=[]),
        team=dict(type='list', default=[]),
        user=dict(type='list', default=[]),
        workflow=dict(type='list', default=[]),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    if not TOWER_CLI_HAS_EXPORT:
        module.fail_json(msg='ansible-tower-cli version does not support export')

    export_all = module.params.get('all')
    assets_to_export = {}
    for asset_type in SEND_ORDER:
        assets_to_export[asset_type] = module.params.get(asset_type)

    result = dict(
        assets=None,
        changed=False,
        message='',
    )

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        try:
            receiver = Receiver()
            result['assets'] = receiver.export_assets(all=export_all, asset_input=assets_to_export)
            module.exit_json(**result)
        except TowerCLIError as e:
            result['message'] = e.message
            module.fail_json(msg='Receive Failed', **result)


if __name__ == '__main__':
    main()
