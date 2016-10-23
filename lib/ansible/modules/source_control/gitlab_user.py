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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

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
    - python-gitlab python module
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
            - Is deprecated and replaced with sshkeys.
        required: false
        default: null
    sshkey_file:
        description:
            - The ssh key itself.
            - Is deprecated and replaced with sshkeys.
        required: false
        default: null
    sshkeys:
        description:
            - A list with all sshkeys for the user.
            - The list should contain the keys name, sshkey and state.
            - When state is not provided, default setting is that the key will be created (present).
        required: false
        default: null
        version_added: "2.3"
    projects_limit:
        description:
            - The amount of project you can create.
        required: false
        default: 10
        version_added: "2.3"
    twitter:
        description:
            - The twitter name.
        required: false
        default: null
        version_added: "2.3"
    linkedin:
        description:
            - The linkedin name.
        required: false
        default: null
        version_added: "2.3"
    skype:
        description:
            - The skype name.
        required: false
        default: null
        version_added: "2.3"
    location:
        description:
            - The location of the user.
        required: false
        default: null
        version_added: "2.3"
    can_create_group:
        description:
            - If the user can create groups.
        required: false
        default: "false"
        version_added: "2.3"
        choices: ["true", "false"]
    external:
        description:
            - If the user is an external user.
            - External users can only access projects to which they are explicitly granted access, thus hiding all other internal or private ones from them
        required: false
        default: "false"
        version_added: "2.3"
        choices: ["true", "false"]
    group:
        description:
            - Add user as an member to this group.
            - Is deprecated and replaced with groupss
        required: false
        default: null
    groups:
        description:
            - A list structure with all groups where this user belongs to.
            - This list should contain the keys name, access_level and state.
            - The groups should already be available, otherwise the module complains user can not be created because group not exist.
            - See at access_level which access_levels are available.
            - When state is not provided, default setting is that the user will be added to the group (present).
        required: false
        default: null
        version_added: "2.3"
    access_level:
        description:
            - The access level to the group.
            - Is deprecated and replaced with groups.
        required: false
        default: "guest"
        choices: ["guest", "reporter", "developer", "master", "owner"]
    state:
        description:
            - create or delete user.
            - Or when a user is created, you can set the user with state blocked or unblocked
        required: false
        default: present
        choices: ["present", "absent", "blocked", "unblocked"]
'''

EXAMPLES = '''
- name: "Delete Gitlab User"
  local_action:
    module: gitlab_user
    server_url: "http://gitlab.dj-wasabi.local"
    validate_certs: false
    login_token: "WnUzDsxjy8230-Dy_k"
    username: myusername
    state: absent

- name: "Create Gitlab User"
  local_action:
    module: gitlab_user
    server_url: "https://gitlab.dj-wasabi.local"
    validate_certs: true
    login_user: dj-wasabi
    login_password: "MySecretPassword"
    name: My Name
    username: myusername
    password: mysecretpassword
    sshkeys:
      - name: MyKey
        sshkey: rsa sasa
        state: present
    email: me@home.com
    state: present

- name: "Create Gitlab User with groups"
  local_action:
    module: gitlab_user
    server_url: "https://gitlab.dj-wasabi.local"
    validate_certs: true
    login_user: dj-wasabi
    login_password: "MySecretPassword"
    name: My Name
    username: myusername
    password: mysecretpassword
    email: me@home.com
    groups:
      - name: my_first_group
        access_level: guest
        state: present
      - name: my_second_group
        access_level: developer
      - name: my_third_group
        access_level: guest
        state: absent
    state: present
'''

RETURN = '''# '''

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except:
    HAS_GITLAB_PACKAGE = False

# from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.basic import *


