#!/usr/bin/python
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
short_description: Creates/updates/deletes Gitlab Users
description:
   - When the user does not exist in Gitlab, it will be created.
   - When the user does exists and state=absent, the user will be deleted.
   - When changes are made to user, the user will be updated.
version_added: "2.1"
author: "Werner Dijkerman (@dj-wasabi)"
requirements:
    - pyapi-gitlab python module
    - administrator rights on the Gitlab server
options:
    server_url:
        description:
            - Url of Gitlab server, with protocol (http or https).
        required: true
    validate_certs:
        description:
            - When using https if SSL certificate needs to be verified.
        type: bool
        default: 'yes'
        aliases:
            - verify_ssl
    login_user:
        description:
            - Gitlab user name.
    login_password:
        description:
            - Gitlab password for login_user
    login_token:
        description:
            - Gitlab token for logging in.
    name:
        description:
            - Name of the user you want to create
        required: true
    username:
        description:
            - The username of the user.
        required: true
    password:
        description:
            - The password of the user.
            - GitLab server enforces minimum password length to 8, set this value with 8 or more characters.
        required: true
    email:
        description:
            - The email that belongs to the user.
        required: true
    sshkey_name:
        description:
            - The name of the sshkey
    sshkey_file:
        description:
            - The ssh key itself.
    group:
        description:
            - The full path of the group.
            - Add user as an member to this group.
    access_level:
        description:
            - The access level to the group. One of the following can be used.
            - guest
            - reporter
            - developer
            - master (alias for maintainer)
            - maintainer
            - owner
    state:
        description:
            - create or delete group.
            - Possible values are present and absent.
        default: present
        choices: ["present", "absent"]
    confirm:
        description:
            - Require confirmation.
        type: bool
        default: 'yes'
        version_added: "2.4"
    isadmin:
        description:
            - Grant admin privilieges to the user
        type: bool
        default: 'false'
        version_added: "2.8"
    external:
        description:
            - Define external parameter for this user
        type: bool
        default: 'false'
        version_added: "2.8"
'''

EXAMPLES = '''
- name: Delete Gitlab User
  gitlab_user:
    server_url: http://gitlab.example.com
    validate_certs: False
    login_token: WnUzDsxjy8230-Dy_k
    username: myusername
    state: absent
  delegate_to: localhost

- name: Create Gitlab User
  gitlab_user:
    server_url: https://gitlab.dj-wasabi.local
    validate_certs: True
    login_user: dj-wasabi
    login_password: MySecretPassword
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

RETURN = '''# '''

import os

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except Exception:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


ACCESS_LEVEL = {
    'guest': gitlab.GUEST_ACCESS,
    'reporter': gitlab.REPORTER_ACCESS,
    'developer': gitlab.DEVELOPER_ACCESS,
    'master': gitlab.MAINTAINER_ACCESS,
    'maintainer': gitlab.MAINTAINER_ACCESS,
    'owner': gitlab.OWNER_ACCESS}


