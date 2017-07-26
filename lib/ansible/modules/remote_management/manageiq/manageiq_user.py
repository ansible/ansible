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
  action:
    description:
      - Specifies the action to take.
    required: False
    choices: ['create', 'delete', 'edit']
    default: 'create'
  userid:
    description:
      - The unique userid in manageiq, often mentioned as username.
    required: true
  name:
    description:
      - The users' full name.
    required: false
    default: null
  password:
    description:
      - The users' password.
    required: false
    default: null
  group:
    description:
      - The name of the group to which the user belongs.
    required: false
    default: null
  email:
    description:
      - The users' E-mail address.
    required: false
    default: null
'''

EXAMPLES = '''
- name: Create a new user in ManageIQ
  manageiq_user:
    action: 'create'
    userid: 'jdoe'
    name: 'Jane Doe'
    password: 'VerySecret'
    group: 'EvmGroup-user'
    email: 'jdoe@example.com'
    miq:
      url: 'http://example.com:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.manageiq import (
    check_client,
    ManageIQ,
)


class ManageIQUser(object):
    """
        object to execute user management operations in manageiq
    """

    def __init__(self, manageiq):
        self.manageiq = manageiq
        self.api_url = self.manageiq.api_url

    def group_id(self, group):
        """ Search for group id by group name

        Returns:
            the group id, or send a module Fail signal if group not found
        """
        group_obj = self.manageiq.find_collection_resource_by('groups', description=group)
        if not group_obj:  # group doesn't exist
            self.manageiq.module.fail_json(
                msg="Group {group} does not exist in manageiq".format(group=group))

        return group_obj['id']

    def user(self, userid):
        """ Search for user object by userid

        Returns:
            the user, or send a module Fail signal if group not found
        """
        user = self.manageiq.find_collection_resource_by('users', userid=userid)
        if not user:  # user doesn't exist
            self.manageiq.module.fail_json(
                msg="User {userid} does not exist in manageiq".format(userid=userid))

        return user

    def delete_user(self, userid):
        """Deletes a user from manageiq.

        Returns:
            a short message describing the operation executed.
        """
        user = self.user(userid)

        try:
            url = '{api_url}/users/{user_id}'.format(api_url=self.api_url, user_id=user['id'])
            result = self.manageiq.client.post(url, action='delete')
        except Exception as e:
            self.manageiq.module.fail_json(msg="Failed to delete user {userid}: {error}".format(userid=userid, error=e))

        return dict(changed=True, msg=result['message'])

    def edit_user(self, userid, name, group, password, email):
        """Edit a user from manageiq.

        Returns:
            a short message describing the operation executed.
        """
        user = self.user(userid)

        url = '{api_url}/users/{user_id}'.format(api_url=self.api_url, user_id=user['id'])
        resource = dict(userid=userid)
        if group is not None:
            group_id = self.group_id(group)
            resource['group'] = dict(id=group_id)
        if name is not None:
            resource['name'] = name
        if password is not None:
            resource['password'] = password
        if email is not None:
            resource['email'] = email

        try:
            result = self.manageiq.client.post(url, action='edit', resource=resource)
        except Exception as e:
            self.manageiq.module.fail_json(msg="Failed to update user {userid}: {error}".format(userid=userid, error=e))

        return dict(
            changed=True,
            msg="Successfully updated the user {userid}: {user_details}".format(userid=userid, user_details=result))

    def create_user(self, userid, name, group, password, email):
        """Creates the user in manageiq.

        Returns:
            the created user id, name, created_on timestamp,
            updated_on timestamp, userid and current_group_id
        """
        group_id = self.group_id(group)

        url = '{api_url}/users'.format(api_url=self.api_url)
        resource = {'userid': userid, 'name': name, 'password': password, 'group': {'id': group_id}}
        if email is not None:
            resource['email'] = email

        try:
            result = self.manageiq.client.post(url, action='create', resource=resource)
        except Exception as e:
            self.manageiq.module.fail_json(msg="Failed to create user {userid}: {error}".format(userid=userid, error=e))

        return dict(
            changed=True,
            msg="Successfully created the user {userid}: {user_details}".format(userid=userid, user_details=result['results']))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            miq=dict(required=True, type='dict'),
            userid=dict(required=True, type='str'),
            name=dict(),
            password=dict(required=False, type='str', no_log=True),
            group=dict(),
            email=dict(),
            action=dict(choices=['create', 'delete', 'edit'], defualt='create'),
        ),
        required_if=[
            ('action', 'create', ['name', 'password', 'group'])
        ],
    )

    userid = module.params['userid']
    name = module.params['name']
    password = module.params['password']
    group = module.params['group']
    email = module.params['email']
    action = module.params['action']

    manageiq = ManageIQ(module)
    manageiq_user = ManageIQUser(manageiq)

    if action == "delete":
        res_args = manageiq_user.delete_user(userid)

    if action == "edit":
        res_args = manageiq_user.edit_user(userid, name, group, password, email)

    if action == "create":
        res_args = manageiq_user.create_user(userid, name, group, password, email)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
