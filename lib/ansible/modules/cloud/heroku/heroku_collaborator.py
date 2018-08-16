#!/usr/bin/python

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: heroku_collaborator
short_description: "Add or delete app collaborators on Heroku"
version_added: "2.6"
description:
  - Manages collaborators for Heroku apps.
  - If set to C(present) and heroku user is already collaborator, then do nothing.
  - If set to C(present) and heroku user is not collaborator, then add user to app.
  - If set to C(absent) and heroku user is collaborator, then delete user from app.
author:
  - Marcel Arns (@marns93)
requirements:
  - heroku3
options:
  api_key:
    description:
      - Heroku API key
  apps:
    description:
      - List of Heroku App names
    required: true
  suppress_invitation:
    description:
      - Suppress email invitation when creating collaborator
    type: bool
    default: "no"
  user:
    description:
      - User ID or e-mail
    required: true
  state:
    description:
      - Create or remove the heroku collaborator
    choices: ["present", "absent"]
    default: "present"
notes:
  - C(HEROKU_API_KEY) and C(TF_VAR_HEROKU_API_KEY) env variable can be used instead setting c(api_key).
  - If you use I(--check), you can also pass the I(-v) flag to see affected apps in C(msg), e.g. ["heroku-example-app"].
'''

EXAMPLES = '''
- heroku_collaborator:
    api_key: YOUR_API_KEY
    user: max.mustermann@example.com
    apps: heroku-example-app
    state: present

- heroku_collaborator:
    api_key: YOUR_API_KEY
    user: '{{ item.user }}'
    apps: '{{ item.apps | default(apps) }}'
    suppress_invitation: '{{ item.suppress_invitation | default(suppress_invitation) }}'
    state: '{{ item.state | default("present") }}'
  with_items:
    - { user: 'a.b@example.com' }
    - { state: 'absent', user: 'b.c@example.com', suppress_invitation: false }
    - { user: 'x.y@example.com', apps: ["heroku-example-app"] }
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.heroku import HerokuHelper


def add_or_delete_heroku_collaborator(module, client):
    user = module.params['user']
    state = module.params['state']
    affected_apps = []
    result_state = False

    for app in module.params['apps']:
        if app not in client.apps():
            module.fail_json(msg='App {0} does not exist'.format(app))

        heroku_app = client.apps()[app]

        heroku_collaborator_list = [collaborator.user.email for collaborator in heroku_app.collaborators()]

        if state == 'absent' and user in heroku_collaborator_list:
            if not module.check_mode:
                heroku_app.remove_collaborator(user)
            affected_apps += [app]
            result_state = True
        elif state == 'present' and user not in heroku_collaborator_list:
            if not module.check_mode:
                heroku_app.add_collaborator(user_id_or_email=user, silent=module.params['suppress_invitation'])
            affected_apps += [app]
            result_state = True

    return result_state, affected_apps


def main():
    argument_spec = HerokuHelper.heroku_argument_spec()
    argument_spec.update(
        user=dict(required=True, type='str'),
        apps=dict(required=True, type='list'),
        suppress_invitation=dict(default=False, type='bool'),
        state=dict(default='present', type='str', choices=['present', 'absent']),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    client = HerokuHelper(module).get_heroku_client()

    has_changed, msg = add_or_delete_heroku_collaborator(module, client)
    module.exit_json(changed=has_changed, msg=msg)


if __name__ == '__main__':
    main()