class GitLabUser(object):
    def __init__(self, module, gitlab_instance):
        self._module = module
        self._gitlab = gitlab_instance
        self.userObject = None

    '''
    @param * Attribut du user
    '''
    def createOrUpdateUser(self, user_name, user_username, user_password, user_email, user_sshkey_name,
                        user_sshkey_file, group_path, access_level, confirm, user_isadmin, user_external):
        changed = False

        # Because we have already call userExists in main()
        if self.userObject is None:
            user = self.createUser({
                'name': user_name,
                'username': user_username,
                'email': user_email,
                'password': user_password,
                'group': group_path,
                'skip_confirmation': not confirm,
                'admin': user_isadmin,
                'external': user_external})
            changed = True
        else:
            changed, user = self.updateUser(self.userObject, {
                'name': user_name,
                'email': user_email,
                'skip_confirmation': not confirm,
                'admin': user_isadmin,
                'external': user_external})

        # Assign ssh keys
        if user_sshkey_name and user_sshkey_file:
            changed = changed or self.addSshKeyToUser(user, {
                'name': user_sshkey_name,
                'file': user_sshkey_file})

        # Assign group
        if group_path:
            changed = changed or self.assignUserToGroup(user, group_path, access_level)

        self.userObject = user
        if changed:
            if self._module.check_mode:
                self._module.exit_json(changed=True, result="User should have updated.")

            try:
                user.save()
            except Exception as e:
                self._module.fail_json(msg="Failed to create or update a user: %s " % to_native(e))
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
    @param name Name of the groupe
    @param full_path Complete path of the Group including parent group path. <parent_path>/<group_path>
    '''
    def findGroup(self, name, full_path):
        groups = self._gitlab.groups.list(search=name)
        for group in groups:
            if (group.full_path == full_path):
                return group

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
    @param access_level Gitlab access_level to check
    '''
    def memberAsGoodAccessLevel(self, group, user_id, access_level):
        member = self.findMember(group, user_id)

        return member.access_level == access_level

    '''
    @param user User object
    @param group_path Complete path of the Group including parent group path. <parent_path>/<group_path>
    @param access_level Gitlab access_level to assign
    '''
    def assignUserToGroup(self, user, group_path, access_level):
        group_name = group_path.split('/').pop()
        group = self.findGroup(group_name, group_path)

        if self.memberExists(group, self.getUserId(user)):
            if not self.memberAsGoodAccessLevel(group, self.getUserId(user), ACCESS_LEVEL[access_level]):
                member = self.findMember(group, self.getUserId(user))
                member.access_level = ACCESS_LEVEL[access_level]
                member.save()
                return True
        else:
            if group is not None:
                try:
                    group.members.create({
                        'user_id': self.getUserId(user),
                        'access_level': ACCESS_LEVEL[access_level]})
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
        user = self._gitlab.users.create(arguments)

        return user

    '''
    @param name Username of the user
    '''
    def findUser(self, username):
        users = self._gitlab.users.list(search=username)
        for user in users:
            if (user.username == username):
                return user

    '''
    @param name Username of the user
    '''
    def existsUser(self, username):
        # When user exists, object will be stored in self.userObject.
        user = self.findUser(username)
        if user:
            self.userObject = user
            return True
        return False

    '''

    '''
    def deleteUser(self):
        user = self.userObject

        return user.delete()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True, type='str'),
            verify_ssl=dict(required=False, default=True, type='bool', aliases=['validate_certs']),
            login_user=dict(required=False, no_log=True, type='str'),
            login_password=dict(required=False, no_log=True, type='str'),
            login_token=dict(required=False, no_log=True, type='str'),
            name=dict(required=True, type='str'),
            state=dict(required=False, default="present", choices=["present", "absent"]),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            email=dict(required=True),
            sshkey_name=dict(required=False),
            sshkey_file=dict(required=False, aliases=['ssh_key']),
            group=dict(required=False),
            access_level=dict(required=False, default="guest", choices=["guest", "reporter", "developer", "master", "maintainer" "owner"]),
            confirm=dict(required=False, default=True, type='bool'),
            isadmin=dict(required=False, default=False, type='bool'),
            external=dict(required=False, default=False, type='bool')
        ),
        mutually_exclusive=[
            ['login_user', 'login_token'],
            ['login_password', 'login_token']
        ],
        required_together=[
            ['login_user', 'login_password']
        ],
        required_one_of=[
            ['login_user', 'login_token']
        ],
        supports_check_mode=True
    )

    server_url = module.params['server_url']
    verify_ssl = module.params['verify_ssl']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
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
        module.fail_json(msg="Missing required gitlab module (check docs or install with: pip install python-gitlab")

    try:
        gitlab_instance = gitlab.Gitlab(url=server_url, ssl_verify=verify_ssl, email=login_user, password=login_password,
                                        private_token=login_token, api_version=4)
        gitlab_instance.auth()
    except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabGetError) as e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s" % to_native(e))
    except (gitlab.exceptions.GitlabHttpError) as e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s. \
            Gitlab remove Session API now that private tokens are removed from user API endpoints since version 10.2." % to_native(e))

    gitlab_user = GitLabUser(module, gitlab_instance)
    user_exists = gitlab_user.existsUser(user_username)

    if state == 'absent':
        if user_exists:
            gitlab_user.deleteUser()
            module.exit_json(changed=True, result="Successfully deleted user %s" % user_username)
        else:
            module.exit_json(changed=False, result="User deleted or does not exists")

    if state == 'present':
        if gitlab_user.createOrUpdateUser(
            user_name,
            user_username,
            user_password,
            user_email,
            user_sshkey_name,
            user_sshkey_file,
            group_path,
            access_level,
            confirm,
            user_isadmin,
            user_external):
            module.exit_json(changed=True, result="Successfully created or updated the user %s" % user_username, user=gitlab_user.userObject._attrs)
        else:
            module.exit_json(changed=False, result="No need to update the user %s" % user_username, user=gitlab_user.userObject._attrs)


if __name__ == '__main__':
    main()
