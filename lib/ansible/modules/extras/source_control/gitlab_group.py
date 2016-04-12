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
module: gitlab_group
short_description: Creates/updates/deletes Gitlab Groups
description:
   - When the group does not exists in Gitlab, it will be created.
   - When the group does exists and state=absent, the group will be deleted.
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
            - Name of the group you want to create.
        required: true
    path:
        description:
            - The path of the group you want to create, this will be server_url/group_path
            - If not supplied, the group_name will be used.
        required: false
        default: null
    state:
        description:
            - create or delete group.
            - Possible values are present and absent.
        required: false
        default: "present"
        choices: ["present", "absent"]
'''

EXAMPLES = '''
- name: "Delete Gitlab Group"
  local_action: gitlab_group
                server_url="http://gitlab.dj-wasabi.local"
                validate_certs=false
                login_token="WnUzDsxjy8230-Dy_k"
                name=my_first_group
                state=absent

- name: "Create Gitlab Group"
  local_action: gitlab_group
                server_url="https://gitlab.dj-wasabi.local"
                validate_certs=true
                login_user=dj-wasabi
                login_password="MySecretPassword"
                name=my_first_group
                path=my_first_group
                state=present
'''

RETURN = '''# '''

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except:
    HAS_GITLAB_PACKAGE = False


class GitLabGroup(object):
    def __init__(self, module, git):
        self._module = module
        self._gitlab = git

    def createGroup(self, group_name, group_path):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        return self._gitlab.creategroup(group_name, group_path)

    def deleteGroup(self, group_name):
        is_group_empty = True
        group_id = self.idGroup(group_name)

        for project in self._gitlab.getall(self._gitlab.getprojects):
            owner = project['namespace']['name']
            if owner == group_name:
                is_group_empty = False

        if is_group_empty:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            return self._gitlab.deletegroup(group_id)
        else:
            self._module.fail_json(msg="There are still projects in this group. These needs to be moved or deleted before this group can be removed.")

    def existsGroup(self, group_name):
        for group in self._gitlab.getall(self._gitlab.getgroups):
            if group['name'] == group_name:
                return True
        return False

    def idGroup(self, group_name):
        for group in self._gitlab.getall(self._gitlab.getgroups):
            if group['name'] == group_name:
                return group['id']


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            validate_certs=dict(required=False, default=True, type=bool, aliases=['verify_ssl']),
            login_user=dict(required=False, no_log=True),
            login_password=dict(required=False, no_log=True),
            login_token=dict(required=False, no_log=True),
            name=dict(required=True),
            path=dict(required=False),
            state=dict(default="present", choices=["present", "absent"]),
        ),
        supports_check_mode=True
    )

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg="Missing requried gitlab module (check docs or install with: pip install pyapi-gitlab")

    server_url = module.params['server_url']
    verify_ssl = module.params['validate_certs']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
    group_name = module.params['name']
    group_path = module.params['path']
    state = module.params['state']

    # We need both login_user and login_password or login_token, otherwise we fail.
    if login_user is not None and login_password is not None:
        use_credentials = True
    elif login_token is not None:
        use_credentials = False
    else:
        module.fail_json(msg="No login credentials are given. Use login_user with login_password, or login_token")

    # Set group_path to group_name if it is empty.
    if group_path is None:
        group_path = group_name.replace(" ", "_")

    # Lets make an connection to the Gitlab server_url, with either login_user and login_password
    # or with login_token
    try:
        if use_credentials:
            git = gitlab.Gitlab(host=server_url)
            git.login(user=login_user, password=login_password)
        else:
            git = gitlab.Gitlab(server_url, token=login_token, verify_ssl=verify_ssl)
    except Exception, e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s " % e)

    # Validate if group exists and take action based on "state"
    group = GitLabGroup(module, git)
    group_name = group_name.lower()
    group_exists = group.existsGroup(group_name)

    if group_exists and state == "absent":
        group.deleteGroup(group_name)
        module.exit_json(changed=True, result="Successfully deleted group %s" % group_name)
    else:
        if state == "absent":
            module.exit_json(changed=False, result="Group deleted or does not exists")
        else:
            if group_exists:
                module.exit_json(changed=False)
            else:
                if group.createGroup(group_name, group_path):
                    module.exit_json(changed=True, result="Successfully created or updated the group %s" % group_name)


from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
