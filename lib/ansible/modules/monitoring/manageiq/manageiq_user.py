#!/usr/bin/python
#
# (c) 2017, Daniel Korn <korndaniel1@gmail.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: manageiq_user

short_description: Management of users in ManageIQ
extends_documentation_fragment: manageiq
version_added: '2.4'
author: Daniel Korn (@dkorn)
description:
  - The manageiq_user module supports adding, updating and deleting users in ManageIQ.

options:
  name:
    description:
      - The unique userid in manageiq, often mentioned as username
    required: true
    default: null
  fullname:
    description:
      - The users' full name
    required: false
    default: null
  password:
    description:
      - The users' password
    required: false
    default: null
  group:
    description:
      - The name of the group to which the user belongs
    required: false
    default: null
  email:
    description:
      - The users' E-mail address
    required: false
    default: null
  state:
    description:
      - The state of the user
      - On present, it will create the user if it does not exist or update the
        user if the associated data is different
      - On absent, it will delete the user if it exists
    required: False
    choices: ['present', 'absent']
    default: 'present'
'''

EXAMPLES = '''
- name: Create a new user in ManageIQ
  manageiq_user:
    name: 'dkorn'
    fullname: 'Daniel Korn'
    password: '******'
    group: 'EvmGroup-user'
    email: 'dkorn@redhat.com'
    state: 'present'
    miq_url: 'http://localhost:3000'
    miq_username: 'admin'
    miq_password: '******'
    validate_certs: False
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.manageiq as manageiq_utils


class ManageIQUser(object):
    """
        object to execute user management operations in manageiq
    """

    def __init__(self, manageiq):
        self.changed = False
        self.manageiq = manageiq

    def delete_user(self, userid):
        """Deletes the user from manageiq.

        Returns:
            a short message describing the operation executed.
        """
        user = self.manageiq.find_collection_resource_by('users', userid=userid)
        if not user:  # user doesn't exist
            return dict(
                changed=self.changed,
                msg="User {userid} does not exist in manageiq".format(userid=userid))
        try:
            url = '{api_url}/users/{user_id}'.format(api_url=self.manageiq.api_url, user_id=user['id'])
            result = self.manageiq.client.post(url, action='delete')
            self.changed = True
            return dict(changed=self.changed, msg=result['message'])
        except Exception as e:
            self.manageiq.module.fail_json(msg="Failed to delete user {userid}: {error}".format(userid=userid, error=e))

    def user_update_required(self, user, username, group_id, email):
        """ Returns True if the username, group id or email passed for the user
            differ from the user's existing ones, False otherwise.
        """
        if username is not None and user['name'] != username:
            return True
        if group_id is not None and user['current_group_id'] != group_id:
            return True
        if email is not None and user.get('email') != email:
            return True
        return False

    def update_user_if_required(self, user, userid, username, group_id, password, email):
        """Updates the user in manageiq.

        Returns:
            the created user id, name, created_on timestamp,
            updated_on timestamp, userid and current_group_id
        """
        if not self.user_update_required(user, username, group_id, email):
            return dict(
                changed=self.changed,
                msg="User {userid} already exist, no need for updates".format(userid=userid))
        url = '{api_url}/users/{user_id}'.format(api_url=self.manageiq.api_url, user_id=user.id)
        resource = {'userid': userid, 'name': username, 'password': password,
                    'group': {'id': group_id}, 'email': email}
        try:
            result = self.manageiq.client.post(url, action='edit', resource=resource)
        except Exception as e:
            self.manageiq.module.fail_json(msg="Failed to update user {userid}: {error}".format(userid=userid, error=e))
        self.changed = True
        return dict(
            changed=self.changed,
            msg="Successfully updated the user {userid}: {user_details}".format(userid=userid, user_details=result))

    def create_user(self, userid, username, group_id, password, email):
        """Creates the user in manageiq.

        Returns:
            the created user id, name, created_on timestamp,
            updated_on timestamp, userid and current_group_id
        """
        url = '{api_url}/users'.format(api_url=self.manageiq.api_url)
        resource = {'userid': userid, 'name': username, 'password': password,
                    'group': {'id': group_id}, 'email': email}
        try:
            result = self.manageiq.client.post(url, action='create', resource=resource)
        except Exception as e:
            self.manageiq.module.fail_json(msg="Failed to create user {userid}: {error}".format(userid=userid, error=e))
        self.changed = True
        return dict(
            changed=self.changed,
            msg="Successfully created the user {userid}: {user_details}".format(userid=userid, user_details=result['results']))

    def create_or_update_user(self, userid, username, password, group, email):
        """ Create or update a user in manageiq.

        Returns:
            Whether or not a change took place and a message describing the
            operation executed.
        """
        group = self.manageiq.find_collection_resource_by('groups', description=group)
        if not group:  # group doesn't exist
            self.manageiq.module.fail_json(
                msg="Failed to create user {userid}: group {group_name} does not exist in manageiq".format(userid=userid, group_name=group))

        user = self.manageiq.find_collection_resource_by('users', userid=userid)
        if user:  # user already exist
            return self.update_user_if_required(user, userid, username, group['id'], password, email)
        else:
            return self.create_user(userid, username, group['id'], password, email)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            manageiq_utils.manageiq_argument_spec(),
            name=dict(required=True, type='str'),
            fullname=dict(required=False, type='str'),
            password=dict(required=False, type='str', no_log=True),
            group=dict(required=False, type='str'),
            email=dict(required=False, type='str'),
            state=dict(required=False, type='str',
                       choices=['present', 'absent'], defualt='present'),
        ),
        required_if=[
            ('state', 'present', ['fullname', 'group', 'password'])
        ],
    )

    name = module.params['name']
    fullname = module.params['fullname']
    password = module.params['password']
    group = module.params['group']
    email = module.params['email']
    state = module.params['state']

    manageiq = manageiq_utils.ManageIQ(module)
    manageiq_user = ManageIQUser(manageiq)
    if state == "present":
        res_args = manageiq_user.create_or_update_user(name, fullname,
                                                       password, group, email)
    if state == "absent":
        res_args = manageiq_user.delete_user(name)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
