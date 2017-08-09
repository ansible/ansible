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
module: pagerduty_contact_method
short_description: Manage PagerDuty user contact methods
description:
    - This module will let you manage PagerDuty user contact methods. Available actions are creation, deletion, and updating.
version_added: "2.3"
author: "Matty Jones (@mattyjones)"
requirements:
    - PagerDuty API access
options:
    address:
        description:
            - The contact address
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
    email:
        description:
            - Email of user that needs to be updated.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
    label:
        description:
            - A user defined label associated with the method.
        required: True
        default:  null
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
    state:
        description:
            - Create or destroy a team.
        required: True
        default:  null
        choices:  [ absent", "present" ]
        aliases:  []
        type: string
    token:
        description:
            - A pagerduty token, generated on the pagerduty site. Should be used instead of
              user/password combination.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
    type:
        description:
            - The type on contact to create
        required: True
        default:  null
        choices:  ['email_contact_method', 'phone_contact_method', 'push_notification_contact_method', 'sms_contact_method']
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
            token=dict(required=False, type='str'),
            user_name=dict(required=False, type='str'),
            password=dict(required=False, type='str'),
            email=dict(required=True, type='str'),
            address=dict(required=True, type='str'),
            type=dict(required=True, type='str', choices=[
                      'email_contact_method', 'phone_contact_method', 'sms_contact_method']),
            label=dict(required=True, type='str'),
            generate_list=dict(required=False, type='bool'),
            remote_data=dict(required=False, type='str'),
        ),
        supports_check_mode=True
    )

    acc_state = module.params['state']
    email = module.params['email']
    obj_type = 'contact_method'
    update = False



    if module.params['generate_list']:
        remote_d = fetchRemoteData('users', module)
        with open(module.params['remote_data'], 'w') as f:
            f.write(json.dumps(remote_d))
        module.exit_json(msg="Dumped current pagerduty state to a file")

    # Get a json blob of remote data
    if not module.params['remote_data']:
        remote_d = fetchRemoteData('users', module)
    else:
        with open(module.params['remote_data']) as json_file:
            remote_d = json.load(json_file)

    # Create the master list of remote users for easy parsing
    remote_master = createObjectList('users', remote_d)

    # If we don't want the contact_method
    if acc_state == 'absent' and email not in remote_master:
        module.exit_json(changed=False, msg="User not found")

    elif acc_state == 'absent' and email in remote_master:
        delete_obj = deleteObj(obj_type, remote_d, module)
        if delete_obj:
            module.exit_json(
                changed=True, msg="removed the contact method from %s" % (
                    module.params['email']))
        else:
            module.exit_json(changed=False, msg="contact method not detected for %s" %
                             (module.params['email']))

    if acc_state == 'present' and email not in remote_master:
        module.exit_json(changed=False, msg="the user %s must be created first" %
                         (module.params['email']))
    elif acc_state == 'present' and email in remote_master:
        update = checkUpdateObj(obj_type, module, remote_d)
        if update:
            module.exit_json(changed=True, msg="we updated %s's contact methods" %
                             (module.params['email']))
        else:
            module.exit_json(changed=False, msg="no updated contact methods detected for %s" %
                             (module.params['email']))


if __name__ == '__main__':
    main()
