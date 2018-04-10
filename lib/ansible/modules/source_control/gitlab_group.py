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
module: gitlab_group
short_description: Creates/updates/deletes Gitlab Groups
description:
   - When the group does not exist in Gitlab, it will be created.
   - When the group does exists and state=absent, the group will be deleted.
   - When changes are made to the group, the group will be updated.
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
            - Name of the group you want to create.
        required: true
    path:
        description:
            - The path of the group you want to create, this will be server_url/group_path
            - If not supplied, the group_name will be used.
        required: false
        default: null
    description:
        description:
            - A description for the group.
        required: false
        default: null
    parent_name:
        description:
            - Name of the parent group for creating nested group.
        required: false
        default: null
    lfs_enabled:
        description:
            - Enable/Disable Large File Storage (LFS) for the projects in this group.
        required: false
        choices: ["true", "false"]
        default: true
    request_access_enabled:
        description:
            - Allow users to request member access.
        required: false
        choices: ["true", "false"]
        default: false
    visibility_level:
        description:
            - Private. visibility_level is 0. Project access must be granted explicitly for each user.
            - Internal. visibility_level is 10. The project can be cloned by any logged in user.
            - Public. visibility_level is 20. The project can be cloned without any authentication.
            - Possible values are 0, 10 and 20.
        required: false
        default: 0
    state:
        description:
            - create or delete group.
            - Possible values are present and absent.
        required: false
        default: "present"
        choices: ["present", "absent"]
'''

EXAMPLES = '''
- name: Delete Gitlab Group
  gitlab_group:
    server_url: http://gitlab.example.com
    validate_certs: False
    login_token: WnUzDsxjy8230-Dy_k
    name: my_first_group
    state: absent
  delegate_to: localhost

- name: Create Gitlab Group
  gitlab_group:
    server_url: https://gitlab.example.com
    validate_certs: True
    login_user: dj-wasabi
    login_password: MySecretPassword
    name: my_first_group
    path: my_first_group
    parent_name: my_parent_group
    lfs_enabled: True
    request_access_enabled: False
    state: present
  delegate_to: localhost
'''

RETURN = '''# '''

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import *
from ansible.module_utils.pycompat24 import get_exception


class GitLabGroup(object):
    def __init__(self, module, git):
        self._module = module
        self._gitlab = git
        self.groupObject = None

    def createOrUpdateGroup(self, arguments):
        changed = False
        if self.groupObject is None:
            try:
                group = self._gitlab.groups.create(arguments)
                changed = True
            except Exception:
                e = get_exception()
                self._module.fail_json(msg="Failed to create a group: %s " % e)
        else:
            group = self.groupObject

        group_dict = group.as_dict()
        for arg_key, arg_value in arguments.items():
            group_data_value = group_dict.get(arg_key)
            if isinstance(group_data_value, bool):
                to_bool = self.to_bool(group_data_value)
                if to_bool != self.to_bool(arg_value):
                    changed = True
                    continue
            else:
                if group_data_value != arg_value:
                    changed = True

        if changed:
            if self._module.check_mode:
                self._module.exit_json(changed=True, result="Group should have updated.")
            try:
                group.save()
            except Exception:
                e = get_exception()
                self._module.fail_json(msg="Failed to create or update a group: %s " % e)
            return True
        else:
            return False

    def deleteGroup(self):
        group = self.groupObject
        if len(group.projects.list()) >= 1:
            self._module.fail_json(
                msg="There are still projects in this group. These needs to be moved or deleted before this group can be removed.")
        else:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            try:
                group.delete()
            except Exception:
                e = get_exception()
                self._module.fail_json(msg="Failed to delete a group: %s " % e)
            return True

    def existsGroup(self, name):
        """When group/user exists, object will be stored in self.groupObject."""
        groups = self._gitlab.groups.search(name)
        if len(groups) == 1:
            self.groupObject = groups[0]
            return True

    def getGroupId(self, group_name):
        groups = self._gitlab.groups.search(group_name)
        if len(groups) == 1:
            return groups[0].id

    def to_bool(self, value):
        if value:
            return 1
        else:
            return 0


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True, type='str'),
            validate_certs=dict(required=False, default=True, type='bool', aliases=['verify_ssl']),
            login_user=dict(required=False, no_log=True, type='str'),
            login_password=dict(required=False, no_log=True, type='str'),
            login_token=dict(required=False, no_log=True, type='str'),
            name=dict(required=True, type='str'),
            path=dict(required=False, type='str'),
            description=dict(default="", required=False, type='str'),
            parent_name=dict(required=False, type='str'),
            lfs_enabled=dict(default=True, type='bool'),
            request_access_enabled=dict(default=False, type='bool'),
            visibility_level=dict(default="0", choices=["0", "10", "20"]),
            state=dict(default="present", choices=["present", "absent"]),
        ),
        supports_check_mode=True
    )

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg="Missing required gitlab module (check docs or "
                             "install with: pip install python-gitlab")

    server_url = module.params['server_url']
    verify_ssl = module.params['validate_certs']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
    group_name = module.params['name']
    group_path = module.params['path']
    description = module.params['description']
    parent_group_name = module.params['parent_name']
    lfs_enabled = module.params['lfs_enabled']
    request_access_enabled = module.params['request_access_enabled']
    visibility_level = module.params['visibility_level']
    state = module.params['state']
    use_credentials = None

    # Validate some credentials configuration parameters.
    if login_user is not None and login_password is not None:
        use_credentials = True
    elif login_token is not None:
        use_credentials = False
    else:
        module.fail_json(msg="No login credentials are given. Use login_user with login_password, or login_token")

    if login_token and login_user:
        module.fail_json(msg="You can either use 'login_token' or 'login_user' and 'login_password'")

    # Lets make an connection to the Gitlab server_url, with either login_user and login_password
    # or with login_token
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

    # Set group_path to group_name if it is empty.
    if group_path is None:
        group_path = group_name.replace(" ", "_")

    # Gitlab API makes no difference between upper and lower cases, so we lower them.
    if group_name is not None:
        group_name = group_name.lower()
    if group_path is not None:
        group_path = group_path.lower()

    # Validate if group exists and take action based on "state"
    group = GitLabGroup(module, git)
    group_exists = group.existsGroup(group_name)

    # Get id of the parent group
    parent_id = None
    if parent_group_name:
        parent_id = group.getGroupId(parent_group_name)

    # Creating the project dict
    arguments = {"name": group_name,
                 "path": group_path,
                 "description": description,
                 "parent_id": parent_id,
                 "lfs_enabled": group.to_bool(lfs_enabled),
                 "request_access_enabled": group.to_bool(request_access_enabled),
                 "visibility_level": int(visibility_level)}

    if group_exists and state == "absent":
        group.deleteGroup(group_name)
        module.exit_json(changed=True, result="Successfully deleted group %s" % group_name)
    else:
        if state == "absent":
            module.exit_json(changed=False, result="Group deleted or does not exist")
        else:
            if group.createOrUpdateGroup(arguments):
                module.exit_json(changed=True, result="Successfully created or updated the group %s" % group_name)
            else:
                module.exit_json(changed=False, result="No need to update the group %s" % group_name)


if __name__ == '__main__':
    main()
