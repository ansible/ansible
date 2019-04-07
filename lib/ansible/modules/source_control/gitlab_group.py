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
short_description: Creates/updates/deletes Gitlab Groups
description:
  - When the group does not exist in Gitlab, it will be created.
  - When the group does exist and state=absent, the group will be deleted.
version_added: "2.1"
author:
  - Werner Dijkerman (@dj-wasabi)
  - Guillaume Martinez (@Lunik)
requirements:
  - python >= 2.7
  - python-gitlab python module
extends_documentation_fragment:
    - auth_basic
options:
  server_url:
    description:
      - The URL of the Gitlab server, with protocol (i.e. http or https).
    required: true
    type: str
  login_user:
    description:
      - Gitlab user name.
    type: str
  login_password:
    description:
      - Gitlab password for login_user
    type: str
  api_token:
    description:
      - Gitlab token for logging in.
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
- name: "Delete Gitlab Group"
  gitlab_group:
    api_url: https://gitlab.example.com/
    api_token: "{{ access_token }}"
    validate_certs: False
    name: my_first_group
    state: absent

- name: "Create Gitlab Group"
  gitlab_group:
    api_url: https://gitlab.example.com/
    validate_certs: True
    api_usersername: dj-wasabi
    api_password: "MySecretPassword"
    name: my_first_group
    path: my_first_group
    state: present

# The group will by created at https://gitlab.dj-wasabi.local/super_parent/parent/my_first_group
- name: "Create Gitlab SubGroup"
  gitlab_group:
    api_url: https://gitlab.example.com/
    validate_certs: True
    api_usersername: dj-wasabi
    api_password: "MySecretPassword"
    name: my_first_group
    path: my_first_group
    state: present
    parent_path: "super_parent/parent"
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
  description: the error message returned by the Gitlab API
  returned: failed
  type: str
  sample: "400: path is already in use"

group:
  description: API object
  returned: always
  type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.gitlab import (gitlab_auth_argument_spec, gitlab_module_kwargs,
                                         gitlab, GitlabApiConnection, findGroup)


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
                'parent_id': parent_id})
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

    module.deprecate("Aliases \'{aliases}\' are deprecated".format(aliases='\', \''.join(deprecated_aliases)), 2.10)


def main():
    argument_spec = gitlab_auth_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str', required=True),
        path=dict(type='str'),
        description=dict(type='str'),
        state=dict(type='str', default="present", choices=["absent", "present"]),
        parent=dict(type='str'),
        visibility=dict(type='str', default="private", choices=["internal", "private", "public"]),
    ))

    module = AnsibleModule(argument_spec, **gitlab_module_kwargs)
    deprecation_warning(module)

    api = GitlabApiConnection(module)
    gitlab_instance = api.auth()

    group_name = module.params['name']
    group_path = module.params['path']
    description = module.params['description']
    state = module.params['state']
    parent_identifier = module.params['parent']
    group_visibility = module.params['visibility']

    # Define default group_path based on group_name
    if group_path is None:
        group_path = group_name.replace(" ", "_")

    gitlab_group = GitLabGroup(module, gitlab_instance)

    parent_group = None
    if parent_identifier:
        parent_group = findGroup(gitlab_instance, parent_identifier)
        if not parent_group:
            module.fail_json(msg="Failed create Gitlab group: Parent group doesn't exists")

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
