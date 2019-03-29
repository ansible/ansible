#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2019, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: tower_user_info
author:
- Abhijeet Kasurde (@Akasurde)
version_added: "2.8"
short_description: List all Ansible Tower user.
description:
    - List all Ansible Tower users. See U(https://www.ansible.com/tower) for an overview.
options:
    username:
      description:
        - The username of the user.
    first_name:
      description:
        - First name of the user.
    last_name:
      description:
        - Last name of the user.
    email:
      description:
        - Email address of the user.
      required: True
    superuser:
      description:
        - User is a system wide administrator.
      type: bool
      default: 'no'
extends_documentation_fragment: tower
'''

EXAMPLES = '''
- name: List all users
  tower_user:
    tower_config_file: "~/tower_cli.cfg"

- name: List user with username
  tower_user:
    username: testuser1
    tower_config_file: "~/tower_cli.cfg"

- name: List all superusers
  tower_user:
    superuser: True
    tower_config_file: "~/tower_cli.cfg"
'''

RETURN = """
result:
    description: metadata about the all user matching the criteria
    returned: always
    type: dict
    sample: [
        {
            "auth": [],
            "created": "2019-03-29T10:26:13.806024Z",
            "email": "ak@example.com",
            "external_account": null,
            "first_name": "",
            "id": 23,
            "is_superuser": false,
            "is_system_auditor": true,
            "last_name": "",
            "ldap_dn": "",
            "related": {
                "access_list": "/api/v2/users/23/access_list/",
                "activity_stream": "/api/v2/users/23/activity_stream/",
                "admin_of_organizations": "/api/v2/users/23/admin_of_organizations/",
                "authorized_tokens": "/api/v2/users/23/authorized_tokens/",
                "credentials": "/api/v2/users/23/credentials/",
                "organizations": "/api/v2/users/23/organizations/",
                "personal_tokens": "/api/v2/users/23/personal_tokens/",
                "projects": "/api/v2/users/23/projects/",
                "roles": "/api/v2/users/23/roles/",
                "teams": "/api/v2/users/23/teams/",
                "tokens": "/api/v2/users/23/tokens/"
            },
            "summary_fields": {
                "user_capabilities": {
                    "delete": true,
                    "edit": true
                }
            },
            "type": "user",
            "url": "/api/v2/users/23/",
            "username": "abhijeet"
        }
    ]
"""

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.exceptions as exc
    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        username=dict(),
        first_name=dict(),
        last_name=dict(),
        superuser=dict(type='bool', default=False),
        email=dict(),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    superuser = module.params.get('superuser')
    username = module.params.get('username')
    first_name = module.params.get('first_name')
    last_name = module.params.get('last_name')
    email = module.params.get('email')

    json_output = dict()
    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        user = tower_cli.get_resource('user')
        try:
            result = user.list(is_superuser=superuser,
                               username=username,
                               first_name=first_name,
                               last_name=last_name,
                               email=email)
            json_output['result'] = result
        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update the user: {0}'.format(excinfo), changed=False)

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
