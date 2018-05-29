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
   - When the group does exist and state=absent, the group will be deleted.
   - As of Ansible version 2.7, this module make use of a different python module and thus some arguments are deprecated.
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
        version_added: "2.7"
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
  local_action:
    gitlab_group:
        server_url: http://gitlab.dj-wasabi.local
        validate_certs: False
        login_token: WnUzDsxjy8230-Dy_k
        name: my_first_group
        state: absent

- name: "Create Gitlab Group"
  local_action:
    gitlab_group:
        server_url: https://gitlab.dj-wasabi.local"
        validate_certs: True
        login_user: dj-wasabi
        login_password: "MySecretPassword"
        name: my_first_group
        path: my_first_group
        state: present
'''

RETURN = '''# '''

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class GitLabGroup(object):
    def __init__(self, module, git):
        self._module = module
        self._gitlab = git
        self.groupObject = None

    def createOrUpdateGroup(self, name, path, description):
        changed = False
        if self.groupObject is None:
            group = self._gitlab.groups.create({'name': name, 'path': path})
            changed = True
        else:
            group = self.groupObject

        if description is not None:
            if group.description != description:
                group.description = description
                changed = True

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
            return True

    def existsGroup(self, name):
        """When group/user exists, object will be stored in self.groupObject."""
        groups = self._gitlab.groups.list(search=name)
        if len(groups) == 1:
            self.groupObject = groups[0]
            return True


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
            description=dict(required=False, type='str'),
            state=dict(default="present", choices=["present", "absent"]),
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

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg="Missing requried gitlab module (check docs or install with: pip install python-gitlab")

    server_url = module.params['server_url']
    validate_certs = module.params['validate_certs']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
    group_name = module.params['name']
    group_path = module.params['path']
    description = module.params['description']
    state = module.params['state']

    try:
        git = gitlab.Gitlab(url=server_url, ssl_verify=validate_certs, email=login_user, password=login_password,
                            private_token=login_token, api_version=4)
        git.auth()
    except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabGetError) as e:
        module.fail_json(msg='Failed to connect to Gitlab server: %s' % to_native(e))

    if group_path is None:
        group_path = group_name.replace(" ", "_")

    group = GitLabGroup(module, git)
    group_name = group_name.lower()
    group_exists = group.existsGroup(group_name)

    if group_exists and state == "absent":
        if group.deleteGroup():
            module.exit_json(changed=True, result="Successfully deleted group %s" % group_name)
    else:
        if state == "absent":
            module.exit_json(changed=False, result="Group deleted or does not exists")
        else:
            if group.createOrUpdateGroup(name=group_name, path=group_path, description=description):
                module.exit_json(changed=True, result="Successfully created or updated the group %s" % group_name)
            else:
                module.exit_json(changed=False, result="No need to update the group %s" % group_name)


if __name__ == '__main__':
    main()
