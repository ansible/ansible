#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': 'preview'
}

DOCUMENTATION = '''
module: pagerduty_user
short_description: Manage PagerDuty users
description:
    - This module will let you manage PagerDuty users. Available actions are creation, deletion, and updating.
version_added: "2.3"
author: "Matty Jones (@mattyjones)"
requirements:
    - PagerDuty API access
options:
    avatar_url:
        description:
            - The url of an avatar for the user
        required: False
        default:  https://static.comicvine.com/uploads/scale_small/0/77/236205-57083-alfred-e-neuman.jpg
        choices:  []
        aliases:  []
        type:     string
    color:
        description:
            - The user color in the UI
        required: False
        default:  green
        choices:  []
        aliases:  []
        type:     string
    desc:
        description:
            - A short description of the user.
        required: False
        default:  Managed by Ansible
        choices:  []
        aliases:  []
        type:     string
    email:
        description:
            - Email of user.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
    job_title:
        description:
            - The job title of the user
        required: False
        default:  ""
        choices:  []
        aliases:  []
        type:     string
    name:
        description:
            - The name of the user
        required: True
        default:  ""
        choices:  []
        aliases:  []
        type:     string
    password:
        description:
            - PagerDuty user password.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
    requester_id:
        description:
            - Email of user making the request.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
    role:
        description:
            - Pagerduty role of the user
        required: False
        default:  limited_user
        choices:  ['admin', 'limited_user', 'owner', 'read_only_user', 'user']
        aliases:  []
        type:     string
    state:
        description:
            - Create or destroy a team.
        required: True
        default:  null
        choices:  [ absent", "present" ]
        aliases:  []
        type:     string
    teams:
        description:
            - Teams the user belongs too
        required: False
        default:  ""
        choices:  []
        aliases:  []
        type:     list
    token:
        description:
            - A pagerduty token, generated on the pagerduty site. Should be used instead of
              user/password combination.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
    time_zone:
        description:
            - The time zone for the user
        required: False
        default:  Etc/UTC
        choices:  []
        aliases:  []
        type:     string
    user_name:
        description:
            - PagerDuty user ID.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
'''

EXAMPLES = '''
- name: Create a new contact method with a username and password
  module: pagerduty_contact_method
    state: present
    email: bob@example.com
    type: sms_contact_method
    label: sms-01
    address: 9785551212
    user_name: bob
    password: superSecretPassword

- name: Delete a contact method with a token
  module: pagerduty_contact_method
    state: absent
    email: bob@example.com
    type: sms_contact_method
    address: 9785551212
    token: xxxxxxxxxx

- name: Update a contact method with a username and password
  module: pagerduty_contact_method
    state: present
    email: bob@example.com
    type: sms_contact_method
    label: sms-02
    address: 9785551212
    user_name: bob
    password: superSecretPassword
'''

RETURN = '''
name:
    description: team name
    returned: changed
    type: string
    sample: engineering
id:
    description: the Pagerduty id
    returned: success
    type: string
    sample: PNQ57GY
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pagerduty_common import *

try:
    import json
except ImportError:
    import simplejson as json


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, type='str',
                       choices=['present', 'absent']),
            desc=dict(default='Managed by Ansible',
                      required=False, type='str'),
            token=dict(required=False, type='str'),
            user_name=dict(required=False, type='str'),
            password=dict(required=False, type='str'),
            avatar_url=dict(
                required=False, default='https://static.comicvine.com/uploads/scale_small/0/77/236205-57083-alfred-e-neuman.jpg',  # nopep8
                type='str'),
            color=dict(required=False, default='green', type='str'),
            email=dict(required=False, default='no-op@example.com', type='str'),
            job_title=dict(required=False, default='', type='str'),
            name=dict(required=False, default='no-op', type='str'),
            role=dict(required=False, default='limited_user', type='str', choices=[  # nopep8
                      'admin', 'limited_user', 'owner', 'read_only_user', 'user']),  # nopep8
            teams=dict(required=False, type='list'),
            time_zone=dict(required=False, default='Etc/UTC', type='str'),
            requester_id=dict(required=False, type='str'),
            generate_list=dict(required=False, type='bool'),
            remote_data=dict(required=False, type='str'),
        ),
        supports_check_mode=True
    )

    acc_state = module.params['state']
    email = module.params['email']
    obj_type = 'users'
    update = False

    if module.params['generate_list']:
        remote_d = fetchRemoteData(obj_type, module)
        with open(module.params['remote_data'], 'w') as f:
            f.write(json.dumps(remote_d))
        module.exit_json(msg="Dumped current pagerduty state to a file")

    # Get a json blob of remote data
    if not module.params['remote_data']:
        remote_d = fetchRemoteData(obj_type, module)
    else:
        with open(module.params['remote_data']) as json_file:
            remote_d = json.load(json_file)

    team_list = []
    if module.params['teams']:
        for t in module.params['teams']:
            team_list.append(t)


    # Create the master list of remote users for easy parsing
    remote_master = createObjectList(obj_type, remote_d)

    # If we don't want the user
    if acc_state == 'absent' and email not in remote_master:
        module.exit_json(changed=False, msg="User not found")
    elif acc_state == 'absent' and len(team_list) > 0 and email in remote_master:
        update = checkUpdateObj(obj_type, module, remote_d)
        if update:
            module.exit_json(
                changed=True, msg="removed the user from the listed teams")
        else:
            module.exit_json(changed=False, msg="no updates detected: %s" %
                             (module.params['email']))

    elif acc_state == 'absent' and not module.params['teams'] and email in remote_master:
        deleteObj(obj_type, remote_d, module)
        module.exit_json(changed=True, msg="removed the user from pagerduty")

    if acc_state == 'present' and email not in remote_master:
        createObj(obj_type, module)
        module.exit_json(changed=True, msg="created the user: %s" %
                         (module.params['email']))
    elif acc_state == 'present' and email in remote_master:
        update = checkUpdateObj(obj_type, module, remote_d)
        if update:
            module.exit_json(changed=True, msg="we updated the user: %s" %
                             (module.params['email']))
        else:
            module.exit_json(changed=False, msg="no updates detected: %s" %
                             (module.params['email']))


if __name__ == '__main__':
    main()