class GitLabUser(object):
    def __init__(self, module, git):
        self._module = module
        self._gitlab = git
        self.userObject = None
        self.groupObject = None
        self.sshkeyObject = None

    def createOrUpdateUser(self, name, username, password, email, projects_limit, twitter, linkedin, skype, external,
                           can_create_group, state, groups=None, sshkeys=None):
        """Create a user in gitlab"""
        changed = False
        if self.userObject is None:
            self.createUser(name=name, username=username, password=password, email=email)
            changed = True

        if state is not None:
            if self.stateUser(state=state):
                changed = True
        if self.updateUser(username=username, email=email, name=name, projects_limit=projects_limit, twitter=twitter,
                           linkedin=linkedin, skype=skype, external=external, can_create_group=can_create_group):
            changed = True
        if self.createOrUpdateMember(groups=groups):
            changed = True
        if self.createOrDeleteSSHKeys(sshkeys=sshkeys):
            changed = True

        if changed:
            return True
        else:
            return False

    def createOrDeleteSSHKeys(self, sshkeys):
        """Create or delete sshkeys"""
        changed = False

        for ssh in sshkeys:
            if 'name' not in ssh:
                self._module.fail_json(msg="There is no 'name' key specified.")
            if 'sshkey' not in ssh:
                self._module.fail_json(msg="There is no 'sshkey' key specified.")
            if 'state' not in ssh:
                state = "present"
            else:
                state = ssh['state']

            key_exists = self.existsSSHKey(name=ssh['name'])
            if key_exists and state == "present":
                changed = False
            elif not key_exists and state == "present":
                if self.createSSHKey(name=ssh['name'], sshkey=ssh['sshkey']):
                    changed = True
            elif not key_exists and state == "absent":
                changed = False
            else:
                if self.deleteSSHKey():
                    changed = True
        return changed

    def existsSSHKey(self, name):
        """Check if userssh keys exists"""
        user = self.userObject
        keys = user.keys.list()

        if len(keys) >= 1:
            for key in keys:
                if key.title == name:
                    self.sshkeyObject = key
                    return True
        self.sshkeyObject = None
        return False

    def createSSHKey(self, name, sshkey):
        """Create ssh key"""
        user = self.userObject
        if user.keys.create({'title': name, 'key': sshkey}):
            return True
        else:
            return False

    def deleteSSHKey(self):
        """Delete ssh key"""
        key = self.sshkeyObject
        if key.delete():
            return True
        else:
            return False

    def getAccessLevel(self, access_level):
        """Returns the correct access_level number"""
        access = {'guest': 10, 'reporter': 20, 'developer': 30, 'master': 40, 'owner': 50}
        if access_level in ['guest', 'reporter', 'developer', 'master', 'owner']:
            return access[access_level]
        else:
            self._module.exit_json(changed=False, result="The given access_level %s is not correct." % access_level)

    def createOrUpdateMember(self, groups):
        changed = False
        user_id = self.userObject.id
        user_name = self.userObject.username

        for group in groups:
            self.groupObject = None

            if 'name' not in group:
                self._module.fail_json(msg="There is no 'name' specified for group.")
            if 'access_level' not in group:
                self._module.fail_json(msg="There is no 'access_level' specified for group.")
            if 'state' not in group:
                state = "present"
            else:
                state = group['state']

            if self.existsGroup(name=group['name']):
                member = self.memberInGroup(group=group['name'], username=user_name)
                access = self.getAccessLevel(access_level=group['access_level'])
                if member:
                    if state == "present":
                        if member.access_level != access:
                            member.access_level = access
                            member.save()
                            changed = True
                    elif state == "absent":
                        member.delete()
                        changed = True
                else:
                    if state == "present":
                        self._gitlab.group_members.create({'user_id': user_id, 'group_id': self.groupObject.id, 'access_level': access})
                        changed = True
        return changed

    def memberInGroup(self, group, username):
        """Check if the user is in a group"""
        # groups = self._gitlab.groups.search(group)
        group = self.groupObject

        members = group.members.list()
        for member in members:
            if member.username == username:
                self.groupObject = group
                return member
        return False

    def createUser(self, name, username, password, email):
        """Create user in gitlab"""
        user = self._gitlab.users.create({'email': email,
                                          'password': password,
                                          'username': username,
                                          'name': name})
        self.userObject = user

    def updateUser(self, username, email, name, projects_limit, twitter, linkedin, skype, external,
                   can_create_group):
        """Update the user"""
        changed = False
        user = self.userObject

        if user.email != email:
            user.email = email
            changed = True
        if user.username != username:
            user.username = username
            changed = True
        if user.name != name:
            user.name = name
            changed = True
        if user.projects_limit != projects_limit:
            user.projects_limit = projects_limit
        if twitter is not None:
            if user.twitter != twitter:
                user.twitter = twitter
                changed = True
        if linkedin is not None:
            if user.linkedin != linkedin:
                user.linkedin = linkedin
                changed = True
        if skype is not None:
            if user.skype != skype:
                user.skype = skype
                changed = True
        if user.external != external:
            user.external = external
            changed = True
        if user.can_create_group != can_create_group:
            user.can_create_group = can_create_group
            changed = True

        if changed:
            user.save()
            self.userObject = user
            return True
        else:
            return False

    def stateUser(self, state):
        """Block or unblock a user."""
        user = self.userObject
        if state == "blocked":
            user.block()
            return True
        if state == "unblocked":
            user.unblock()
            return True
        return False

    def userExists(self, username):
        """Find user and if exists, return object"""
        users = self._gitlab.users.list(username=username)
        if len(users) == 1:
            self.userObject = users[0]
            return True
        else:
            return False

    def existsGroup(self, name):
        """When group/user exists, object will be stored in self.groupObject."""
        groups = self._gitlab.groups.search(name)
        if len(groups) == 1:
            self.groupObject = groups[0]
            return True
        else:
            return False

    def deleteUser(self):
        """Delete the user"""
        user = self.userObject
        if user.delete():
            return True
        else:
            return False


