#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# Copyright: (c) 2015, Werner Dijkerman (ikben@werner-dijkerman.nl)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gitlab_user
short_description: Creates/updates/deletes GitLab Users
description:
  - When the user does not exist in GitLab, it will be created.
  - When the user does exists and state=absent, the user will be deleted.
  - When changes are made to user, the user will be updated.
version_added: "2.1"
author:
  - Werner Dijkerman (@dj-wasabi)
  - Guillaume Martinez (@Lunik)
requirements:
  - python >= 2.7
  - python-gitlab python module <= 1.12.1
  - administrator rights on the GitLab server
extends_documentation_fragment:
    - auth_basic
options:
  server_url:
    description:
      - The URL of the GitLab server, with protocol (i.e. http or https).
    type: str
  login_user:
    description:
      - GitLab user name.
    type: str
  login_password:
    description:
      - GitLab password for login_user
    type: str
  api_token:
    description:
      - GitLab token for logging in.
    type: str
    aliases:
      - login_token
  name:
    description:
      - Name of the user you want to create
    required: true
    type: str
  username:
    description:
      - The username of the user.
    required: true
    type: str
  password:
    description:
      - The password of the user.
      - GitLab server enforces minimum password length to 8, set this value with 8 or more characters.
    required: true
    type: str
  email:
    description:
      - The email that belongs to the user.
    required: true
    type: str
  sshkey_name:
    description:
      - The name of the sshkey
    type: str
  sshkey_file:
    description:
      - The ssh key itself.
    type: str
  group:
    description:
      - Id or Full path of parent group in the form of group/name
      - Add user as an member to this group.
    type: str
  access_level:
    description:
      - The access level to the group. One of the following can be used.
      - guest
      - reporter
      - developer
      - master (alias for maintainer)
      - maintainer
      - owner
    default: guest
    type: str
    choices: ["guest", "reporter", "developer", "master", "maintainer", "owner"]
  state:
    description:
      - create or delete group.
      - Possible values are present and absent.
    default: present
    type: str
    choices: ["present", "absent"]
  confirm:
    description:
      - Require confirmation.
    type: bool
    default: yes
    version_added: "2.4"
  isadmin:
    description:
      - Grant admin privileges to the user
    type: bool
    default: no
    version_added: "2.8"
  external:
    description:
      - Define external parameter for this user
    type: bool
    default: no
    version_added: "2.8"
'''

EXAMPLES = '''
- name: "Delete GitLab User"
  gitlab_user:
    api_url: https://gitlab.example.com/
    api_token: "{{ access_token }}"
    validate_certs: False
    username: myusername
    state: absent
  delegate_to: localhost

- name: "Create GitLab User"
  gitlab_user:
    api_url: https://gitlab.example.com/
    validate_certs: True
    api_username: dj-wasabi
    api_password: "MySecretPassword"
    name: My Name
    username: myusername
    password: mysecretpassword
    email: me@example.com
    sshkey_name: MySSH
    sshkey_file: ssh-rsa AAAAB3NzaC1yc...
    state: present
    group: super_group/mon_group
    access_level: owner
  delegate_to: localhost
'''

RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: str
  sample: "Success"

result:
  description: json parsed response from the server
  returned: always
  type: dict

error:
  description: the error message returned by the GitLab API
  returned: failed
  type: str
  sample: "400: path is already in use"

user:
  description: API object
  returned: always
  type: dict
'''

import os
import re
import traceback

GITLAB_IMP_ERR = None
try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except Exception:
    GITLAB_IMP_ERR = traceback.format_exc()
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native

from ansible.module_utils.gitlab import findGroup


