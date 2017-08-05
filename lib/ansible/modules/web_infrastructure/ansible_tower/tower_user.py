#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_user
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower user.
description:
    - Create, update, or destroy Ansible Tower users. See
      U(https://www.ansible.com/tower) for an overview.
options:
    username:
      description:
        - The username of the user.
      required: True
    first_name:
      description:
        - First name of the user.
      required: False
      default: null
    last_name:
      description:
        - Last name of the user.
      required: False
      default: null
    email:
      description:
        - Email address of the user.
      required: True
    password:
      description:
        - Password of the user.
      required: False
      default: null
    superuser:
      description:
        - User is a system wide administator.
      required: False
      default: False
    auditor:
      description:
        - User is a system wide auditor.
      required: False
      default: False
    state:
      description:
        - Desired state of the resource.
      required: False
      default: "present"
      choices: ["present", "absent"]
    tower_host:
      description:
        - URL to your Tower instance.
      required: False
      default: null
    tower_username:
        description:
          - Username for your Tower instance.
        required: False
        default: null
    tower_password:
        description:
          - Password for your Tower instance.
        required: False
        default: null
    tower_verify_ssl:
        description:
          - Dis/allow insecure connections to Tower. If C(no), SSL certificates will not be validated.
            This should only be used on personally controlled sites using self-signed certificates.
        required: False
        default: True
    tower_config_file:
      description:
        - Path to the Tower config file. See notes.
      required: False
      default: null


requirements:
  - "python >= 2.6"
  - "ansible-tower-cli >= 3.0.3"

notes:
  - If no I(config_file) is provided we will attempt to use the tower-cli library
    defaults to find your Tower host information.
  - I(config_file) should contain Tower configuration in the following format
      host=hostname
      username=username
      password=password
'''


EXAMPLES = '''
- name: Add tower user
  tower_user:
    username: jdoe
    password: foobarbaz
    email: jdoe@example.org
    first_name: John
    last_name: Doe
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
    from ansible.module_utils.ansible_tower import tower_auth_config, tower_check_mode

    HAS_TOWER_CLI = True
except ImportError:
    HAS_TOWER_CLI = False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(required=True),
            first_name=dict(),
            last_name=dict(),
            password=dict(no_log=True),
            email=dict(required=True),
            superuser=dict(type='bool', default=False),
            auditor=dict(type='bool', default=False),
            tower_host=dict(),
            tower_username=dict(),
            tower_password=dict(no_log=True),
            tower_verify_ssl=dict(type='bool', default=True),
            tower_config_file=dict(type='path'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    username = module.params.get('username')
    first_name = module.params.get('first_name')
    last_name = module.params.get('last_name')
    password = module.params.get('password')
    email = module.params.get('email')
    superuser = module.params.get('superuser')
    auditor = module.params.get('auditor')
    state = module.params.get('state')

    json_output = {'username': username, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        user = tower_cli.get_resource('user')
        try:
            if state == 'present':
                result = user.modify(username=username, first_name=first_name, last_name=last_name,
                                     email=email, password=password, is_superuser=superuser,
                                     is_auditor=auditor, create_on_missing=True)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = user.delete(username=username)
        except (exc.ConnectionError, exc.BadRequest) as excinfo:
            module.fail_json(msg='Failed to update the user: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
