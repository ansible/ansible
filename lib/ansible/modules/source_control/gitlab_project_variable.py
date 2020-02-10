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
short_description: Creates/updates/deletes GitLab Projects Variables
description:
  - When a project variable does not exist, it will be created.
  - When a project variable does exist, its value will be updated when the values are different.
  - Variables which are untouched in the playbook, but are not untouched in the GitLab project,
    they stay untouched (I(purge) is C(false)) or will be deleted (I(purge) is C(true)).
version_added: "2.9"
author:
  - "Markus Bergholz (@markuman)"
requirements:
  - python >= 2.7
  - python-gitlab python module <= 1.12.1
extends_documentation_fragment:
  - auth_basic
options:
  state:
    description:
      - Create or delete project variable.
      - Possible values are present and absent.
    default: present
    type: str
    choices: ["present", "absent"]
  api_token:
    description:
      - GitLab access token with API permissions.
    required: true
    type: str
  project:
    description:
      - The path and name of the project.
    required: true
    type: str
  purge:
    description:
      - When set to true, all variables which are not untouched in the task will be deleted.
    default: false
    type: bool
  vars:
    description:
      - A list of key value pairs.
    default: {}
    type: dict
'''


EXAMPLES = '''
- name: Set or update some CI/CD variables
  gitlab_project_variable:
    api_url: https://gitlab.com
    api_token: secret_access_token
    project: markuman/dotfiles
    purge: false
    vars:
      ACCESS_KEY_ID: abc123
      SECRET_ACCESS_KEY: 321cba

- name: Delete one variable
  gitlab_project_variable:
    api_url: https://gitlab.com
    api_token: secret_access_token
    project: markuman/dotfiles
    state: absent
    vars:
      ACCESS_KEY_ID: abc123
'''

RETURN = '''
project_variable:
  description: Four lists of the variablenames which were added, updated, removed or exist.
  returned: always
  type: dict
  contains:
    added:
      description: A list of variables which were created.
      returned: always
      type: list
      sample: "['ACCESS_KEY_ID', 'SECRET_ACCESS_KEY']"
    untouched:
      description: A list of variables which exist.
      returned: always
      type: list
      sample: "['ACCESS_KEY_ID', 'SECRET_ACCESS_KEY']"
    removed:
      description: A list of variables which were deleted.
      returned: always
      type: list
      sample: "['ACCESS_KEY_ID', 'SECRET_ACCESS_KEY']"
    updated:
      description: A list of variables whose values were changed.
      returned: always
      type: list
      sample: "['ACCESS_KEY_ID', 'SECRET_ACCESS_KEY']"
'''

import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native
from ansible.module_utils.api import basic_auth_argument_spec


GITLAB_IMP_ERR = None
try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except Exception:
    GITLAB_IMP_ERR = traceback.format_exc()
    HAS_GITLAB_PACKAGE = False


class GitlabProjectVariables(object):

    def __init__(self, module, gitlab_instance):
        self.repo = gitlab_instance
        self.project = self.get_project(module.params['project'])
        self._module = module

    def get_project(self, project_name):
        return self.repo.projects.get(project_name)

    def list_all_project_variables(self):
        return self.project.variables.list()

    def create_variable(self, key, value):
        if self._module.check_mode:
            return
        return self.project.variables.create({"key": key, "value": value})

    def update_variable(self, var, value):
        if var.value == value:
            return False
        if self._module.check_mode:
            return True
        var.value = value
        var.save()
        return True

    def delete_variable(self, key):
        if self._module.check_mode:
            return
        return self.project.variables.delete(key)


def native_python_main(this_gitlab, purge, var_list, state):

    change = False
    return_value = dict(added=list(), updated=list(), removed=list(), untouched=list())

    gitlab_keys = this_gitlab.list_all_project_variables()
    existing_variables = [x.get_id() for x in gitlab_keys]

    for key in var_list:
        if key in existing_variables:
            index = existing_variables.index(key)
            existing_variables[index] = None

            if state == 'present':
                single_change = this_gitlab.update_variable(
                    gitlab_keys[index], var_list[key])
                change = single_change or change
                if single_change:
                    return_value['updated'].append(key)
                else:
                    return_value['untouched'].append(key)

            elif state == 'absent':
                this_gitlab.delete_variable(key)
                change = True
                return_value['removed'].append(key)

        elif key not in existing_variables and state == 'present':
            this_gitlab.create_variable(key, var_list[key])
            change = True
            return_value['added'].append(key)

    existing_variables = list(filter(None, existing_variables))
    if purge:
        for item in existing_variables:
            this_gitlab.delete_variable(item)
            change = True
            return_value['removed'].append(item)
    else:
        return_value['untouched'].extend(existing_variables)

    return change, return_value


def main():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(
        api_token=dict(type='str', required=True, no_log=True),
        project=dict(type='str', required=True),
        purge=dict(type='bool', required=False, default=False),
        vars=dict(type='dict', required=False, default=dict(), no_log=True),
        state=dict(type='str', default="present", choices=["absent", "present"])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['api_username', 'api_token'],
            ['api_password', 'api_token'],
        ],
        required_together=[
            ['api_username', 'api_password'],
        ],
        required_one_of=[
            ['api_username', 'api_token']
        ],
        supports_check_mode=True
    )

    api_url = module.params['api_url']
    gitlab_token = module.params['api_token']
    purge = module.params['purge']
    var_list = module.params['vars']
    state = module.params['state']

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg=missing_required_lib("python-gitlab"), exception=GITLAB_IMP_ERR)

    try:
        gitlab_instance = gitlab.Gitlab(url=api_url, private_token=gitlab_token)
        gitlab_instance.auth()
    except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabGetError) as e:
        module.fail_json(msg="Failed to connect to GitLab server: %s" % to_native(e))
    except (gitlab.exceptions.GitlabHttpError) as e:
        module.fail_json(msg="Failed to connect to GitLab server: %s. \
            GitLab remove Session API now that private tokens are removed from user API endpoints since version 10.2" % to_native(e))

    this_gitlab = GitlabProjectVariables(module=module, gitlab_instance=gitlab_instance)

    change, return_value = native_python_main(this_gitlab, purge, var_list, state)

    module.exit_json(changed=change, project_variable=return_value)


if __name__ == '__main__':
    main()