class GitLabUser(object):
    def __init__(self, module, gitlab_instance):
        self._module = module
        self._gitlab = gitlab_instance
        self.userObject = None
        self.ACCESS_LEVEL = {
            'guest': gitlab.GUEST_ACCESS,
            'reporter': gitlab.REPORTER_ACCESS,
            'developer': gitlab.DEVELOPER_ACCESS,
            'master': gitlab.MAINTAINER_ACCESS,
            'maintainer': gitlab.MAINTAINER_ACCESS,
            'owner': gitlab.OWNER_ACCESS}

    '''
    @param username Username of the user
    @param options User options
    '''
    def createOrUpdateUser(self, username, options):
        changed = False

        # Because we have already call userExists in main()
        if self.userObject is None:
            user = self.createUser({
                'name': options['name'],
                'username': username,
                'password': options['password'],
                'email': options['email'],
                'skip_confirmation': not options['confirm'],
                'admin': options['isadmin'],
                'external': options['external']})
            changed = True
        else:
            changed, user = self.updateUser(self.userObject, {
                'name': options['name'],
                'email': options['email'],
                'is_admin': options['isadmin'],
                'external': options['external']})

        # Assign ssh keys
        if options['sshkey_name'] and options['sshkey_file']:
            key_changed = self.addSshKeyToUser(user, {
                'name': options['sshkey_name'],
                'file': options['sshkey_file']})
            changed = changed or key_changed

        # Assign group
        if options['group_path']:
            group_changed = self.assignUserToGroup(user, options['group_path'], options['access_level'])
            changed = changed or group_changed

        self.userObject = user
        if changed:
            if self._module.check_mode:
                self._module.exit_json(changed=True, msg="Successfully created or updated the user %s" % username)

            try:
                user.save()
            except Exception as e:
                self._module.fail_json(msg="Failed to update user: %s " % to_native(e))
            return True
        else:
            return False

    '''
    @param group User object
    '''
    def getUserId(self, user):
        if user is not None:
            return user.id
        return None

    '''
    @param user User object
    @param sshkey_name Name of the ssh key
    '''
    def sshKeyExists(self, user, sshkey_name):
        keyList = map(lambda k: k.title, user.keys.list())

        return sshkey_name in keyList

    '''
    @param user User object
    @param sshkey Dict containing sshkey infos {"name": "", "file": ""}
    '''
    def addSshKeyToUser(self, user, sshkey):
        if not self.sshKeyExists(user, sshkey['name']):
            if self._module.check_mode:
                return True

            try:
                user.keys.create({
                    'title': sshkey['name'],
                    'key': sshkey['file']})
            except gitlab.exceptions.GitlabCreateError as e:
                self._module.fail_json(msg="Failed to assign sshkey to user: %s" % to_native(e))
            return True
        return False

    '''
    @param group Group object
    @param user_id Id of the user to find
    '''
    def findMember(self, group, user_id):
        try:
            member = group.members.get(user_id)
        except gitlab.exceptions.GitlabGetError as e:
            return None
        return member

    '''
    @param group Group object
    @param user_id Id of the user to check
    '''
    def memberExists(self, group, user_id):
        member = self.findMember(group, user_id)

        return member is not None

    '''
    @param group Group object
    @param user_id Id of the user to check
    @param access_level GitLab access_level to check
    '''
    def memberAsGoodAccessLevel(self, group, user_id, access_level):
        member = self.findMember(group, user_id)

        return member.access_level == access_level

    '''
    @param user User object
    @param group_path Complete path of the Group including parent group path. <parent_path>/<group_path>
    @param access_level GitLab access_level to assign
    '''
    def assignUserToGroup(self, user, group_identifier, access_level):
        group = findGroup(self._gitlab, group_identifier)

        if self._module.check_mode:
            return True

        if group is None:
            return False

        if self.memberExists(group, self.getUserId(user)):
            member = self.findMember(group, self.getUserId(user))
            if not self.memberAsGoodAccessLevel(group, member.id, self.ACCESS_LEVEL[access_level]):
                member.access_level = self.ACCESS_LEVEL[access_level]
                member.save()
                return True
        else:
            try:
                group.members.create({
                    'user_id': self.getUserId(user),
                    'access_level': self.ACCESS_LEVEL[access_level]})
            except gitlab.exceptions.GitlabCreateError as e:
                self._module.fail_json(msg="Failed to assign user to group: %s" % to_native(e))
            return True
        return False

    '''
    @param user User object
    @param arguments User attributes
    '''
    def updateUser(self, user, arguments):
        changed = False

        for arg_key, arg_value in arguments.items():
            if arguments[arg_key] is not None:
                if getattr(user, arg_key) != arguments[arg_key]:
                    setattr(user, arg_key, arguments[arg_key])
                    changed = True

        return (changed, user)

    '''
    @param arguments User attributes
    '''
    def createUser(self, arguments):
        if self._module.check_mode:
            return True

        try:
            user = self._gitlab.users.create(arguments)
        except (gitlab.exceptions.GitlabCreateError) as e:
            self._module.fail_json(msg="Failed to create user: %s " % to_native(e))

        return user

    '''
    @param username Username of the user
    '''
    def findUser(self, username):
        users = self._gitlab.users.list(search=username)
        for user in users:
            if (user.username == username):
                return user

    '''
    @param username Username of the user
    '''
    def existsUser(self, username):
        # When user exists, object will be stored in self.userObject.
        user = self.findUser(username)
        if user:
            self.userObject = user
            return True
        return False

    def deleteUser(self):
        if self._module.check_mode:
            return True

        user = self.userObject

        return user.delete()