def main():
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
            groups=dict(required=False, type='list', default=[]),
            sshkeys=dict(required=False, type='list', default=[]),
            projects_limit=dict(required=False, default=10, type='int'),
            twitter=dict(required=False, default=None, type='str'),
            linkedin=dict(required=False, default=None, type='str'),
            skype=dict(required=False, default=None, type='str'),
            external=dict(required=False, default=False, type='bool'),
            can_create_group=dict(default=False, type='bool'),
            state=dict(default="present", choices=["present", "absent", "blocked", "unblocked"]),
            sshkey_name=dict(required=False),
            sshkey_file=dict(required=False),
            group=dict(required=False, type='str'),
            access_level=dict(required=False, default="guest",
                              choices=["guest", "reporter", "developer", "master", "owner"])
        ),
        supports_check_mode=True
    )
    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg="Missing required gitlab module (check docs or install with: pip install python-gitlab")

    server_url = module.params['server_url']
    verify_ssl = module.params['validate_certs']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
    user_name = module.params['name']
    user_username = module.params['username']
    user_password = module.params['password']
    user_email = module.params['email']
    groups = module.params['groups']
    projects_limit = module.params['projects_limit']
    twitter = module.params['twitter']
    linkedin = module.params['linkedin']
    skype = module.params['skype']
    external = module.params['external']
    can_create_group = module.params['can_create_group']
    sshkeys = module.params['sshkeys']
    state = module.params['state']
    use_credentials = None

    # Not used anymore, is replaced by groups and sshkeys
    user_sshkey_name = module.params['sshkey_name']
    user_sshkey_file = module.params['sshkey_file']
    group_name = module.params['group']
    access_level = module.params['access_level']

    # Validate some credentials configuration parameters.
    if login_user is not None and login_password is not None:
        use_credentials = True
    elif login_token is not None:
        use_credentials = False
    else:
        module.fail_json(msg="No login credentials are given. Use login_user with login_password, or login_token")

    if login_token and login_user:
        module.fail_json(msg="You can either use 'login_token' or 'login_user' and 'login_password'")

    try:
        if use_credentials:
            git = gitlab.Gitlab(server_url, email=login_user, password=login_password, ssl_verify=verify_ssl)
            git.auth()
        else:
            git = gitlab.Gitlab(server_url, private_token=login_token, ssl_verify=verify_ssl)
            git.auth()
    except Exception:
        e = get_exception()
        module.fail_json(msg="Failed to connect to Gitlab server: %s " % e)

    user_username = user_username.lower()
    user = GitLabUser(module, git)
    user_exists = user.userExists(username=user_username)

    if user_exists:
        if state == "absent":
            if module.check_mode:
                module.exit_json(changed=True, result="User should have been deleted.")
            if user.deleteUser():
                module.exit_json(changed=True, result="User is deleted.")
            else:
                module.exit_json(changed=False, result="Something went wrong with deleting the user.")
        else:
            if user.createOrUpdateUser(name=user_name, username=user_username, password=user_password, email=user_email,
                                       state=state, groups=groups, sshkeys=sshkeys, projects_limit=projects_limit,
                                       twitter=twitter, linkedin=linkedin, skype=skype, external=external,
                                       can_create_group=can_create_group):
                module.exit_json(changed=True, result="We updated the user.")
            else:
                module.exit_json(changed=False, result="There was no need for updating the user")
    else:
        if state == "absent":
            module.exit_json(changed=False, result="User already deleted or does not exists")
        else:
            if module.check_mode:
                module.exit_json(changed=True, result="User should have been created.")
            if user.createOrUpdateUser(name=user_name, username=user_username, password=user_password, email=user_email,
                                       state=None, groups=groups, sshkeys=sshkeys, projects_limit=projects_limit,
                                       twitter=twitter, linkedin=linkedin, skype=skype, external=external,
                                       can_create_group=can_create_group):
                module.exit_json(changed=True, result="User is created.")
            else:
                module.exit_json(changed=False, result="Something went wrong in deleting.")


if __name__ == '__main__':
    main()
