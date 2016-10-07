#!/usr/bin/python
# (c) 2015, Werner Dijkerman (ikben@werner-dijkerman.nl)
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

DOCUMENTATION = '''
---
module: gitlab_user
short_description: Creates/updates/deletes Gitlab Users
description:
   - When the user does not exists in Gitlab, it will be created.
   - When the user does exists and state=absent, the user will be deleted.
   - When changes are made to user, the user will be updated.
version_added: "2.1"
author: "Werner Dijkerman (@dj-wasabi)"
requirements:
    - pyapi-gitlab python module
options:
    server_url:
        description:
            - Url of Gitlab server, with protocol (http or https).
        required: true
    validate_certs:
        description:
            - When using https if SSL certificate needs to be verified.
        required: false
        default: true
        aliases:
            - verify_ssl
    login_user:
        description:
            - Gitlab user name.
        required: false
        default: null
    login_password:
        description:
            - Gitlab password for login_user
        required: false
        default: null
    login_token:
        description:
            - Gitlab token for logging in.
        required: false
        default: null
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
        required: true
    email:
        description:
            - The email that belongs to the user.
        required: true
    sshkey_name:
        description:
            - The name of the sshkey
        required: false
        default: null
    sshkey_file:
        description:
            - The ssh key itself.
        required: false
        default: null
    group:
        description:
            - Add user as an member to this group.
        required: false
        default: null
    access_level:
        description:
            - The access level to the group. One of the following can be used.
            - guest
            - reporter
            - developer
            - master
            - owner
        required: false
        default: null
    state:
        description:
            - create or delete group.
            - Possible values are present and absent.
        required: false
        default: present
        choices: ["present", "absent"]
'''

EXAMPLES = '''
- name: "Delete Gitlab User"
  local_action: gitlab_user
                server_url="http://gitlab.dj-wasabi.local"
                validate_certs=false
                login_token="WnUzDsxjy8230-Dy_k"
                username=myusername
                state=absent

- name: "Create Gitlab User"
  local_action: gitlab_user
                server_url="https://gitlab.dj-wasabi.local"
                validate_certs=true
                login_user=dj-wasabi
                login_password="MySecretPassword"
                name=My Name
                username=myusername
                password=mysecretpassword
                email=me@home.com
                sshkey_name=MySSH
                sshkey_file=ssh-rsa AAAAB3NzaC1yc...
                state=present
'''

RETURN = '''# '''

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.basic import *


class GitLabUser(object):
    def __init__(self, module, git):
        self._module = module
        self._gitlab = git

    def addToGroup(self, group_id, user_id, access_level):
        if access_level == "guest":
            level = 10
        elif access_level == "reporter":
            level = 20
        elif access_level == "developer":
            level = 30
        elif access_level == "master":
            level = 40
        elif access_level == "owner":
            level = 50
        return self._gitlab.addgroupmember(group_id, user_id, level)

    def createOrUpdateUser(self, user_name, user_username, user_password, user_email, user_sshkey_name, user_sshkey_file, group_name, access_level):
        group_id = ''
        arguments = {"name": user_name,
                     "username": user_username,
                     "email": user_email}

        if group_name is not None:
            if self.existsGroup(group_name):
                group_id = self.getGroupId(group_name)

        if self.existsUser(user_username):
            self.updateUser(group_id, user_sshkey_name, user_sshkey_file, access_level, arguments)
        else:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self.createUser(group_id, user_password, user_sshkey_name, user_sshkey_file, access_level, arguments)

    def createUser(self, group_id, user_password, user_sshkey_name, user_sshkey_file, access_level, arguments):
        user_changed = False

        # Create the user
        user_username = arguments['username']
        user_name = arguments['name']
        user_email = arguments['email']
        if self._gitlab.createuser(password=user_password, **arguments):
            user_id = self.getUserId(user_username)
            if self._gitlab.addsshkeyuser(user_id=user_id, title=user_sshkey_name, key=user_sshkey_file):
                user_changed = True
            # Add the user to the group if group_id is not empty
            if group_id != '':
                if self.addToGroup(group_id, user_id, access_level):
                    user_changed = True
            user_changed = True

        # Exit with change to true or false
        if user_changed:
            self._module.exit_json(changed=True, result="Created the user")
        else:
            self._module.exit_json(changed=False)

    def deleteUser(self, user_username):
        user_id = self.getUserId(user_username)

        if self._gitlab.deleteuser(user_id):
            self._module.exit_json(changed=True, result="Successfully deleted user %s" % user_username)
        else:
            self._module.exit_json(changed=False, result="User %s already deleted or something went wrong" % user_username)

    def existsGroup(self, group_name):
        for group in self._gitlab.getall(self._gitlab.getgroups):
            if group['name'] == group_name:
                return True
        return False

    def existsUser(self, username):
        found_user = self._gitlab.getusers(search=username)
        for user in found_user:
            if user['id'] != '':
                return True
        return False

    def getGroupId(self, group_name):
        for group in self._gitlab.getall(self._gitlab.getgroups):
            if group['name'] == group_name:
                return group['id']

    def getUserId(self, username):
        found_user = self._gitlab.getusers(search=username)
        for user in found_user:
            if user['id'] != '':
                return user['id']

    def updateUser(self, group_id, user_sshkey_name, user_sshkey_file, access_level, arguments):
        user_changed = False
        user_username = arguments['username']
        user_id = self.getUserId(user_username)
        user_data = self._gitlab.getuser(user_id=user_id)

        # Lets check if we need to update the user
        for arg_key, arg_value in arguments.items():
            if user_data[arg_key] != arg_value:
                user_changed = True

        if user_changed:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._gitlab.edituser(user_id=user_id, **arguments)
            user_changed = True
        if self._module.check_mode or self._gitlab.addsshkeyuser(user_id=user_id, title=user_sshkey_name, key=user_sshkey_file):
            user_changed = True
        if group_id != '':
            if self._module.check_mode or self.addToGroup(group_id, user_id, access_level):
                user_changed = True
        if user_changed:
            self._module.exit_json(changed=True, result="The user %s is updated" % user_username)
        else:
            self._module.exit_json(changed=False, result="The user %s is already up2date" % user_username)