def deprecation_warning(module):
    deprecated_aliases = ['login_token']

    for aliase in deprecated_aliases:
        if aliase in module.params:
            module.deprecate("Alias \'{aliase}\' is deprecated".format(aliase=aliase), "2.10")


def main():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        server_url=dict(type='str', removed_in_version="2.10"),
        login_user=dict(type='str', no_log=True, removed_in_version="2.10"),
        login_password=dict(type='str', no_log=True, removed_in_version="2.10"),
        api_token=dict(type='str', no_log=True, aliases=["login_token"]),
        name=dict(type='str', required=True),
        state=dict(type='str', default="present", choices=["absent", "present"]),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        email=dict(type='str', required=True),
        sshkey_name=dict(type='str'),
        sshkey_file=dict(type='str'),
        group=dict(type='str'),
        access_level=dict(type='str', default="guest", choices=["developer", "guest", "maintainer", "master", "owner", "reporter"]),
        confirm=dict(type='bool', default=True),
        isadmin=dict(type='bool', default=False),
        external=dict(type='bool', default=False),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['api_url', 'server_url'],
            ['api_username', 'login_user'],
            ['api_password', 'login_password'],
            ['api_username', 'api_token'],
            ['api_password', 'api_token'],
            ['login_user', 'login_token'],
            ['login_password', 'login_token']
        ],
        required_together=[
            ['api_username', 'api_password'],
            ['login_user', 'login_password'],
        ],
        required_one_of=[
            ['api_username', 'api_token', 'login_user', 'login_token'],
            ['server_url', 'api_url']
        ],
        supports_check_mode=True,
    )

    deprecation_warning(module)

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']

    api_url = module.params['api_url']
    validate_certs = module.params['validate_certs']
    api_user = module.params['api_username']
    api_password = module.params['api_password']

    gitlab_url = server_url if api_url is None else api_url
    gitlab_user = login_user if api_user is None else api_user
    gitlab_password = login_password if api_password is None else api_password
    gitlab_token = module.params['api_token']

    user_name = module.params['name']
    state = module.params['state']
    user_username = module.params['username'].lower()
    user_password = module.params['password']
    user_email = module.params['email']
    user_sshkey_name = module.params['sshkey_name']
    user_sshkey_file = module.params['sshkey_file']
    group_path = module.params['group']
    access_level = module.params['access_level']
    confirm = module.params['confirm']
    user_isadmin = module.params['isadmin']
    user_external = module.params['external']

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg=missing_required_lib("python-gitlab"), exception=GITLAB_IMP_ERR)

    try:
        gitlab_instance = gitlab.Gitlab(url=gitlab_url, ssl_verify=validate_certs, email=gitlab_user, password=gitlab_password,
                                        private_token=gitlab_token, api_version=4)
        gitlab_instance.auth()
    except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabGetError) as e:
        module.fail_json(msg="Failed to connect to GitLab server: %s" % to_native(e))
    except (gitlab.exceptions.GitlabHttpError) as e:
        module.fail_json(msg="Failed to connect to GitLab server: %s. \
            GitLab remove Session API now that private tokens are removed from user API endpoints since version 10.2." % to_native(e))

    gitlab_user = GitLabUser(module, gitlab_instance)
    user_exists = gitlab_user.existsUser(user_username)

    if state == 'absent':
        if user_exists:
            gitlab_user.deleteUser()
            module.exit_json(changed=True, msg="Successfully deleted user %s" % user_username)
        else:
            module.exit_json(changed=False, msg="User deleted or does not exists")

    if state == 'present':
        if gitlab_user.createOrUpdateUser(user_username, {
                                          "name": user_name,
                                          "password": user_password,
                                          "email": user_email,
                                          "sshkey_name": user_sshkey_name,
                                          "sshkey_file": user_sshkey_file,
                                          "group_path": group_path,
                                          "access_level": access_level,
                                          "confirm": confirm,
                                          "isadmin": user_isadmin,
                                          "external": user_external}):
            module.exit_json(changed=True, msg="Successfully created or updated the user %s" % user_username, user=gitlab_user.userObject._attrs)
        else:
            module.exit_json(changed=False, msg="No need to update the user %s" % user_username, user=gitlab_user.userObject._attrs)


if __name__ == '__main__':
    main()
