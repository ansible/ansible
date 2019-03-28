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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: manageiq_user

short_description: Management of users in ManageIQ.
extends_documentation_fragment: manageiq
version_added: '2.4'
author: Daniel Korn (@dkorn)
description:
  - The manageiq_user module supports adding, updating and deleting users in ManageIQ.

options:
  state:
    description:
      - absent - user should not exist, present - user should be.
    choices: ['absent', 'present']
    default: 'present'
  userid:
    description:
      - The unique userid in manageiq, often mentioned as username.
    required: true
  name:
    description:
      - The users' full name.
  password:
    description:
      - The users' password.
  group:
    description:
      - The name of the group to which the user belongs.
  email:
    description:
      - The users' E-mail address.
  update_password:
    default: always
    choices: ['always', 'on_create']
    description:
      - C(always) will update passwords unconditionally.  C(on_create) will only set the password for a newly created user.
    version_added: '2.5'
'''

EXAMPLES = '''
- name: Create a new user in ManageIQ
  manageiq_user:
    userid: 'jdoe'
    name: 'Jane Doe'
    password: 'VerySecret'
    group: 'EvmGroup-user'
    email: 'jdoe@example.com'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False

- name: Create a new user in ManageIQ using a token
  manageiq_user:
    userid: 'jdoe'
    name: 'Jane Doe'
    password: 'VerySecret'
    group: 'EvmGroup-user'
    email: 'jdoe@example.com'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      token: 'sometoken'
      validate_certs: False

- name: Delete a user in ManageIQ
  manageiq_user:
    state: 'absent'
    userid: 'jdoe'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False

- name: Delete a user in ManageIQ using a token
  manageiq_user:
    state: 'absent'
    userid: 'jdoe'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      token: 'sometoken'
      validate_certs: False

- name: Update email of user in ManageIQ
  manageiq_user:
    userid: 'jdoe'
    email: 'jaustine@example.com'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False

- name: Update email of user in ManageIQ using a token
  manageiq_user:
    userid: 'jdoe'
    email: 'jaustine@example.com'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      token: 'sometoken'
      validate_certs: False
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.manageiq import ManageIQ, manageiq_argument_spec


class ManageIQUser(object):
    """
        Object to execute user management operations in manageiq.
    """

    def __init__(self, manageiq):
        self.manageiq = manageiq

        self.module = self.manageiq.module
        self.api_url = self.manageiq.api_url
        self.client = self.manageiq.client

    def group_id(self, description):
        """ Search for group id by group description.

        Returns:
            the group id, or send a module Fail signal if group not found.
        """
        group = self.manageiq.find_collection_resource_by('groups', description=description)
        if not group:  # group doesn't exist
            self.module.fail_json(
                msg="group %s does not exist in manageiq" % (description))

        return group['id']

    def user(self, userid):
        """ Search for user object by userid.

        Returns:
            the user, or None if user not found.
        """
        return self.manageiq.find_collection_resource_by('users', userid=userid)

    def compare_user(self, user, name, group_id, password, email):
        """ Compare user fields with new field values.

        Returns:
            false if user fields have some difference from new fields, true o/w.
        """
        found_difference = (
            (name and user['name'] != name) or
            (password is not None) or
            (email and user['email'] != email) or
            (group_id and user['current_group_id'] != group_id)
        )

        return not found_difference

    def delete_user(self, user):
        """ Deletes a user from manageiq.

        Returns:
            a short message describing the operation executed.
        """
        try:
            url = '%s/users/%s' % (self.api_url, user['id'])
            result = self.client.post(url, action='delete')
        except Exception as e:
            self.module.fail_json(msg="failed to delete user %s: %s" % (user['userid'], str(e)))

        return dict(changed=True, msg=result['message'])

    def edit_user(self, user, name, group, password, email):
        """ Edit a user from manageiq.

        Returns:
            a short message describing the operation executed.
        """
        group_id = None
        url = '%s/users/%s' % (self.api_url, user['id'])

        resource = dict(userid=user['userid'])
        if group is not None:
            group_id = self.group_id(group)
            resource['group'] = dict(id=group_id)
        if name is not None:
            resource['name'] = name
        if email is not None:
            resource['email'] = email

        # if there is a password param, but 'update_password' is 'on_create'
        # then discard the password (since we're editing an existing user)
        if self.module.params['update_password'] == 'on_create':
            password = None
        if password is not None:
            resource['password'] = password

        # check if we need to update ( compare_user is true is no difference found )
        if self.compare_user(user, name, group_id, password, email):
            return dict(
                changed=False,
                msg="user %s is not changed." % (user['userid']))

        # try to update user
        try:
            result = self.client.post(url, action='edit', resource=resource)
        except Exception as e:
            self.module.fail_json(msg="failed to update user %s: %s" % (user['userid'], str(e)))

        return dict(
            changed=True,
            msg="successfully updated the user %s: %s" % (user['userid'], result))

    def create_user(self, userid, name, group, password, email):
        """ Creates the user in manageiq.

        Returns:
            the created user id, name, created_on timestamp,
            updated_on timestamp, userid and current_group_id.
        """
        # check for required arguments
        for key, value in dict(name=name, group=group, password=password).items():
            if value in (None, ''):
                self.module.fail_json(msg="missing required argument: %s" % (key))

        group_id = self.group_id(group)
        url = '%s/users' % (self.api_url)

        resource = {'userid': userid, 'name': name, 'password': password, 'group': {'id': group_id}}
        if email is not None:
            resource['email'] = email

        # try to create a new user
        try:
            result = self.client.post(url, action='create', resource=resource)
        except Exception as e:
            self.module.fail_json(msg="failed to create user %s: %s" % (userid, str(e)))

        return dict(
            changed=True,
            msg="successfully created the user %s: %s" % (userid, result['results']))


def main():
    argument_spec = dict(
        userid=dict(required=True, type='str'),
        name=dict(),
        password=dict(no_log=True),
        group=dict(),
        email=dict(),
        state=dict(choices=['absent', 'present'], default='present'),
        update_password=dict(choices=['always', 'on_create'],
                             default='always'),
    )
    # add the manageiq connection arguments to the arguments
    argument_spec.update(manageiq_argument_spec())

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    userid = module.params['userid']
    name = module.params['name']
    password = module.params['password']
    group = module.params['group']
    email = module.params['email']
    state = module.params['state']

    manageiq = ManageIQ(module)
    manageiq_user = ManageIQUser(manageiq)

    user = manageiq_user.user(userid)

    # user should not exist
    if state == "absent":
        # if we have a user, delete it
        if user:
            res_args = manageiq_user.delete_user(user)
        # if we do not have a user, nothing to do
        else:
            res_args = dict(
                changed=False,
                msg="user %s: does not exist in manageiq" % (userid))

    # user shoult exist
    if state == "present":
        # if we have a user, edit it
        if user:
            res_args = manageiq_user.edit_user(user, name, group, password, email)
        # if we do not have a user, create it
        else:
            res_args = manageiq_user.create_user(userid, name, group, password, email)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