def main():
    global user_id
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            validate_certs=dict(required=False, default=True, type='bool', aliases=['verify_ssl']),
            login_user=dict(required=False, no_log=True),
            login_password=dict(required=False, no_log=True),
            login_token=dict(required=False, no_log=True),
            name=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            email=dict(required=True),
            sshkey_name=dict(required=False),
            sshkey_file=dict(required=False),
            group=dict(required=False),
            access_level=dict(required=False, choices=["guest", "reporter", "developer", "master", "owner"]),
            state=dict(default="present", choices=["present", "absent"]),
        ),
        supports_check_mode=True
    )

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg="Missing required gitlab module (check docs or install with: pip install pyapi-gitlab")

    server_url = module.params['server_url']
    verify_ssl = module.params['validate_certs']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
    user_name = module.params['name']
    user_username = module.params['username']
    user_password = module.params['password']
    user_email = module.params['email']
    user_sshkey_name = module.params['sshkey_name']
    user_sshkey_file = module.params['sshkey_file']
    group_name = module.params['group']
    access_level = module.params['access_level']
    state = module.params['state']

    # We need both login_user and login_password or login_token, otherwise we fail.
    if login_user is not None and login_password is not None:
        use_credentials = True
    elif login_token is not None:
        use_credentials = False
    else:
        module.fail_json(msg="No login credentials are given. Use login_user with login_password, or login_token")

    # Check if vars are none
    if user_sshkey_file is not None and user_sshkey_name is not None:
        use_sshkey = True
    else:
        use_sshkey = False

    if group_name is not None and access_level is not None:
        add_to_group = True
        group_name = group_name.lower()
    else:
        add_to_group = False

    user_username = user_username.lower()

    # Lets make an connection to the Gitlab server_url, with either login_user and login_password
    # or with login_token
    try:
        if use_credentials:
            git = gitlab.Gitlab(host=server_url)
            git.login(user=login_user, password=login_password)
        else:
            git = gitlab.Gitlab(server_url, token=login_token, verify_ssl=verify_ssl)
    except Exception:
        e = get_exception()
        module.fail_json(msg="Failed to connect to Gitlab server: %s " % e)

    # Validate if group exists and take action based on "state"
    user = GitLabUser(module, git)

    # Check if user exists, if not exists and state = absent, we exit nicely.
    if not user.existsUser(user_username) and state == "absent":
        module.exit_json(changed=False, result="User already deleted or does not exists")
    else:
        # User exists,
        if state == "absent":
            user.deleteUser(user_username)
        else:
            user.createOrUpdateUser(user_name, user_username, user_password, user_email, user_sshkey_name, user_sshkey_file, group_name, access_level)



if __name__ == '__main__':
    main()
