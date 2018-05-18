#!/usr/bin/python
# (c) 2015, Werner Dijkerman (ikben@werner-dijkerman.nl)
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
            - Add user as an member to this group.
    access_level:
        description:
            - The access level to the group. One of the following can be used.
            - guest
            - reporter
            - developer
            - master
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
  delegate_to: localhost
'''

RETURN = '''# '''

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


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

    def createOrUpdateUser(self, user_name, user_username, user_password, user_email, user_sshkey_name, user_sshkey_file, group_name, access_level, confirm):
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
            self.createUser(group_id, user_password, user_sshkey_name, user_sshkey_file, access_level, confirm, arguments)

    def createUser(self, group_id, user_password, user_sshkey_name, user_sshkey_file, access_level, confirm, arguments):
        user_changed = False

        # Create the user
        user_username = arguments['username']
        if self._gitlab.createuser(password=user_password, confirm=confirm, **arguments):
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
            confirm=dict(required=False, default=True, type='bool')
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
    confirm = module.params['confirm']

    if len(user_password) < 8:
        module.fail_json(msg="New user's 'password' should contain more than 8 characters.")

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
            git = gitlab.Gitlab(host=server_url, verify_ssl=verify_ssl)
            git.login(user=login_user, password=login_password)
        else:
            git = gitlab.Gitlab(server_url, token=login_token, verify_ssl=verify_ssl)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s " % to_native(e))

    # Check if user is authorized or not before proceeding to any operations
    # if not, exit from here
    auth_msg = git.currentuser().get('message', None)
    if auth_msg is not None and auth_msg == '401 Unauthorized':
        module.fail_json(msg='User unauthorized',
                         details="User is not allowed to access Gitlab server "
                                 "using login_token. Please check login_token")

    # Validate if group exists and take action based on "state"
    user = GitLabUser(module, git)

    # Check if user exists, if not exists and state = absent, we exit nicely.
    if not user.existsUser(user_username) and state == "absent":
        module.exit_json(changed=False, result="User already deleted or does not exist")
    else:
        # User exists,
        if state == "absent":
            user.deleteUser(user_username)
        else:
            user.createOrUpdateUser(user_name, user_username, user_password, user_email, user_sshkey_name, user_sshkey_file, group_name, access_level, confirm)


if __name__ == '__main__':
    main()
