#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2018, Nikhil Jain <nikjain@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_settings
author: "Nikhil Jain (@jainnikhil30)"
version_added: "2.7"
short_description: Modify Ansible Tower settings.
description:
    - Modify Ansible Tower settings. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name of setting to modify
      required: True
    value:
      description:
        - Value to be modified for given setting.
      required: True
extends_documentation_fragment: tower
'''

RETURN = ''' # '''

EXAMPLES = '''
- name: Set the value of AWX_PROOT_BASE_PATH
  tower_settings:
    name: AWX_PROOT_BASE_PATH
    value: "/tmp"
  register: testing_settings

- name: Set the value of AWX_PROOT_SHOW_PATHS
  tower_settings:
    name: "AWX_PROOT_SHOW_PATHS"
    value: "'/var/lib/awx/projects/', '/tmp'"
  register: testing_settings

- name: Set the LDAP Auth Bind Password
  tower_settings:
    name: "AUTH_LDAP_BIND_PASSWORD"
    value: "Password"
  no_log: true
'''

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
        value=dict(required=True),
    )

    module = TowerModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    json_output = {}

    name = module.params.get('name')
    value = module.params.get('value')

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        try:
            setting = tower_cli.get_resource('setting')
            result = setting.modify(setting=name, value=value)

            json_output['id'] = result['id']
            json_output['value'] = result['value']

        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to modify the setting: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
