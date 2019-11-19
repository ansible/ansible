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
module: gitlab_group
short_description: Creates/updates/deletes GitLab Groups
description:
  - When the group does not exist in GitLab, it will be created.
  - When the group does exist and state=absent, the group will be deleted.
version_added: "2.1"
author:
  - Werner Dijkerman (@dj-wasabi)
  - Guillaume Martinez (@Lunik)
requirements:
  - python >= 2.7
  - python-gitlab python module <= 1.12.1
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
      - Name of the group you want to create.
    required: true
    type: str
  path:
    description:
      - The path of the group you want to create, this will be server_url/group_path
      - If not supplied, the group_name will be used.
    type: str
  description:
    description:
      - A description for the group.
    version_added: "2.7"
    type: str
  state:
    description:
      - create or delete group.
      - Possible values are present and absent.
    default: present
    type: str
    choices: ["present", "absent"]
  parent:
    description:
      - Allow to create subgroups
      - Id or Full path of parent group in the form of group/name
    version_added: "2.8"
    type: str
  visibility:
    description:
      - Default visibility of the group
    version_added: "2.8"
    choices: ["private", "internal", "public"]
    default: private
    type: str
'''

EXAMPLES = '''
- name: "Delete GitLab Group"
  gitlab_group:
    server_url: https://gitlab.example.com/
    api_token: "{{ access_token }}"
    validate_certs: False
    name: my_first_group
    state: absent

- name: "Create GitLab Group"
  gitlab_group:
    server_url: https://gitlab.example.com/
    validate_certs: True
    api_username: dj-wasabi
    api_password: "MySecretPassword"
    name: my_first_group
    path: my_first_group
    state: present

# The group will by created at https://gitlab.dj-wasabi.local/super_parent/parent/my_first_group
- name: "Create GitLab SubGroup"
  gitlab_group:
    server_url: https://gitlab.example.com/
    validate_certs: True
    api_username: dj-wasabi
    api_password: "MySecretPassword"
    name: my_first_group
    path: my_first_group
    state: present
    parent: "super_parent/parent"
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

group:
  description: API object
  returned: always
  type: dict
'''

import os
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
    @param parent Parent group full path
    @param options Group options
    '''
    def createOrUpdateGroup(self, name, parent, options):
        changed = False

        # Because we have already call userExists in main()
        if self.groupObject is None:
            parent_id = self.getGroupId(parent)

            group = self.createGroup({
                'name': name,
                'path': options['path'],
                'parent_id': parent_id,
                'visibility': options['visibility']})
            changed = True
        else:
            changed, group = self.updateGroup(self.groupObject, {
                'name': name,
                'description': options['description'],
                'visibility': options['visibility']})

        self.groupObject = group
        if changed:
            if self._module.check_mode:
                self._module.exit_json(changed=True, msg="Successfully created or updated the group %s" % name)

            try:
                group.save()
            except Exception as e:
                self._module.fail_json(msg="Failed to update group: %s " % e)
            return True
        else:
            return False

    '''
    @param arguments Attributs of the group
    '''
    def createGroup(self, arguments):
        if self._module.check_mode:
            return True

        try:
            group = self._gitlab.groups.create(arguments)
        except (gitlab.exceptions.GitlabCreateError) as e:
            self._module.fail_json(msg="Failed to create group: %s " % to_native(e))

        return group

    '''
    @param group Group Object
    @param arguments Attributs of the group
    '''
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
                return True

            try:
                group.delete()
            except Exception as e:
                self._module.fail_json(msg="Failed to delete group: %s " % to_native(e))

    '''
    @param name Name of the groupe
    @param full_path Complete path of the Group including parent group path. <parent_path>/<group_path>
    '''
    def existsGroup(self, project_identifier):
        # When group/user exists, object will be stored in self.groupObject.
        group = findGroup(self._gitlab, project_identifier)
        if group:
            self.groupObject = group
            return True
        return False


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
        path=dict(type='str'),
        description=dict(type='str'),
        state=dict(type='str', default="present", choices=["absent", "present"]),
        parent=dict(type='str'),
        visibility=dict(type='str', default="private", choices=["internal", "private", "public"]),
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

    group_name = module.params['name']
    group_path = module.params['path']
    description = module.params['description']
    state = module.params['state']
    parent_identifier = module.params['parent']
    group_visibility = module.params['visibility']

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
            GitLab remove Session API now that private tokens are removed from user API endpoints since version 10.2" % to_native(e))

    # Define default group_path based on group_name
    if group_path is None:
        group_path = group_name.replace(" ", "_")

    gitlab_group = GitLabGroup(module, gitlab_instance)

    parent_group = None
    if parent_identifier:
        parent_group = findGroup(gitlab_instance, parent_identifier)
        if not parent_group:
            module.fail_json(msg="Failed create GitLab group: Parent group doesn't exists")

        group_exists = gitlab_group.existsGroup(parent_group.full_path + '/' + group_path)
    else:
        group_exists = gitlab_group.existsGroup(group_path)

    if state == 'absent':
        if group_exists:
            gitlab_group.deleteGroup()
            module.exit_json(changed=True, msg="Successfully deleted group %s" % group_name)
        else:
            module.exit_json(changed=False, msg="Group deleted or does not exists")

    if state == 'present':
        if gitlab_group.createOrUpdateGroup(group_name, parent_group, {
                                            "path": group_path,
                                            "description": description,
                                            "visibility": group_visibility}):
            module.exit_json(changed=True, msg="Successfully created or updated the group %s" % group_name, group=gitlab_group.groupObject._attrs)
        else:
            module.exit_json(changed=False, msg="No need to update the group %s" % group_name, group=gitlab_group.groupObject._attrs)


if __name__ == '__main__':
    main()
