#!/usr/bin/env python
# Copyright: (c) 2015, Werner Dijkerman (ikben@werner-dijkerman.nl)
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
   - When the group does exist and state=absent, the group will be deleted.
version_added: "2.1"
author: "Werner Dijkerman (@dj-wasabi)"
requirements:
    - python-gitlab python module
options:
    server_url:
        description:
            - Url of Gitlab server, with protocol (http or https).
        required: true
    verify_ssl:
        description:
            - When using https if SSL certificate needs to be verified.
        type: bool
        default: 'yes'
        aliases:
            - validate_certs
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
            - Name of the group you want to create.
        required: true
    path:
        description:
            - The path of the group you want to create, this will be server_url/group_path
            - If not supplied, the group_name will be used.
    description:
        description:
            - A description for the group.
        version_added: "2.7"
    state:
        description:
            - create or delete group.
            - Possible values are present and absent.
        default: "present"
        choices: ["present", "absent"]
    parent:
        description:
            - Allow to create subgroups
            - Must contain the full path of the parent.
        version_added: "2.8"
    visibility:
        description:
            - Default visibility of the group
        version_added: "2.8"
        choices: ["private", "internal", "public"]
        default: "private"
'''

EXAMPLES = '''
- name: "Delete Gitlab Group"
  local_action:
    gitlab_group:
        server_url: "http://gitlab.dj-wasabi.local"
        validate_certs: False
        login_token: WnUzDsxjy8230-Dy_k
        name: my_first_group
        state: absent

- name: "Create Gitlab Group"
  local_action:
    gitlab_group:
        server_url: "https://gitlab.dj-wasabi.local"
        validate_certs: True
        login_user: dj-wasabi
        login_password: "MySecretPassword"
        name: my_first_group
        path: my_first_group
        state: present

# The group will by created at https://gitlab.dj-wasabi.local/super_parent/parent/my_first_group
- name: "Create Gitlab SubGroup"
  local_action:
    gitlab_group:
        server_url: "https://gitlab.dj-wasabi.local"
        validate_certs: True
        login_user: dj-wasabi
        login_password: "MySecretPassword"
        name: my_first_group
        path: my_first_group
        state: present
        parent_path: "super_parent/parent"
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


class GitLabGroup(object):
    def __init__(self, module, gitlab_instance):
        self._module = module
        self._gitlab = gitlab_instance
        self.groupObject = None

    '''
    @param group Group object
    '''
    def getGroupId(self, group):
        if group is not None:
            return group.id
        return None

    '''
    @param name Name of the group
    @param path Path of the group
    @param description Description of the group
    @param parent Parent group full path
    '''
    def createOrUpdateGroup(self, name, path, description, parent, visibility):
        changed = False

        # Because we have already call userExists in main()
        if self.groupObject is None:
            parent_id = self.getGroupId(parent)

            group = self.createGroup({
                'name': name,
                'path': path,
                'parent_id': parent_id})
            changed = True
        else:
            changed, group = self.updateGroup(self.groupObject, {
                'name': name,
                'description': description,
                'visibility': visibility})

        self.groupObject = group
        if changed:
            if self._module.check_mode:
                self._module.exit_json(changed=True, result="Group should have updated.")

            try:
                group.save()
            except Exception as e:
                self._module.fail_json(msg="Failed to create or update a group: %s " % e)
            return True
        else:
            return False

    def createGroup(self, arguments):
        group = self._gitlab.groups.create(arguments)
        return group

    def updateGroup(self, group, arguments):
        changed = False

        for arg_key, arg_value in arguments.items():
            if arguments[arg_key] is not None:
                if getattr(group, arg_key) != arguments[arg_key]:
                    setattr(group, arg_key, arguments[arg_key])
                    changed = True

        return (changed, group)

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
            except Exception as e:
                self._module.fail_json(msg="Failed to delete a group: %s " % e)

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
    @param name Name of the groupe
    @param full_path Complete path of the Group including parent group path. <parent_path>/<group_path>
    '''
    def existsGroup(self, name, full_path):
        # When group/user exists, object will be stored in self.groupObject.
        group = self.findGroup(name, full_path)
        if group:
            self.groupObject = group
            return True
        return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True, type='str'),
            verify_ssl=dict(required=False, default=True, type='bool', aliases=['validate_certs']),
            login_user=dict(required=False, no_log=True, type='str'),
            login_password=dict(required=False, no_log=True, type='str'),
            login_token=dict(required=False, no_log=True, type='str'),
            name=dict(required=True, type='str'),
            path=dict(required=False, type='str'),
            description=dict(required=False, default="", type='str'),
            state=dict(required=False, default="present", choices=["present", "absent"]),
            parent=dict(required=False, default="", type="str"),
            visibility=dict(required=False, default="private", choices=["private", "internal", "public"])
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
    group_name = module.params['name']
    group_path = module.params['path']
    description = module.params['description']
    state = module.params['state']
    parent_path = module.params['parent']
    group_visibility = module.params['visibility']

    parent_name = parent_path.split('/').pop()
    group_full_path = os.path.join(parent_path, group_path)

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
            Gitlab remove Session API now that private tokens are removed from user API endpoints since version 10.2" % to_native(e))

    # Define default group_path based on group_name
    if group_path is None:
        group_path = group_name.replace(" ", "_")

    gitlab_group = GitLabGroup(module, gitlab_instance)
    group_exists = gitlab_group.existsGroup(group_name, group_full_path)

    if state == 'absent':
        if group_exists:
            gitlab_group.deleteGroup()
            module.exit_json(changed=True, result="Successfully deleted group %s" % group_name)
        else:
            module.exit_json(changed=False, result="Group deleted or does not exists")

    if state == 'present':
        parent_group = None
        if parent_path:
            parent_group = gitlab_group.findGroup(parent_name, parent_path)
            if not parent_group:
                module.fail_json(msg="Failed create Gitlab group: Parent group doesn't exists")

        if gitlab_group.createOrUpdateGroup(group_name, group_path, description, parent_group, group_visibility):
            module.exit_json(changed=True, result="Successfully created or updated the group %s" % group_name, group=gitlab_group.groupObject._attrs)
        else:
            module.exit_json(changed=False, result="No need to update the group %s" % group_name, group=gitlab_group.groupObject._attrs)


if __name__ == '__main__':
    main()
