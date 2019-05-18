#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Markus Bergholz (markuman@gmail.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: gitlab_project_variable
short_description: Creates/updates/deletes Gitlab Projects Variables
description:
  - When a project variable does not exists, it will be created.
  - When a project variable does exists, its value will be updated when the values are different.
  - Variables which are presented in the playbook, but are not presented in the Gitlab project,
    they stay untouched (purged_vars = False) or will be deleted (purged_vars = True).
version_added: "2.9"
author:
    - "Markus Bergholz (@markuman)"
requirements:
  - python >= 2.7
  - python-gitlab python module
options:
  state:
    description:
      - create or delete project variable.
      - Possible values are present and absent.
    default: present
    type: str
    choices: ["present", "absent"]
  server_url:
    description:
      - The URL of the Gitlab server, with protocol (i.e. http or https).
    required: true
    type: str
  login_token:
    description:
      - Gitlab access token with api permissions.
    required: true
    type: str
  name:
    description:
      - The path and name of the project
    required: true
    type: str
  purge_vars:
    description:
      - When set to true, all variables which are not presented in the task will be deleted.
    default: false
    required: false
    type: bool
  vars:
    description:
      - A list of key value pairs
    default: []
    required: false
    type: list
'''


EXAMPLES = '''
- name: Set or update some CI/CD variables
  gitlab_project_variables:
    server_url: gitlab.com
    login_token: secret_access_token
    name: markuman/dotfiles
    purge_vars: False
    vars:
      - ACCESS_KEY_ID: abc123
      - SECRET_ACCESS_KEY: 321cba

- name: delete one variable
  gitlab_project_variables:
    server_url: gitlab.com
    login_token: secret_access_token
    name: markuman/dotfiles
    state: absent
    vars:
      - ACCESS_KEY_ID: abc123
'''

RETURN = '''# '''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except Exception:
    HAS_GITLAB_PACKAGE = False


class gitlab_project_variables(object):

    def __init__(self, login_token, project_name, server_url):
        self.repo = gitlab.Gitlab(
            '{server_url}'.format(server_url=server_url), private_token=login_token)
        self.repo.auth()
        self.project = self.get_project(project_name)

    def get_project(self, project_name):
        return self.repo.projects.get(project_name)

    def list_all_project_variables(self):
        raw_variable_list = self.project.variables.list()
        retval = []
        if len(raw_variable_list) > 0:
            for item in raw_variable_list:
                retval.append(item.get_id())
        return retval

    def create_variable(self, key, value):
        return self.project.variables.create({"key": key, "value": value})

    def update_variable(self, key, value):
        var = self.project.variables.get(key)
        if var.value == value:
            return False
        var.save()
        return True

    def delete_variable(self, key):
        return self.project.variables.delete(key)


def native_python_main(server_url, login_token, project_name, purge_vars, var_list, state):

    change = False
    this_gitlab = gitlab_project_variables(
        login_token=login_token, project_name=project_name, server_url=server_url)

    existing_variables = this_gitlab.list_all_project_variables()

    for idx in range(len(var_list)):
        key = list(var_list[idx].keys())[0]
        if key in existing_variables and state == 'present':
            change = this_gitlab.update_variable(
                key, var_list[idx][key]) or change
            pop_index = existing_variables.index(key)
            existing_variables.pop(pop_index)
        elif key not in existing_variables and state == 'present':
            this_gitlab.create_variable(key, var_list[idx][key])
            change = True
        elif key in existing_variables and state == 'absent':
            this_gitlab.delete_variable(key)
            change = True

    if len(existing_variables) > 0 and purge_vars:
        for item in existing_variables:
            this_gitlab.delete_variable(item)
            change = True

    existing_variables = this_gitlab.list_all_project_variables()
    return change


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True, type='str'),
            login_token=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            purge_vars=dict(required=False, default=False, type='bool'),
            vars=dict(required=False, default=list(), type='list'),
            state=dict(type='str', default="present", choices=["absent", "present"])
        )
    )

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(
            msg="Missing required gitlab module (check docs or install with: pip install python-gitlab")

    server_url = module.params['server_url']
    login_token = module.params['login_token']
    purge_vars = module.params['purge_vars']
    var_list = module.params['vars']
    project_name = module.params['name']
    state = module.params['state']

    change = native_python_main(
        server_url, login_token, project_name, purge_vars, var_list, state)

    module.exit_json(changed=change, gitlab_project_variables=None)


if __name__ == '__main__':
    main()
