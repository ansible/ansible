#!/usr/bin/python
# Copyright: (c) 2019, Guillaume Martinez (guillaume.lunik@gmail.com)
# Copyright: (c) 2018, Samy Coenen <samy.coenen@nubera.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gitlab_runner
short_description: Create, modify and delete GitLab Runners.
description:
  - Register, update and delete runners with the GitLab API.
  - All operations are performed using the GitLab API v4.
  - For details, consult the full API documentation at U(https://docs.gitlab.com/ee/api/runners.html).
  - A valid private API token is required for all operations. You can create as many tokens as you like using the GitLab web interface at
    U(https://$GITLAB_URL/profile/personal_access_tokens).
  - A valid registration token is required for registering a new runner.
    To create shared runners, you need to ask your administrator to give you this token.
    It can be found at U(https://$GITLAB_URL/admin/runners/).
notes:
  - Instead of the private_token parameter, the GITLAB_PRIVATE_TOKEN environment variable can be used.
  - To create a new runner at least the C(private_token), C(registration_token), C(name) and C(url) options are required.
  - Runners need to have unique names.
version_added: 2.8
author: "Samy Coenen (@SamyCoenen)"
requirements:
  - python-gitlab python module
options:
  login_token:
    description:
      - Your private token to interact with the GitLab API.
    required: True
    type: str
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
  description:
    description:
      - The unique name of the runner.
    required: True
    type: str
    aliases:
      - name
  state:
    description:
      - Make sure that the runner with the same name exists with the same configuration or delete the runner with the same name.
    required: False
    default: "present"
    choices: ["present", "absent"]
    type: str
  registration_token:
    description:
      - The registration token is used to register new runners.
    required: True
    type: str
  server_url:
    description:
      - The GitLab URL including the API v4 path and http or https.
    required: False
    type: str
  active:
    description:
      - Define if the runners is immediately active after creation.
    required: False
    default: True
    type: bool
  locked:
    description:
      - Determines if the runner is locked or not.
    required: False
    default: False
    type: bool
  access_level:
    description:
      - Determines if a runner can pick up jobs from protected branches.
    required: False
    default: "ref_protected"
    choices: ["ref_protected", "not_protected"]
    type: str
  maximum_timeout:
    description:
      - The maximum timeout that a runner has to pick up a specific job.
    required: False
    default: 3600
    type: int
  run_untagged:
    description:
      - Run untagged jobs or not.
    required: False
    default: True
    type: bool
  tag_list:
    description: The tags that apply to the runner.
    required: False
    default: []
    type: list
'''

EXAMPLES = '''
# Register a new runner (if it does not exist)

- name: Register runner
  gitlab_runner:
    server_url: "https://gitlab.com/"
    login_token: 5432632464326432632463246
    registration_token: 4gfdsg345
    description: Docker Machine t1
    state: present
    active: True
    tag_list: ['docker']
    run_untagged: False
    locked: False

# Delete a runner
- name: Delete runner
  gitlab_runner:
    server_url: "https://gitlab.com/"
    login_token: 5432632464326432632463246
    description: Docker Machine t1
    state: absent
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

runner:
  description: API object
  returned: always
  type: dict
'''

import os

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except Exception:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

try:
    cmp
except NameError:
    def cmp(a, b):
        return (a > b) - (a < b)


class GitLabRunner(object):
    def __init__(self, module, gitlab_instance):
        self._module = module
        self._gitlab = gitlab_instance
        self.runnerObject = None

    def createOrUpdateRunner(self, description, options):
        changed = False

        # Because we have already call userExists in main()
        if self.runnerObject is None:
            runner = self.createRunner({
                'description': description,
                'active': options['active'],
                'token': options['registration_token'],
                'locked': options['locked'],
                'run_untagged': options['run_untagged'],
                'maximum_timeout': options['maximum_timeout'],
                'tag_list': options['tag_list']})
            changed = True
        else:
            changed, runner = self.updateRunner(self.runnerObject, {
                'active': options['active'],
                'locked': options['locked'],
                'run_untagged': options['run_untagged'],
                'maximum_timeout': options['maximum_timeout'],
                'access_level': options['access_level'],
                'tag_list': options['tag_list']})

        self.runnerObject = runner
        if changed:
            if self._module.check_mode:
                self._module.exit_json(changed=True, result="Runner should have been updated.")

            try:
                runner.save()
            except Exception as e:
                self._module.fail_json(msg="Failed to update a runner: %s " % to_native(e))
            return True
        else:
            return False

    '''
    @param arguments Attributs of the runner
    '''
    def createRunner(self, arguments):
        if self._module.check_mode:
                self._module.exit_json(changed=True, result="Runner should have been created.")

        try:
            runner = self._gitlab.runners.create(arguments)
        except (gitlab.exceptions.GitlabCreateError) as e:
            self._module.fail_json(msg="Failed to create a runner: %s " % to_native(e))

        return runner

    '''
    @param runner Runner object
    @param arguments Attributs of the runner
    '''
    def updateRunner(self, runner, arguments):
        changed = False

        for arg_key, arg_value in arguments.items():
            if arguments[arg_key] is not None:
                if isinstance(arguments[arg_key], list):
                    list1 = getattr(runner, arg_key)
                    list1.sort()
                    list2 = arguments[arg_key]
                    list2.sort()
                    if cmp(list1, list2):
                        setattr(runner, arg_key, arguments[arg_key])
                        changed = True
                else:
                    if getattr(runner, arg_key) != arguments[arg_key]:
                        setattr(runner, arg_key, arguments[arg_key])
                        changed = True

        return (changed, runner)

    '''
    @param description Description of the runner
    '''
    def findRunner(self, description):
        runners = self._gitlab.runners.all()
        for runner in runners:
            if (runner['description'] == description):
                return self._gitlab.runners.get(runner['id'])

    '''
    @param description Description of the runner
    '''
    def existsRunner(self, description):
        # When runner exists, object will be stored in self.runnerObject.
        runner = self.findRunner(description)

        if runner:
            self.runnerObject = runner
            return True
        return False

    def deleteRunner(self):
        if self._module.check_mode:
            self._module.exit_json(changed=True, result="Runner should have been deleted.")

        runner = self.runnerObject

        return runner.delete()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True, type='str'),
            verify_ssl=dict(required=False, default=True, type='bool', aliases=['validate_certs']),
            login_user=dict(required=False, no_log=True, type='str'),
            login_password=dict(required=False, no_log=True, type='str'),
            login_token=dict(required=False, no_log=True, type='str'),
            description=dict(required=True, type='str', aliases=['name']),
            active=dict(required=False, type='bool', default=True),
            tag_list=dict(required=False, type='list', default=[]),
            run_untagged=dict(required=False, type='bool', default=True),
            locked=dict(required=False, type='bool', default=False),
            access_level=dict(required=False, type='str', default='ref_protected', choices=["ref_protected", "not_protected"]),
            maximum_timeout=dict(required=False, type='int', default=3600),
            registration_token=dict(required=True, type='str'),
            state=dict(required=False, type='str', default="present", choices=["present", "absent"])
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
    state = module.params['state']
    runner_description = module.params['description']
    runner_active = module.params['active']
    tag_list = module.params['tag_list']
    run_untagged = module.params['run_untagged']
    runner_locked = module.params['locked']
    access_level = module.params['access_level']
    maximum_timeout = module.params['maximum_timeout']
    registration_token = module.params['registration_token']

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

    gitlab_runner = GitLabRunner(module, gitlab_instance)
    runner_exists = gitlab_runner.existsRunner(runner_description)

    if state == 'absent':
        if runner_exists:
            gitlab_runner.deleteRunner()
            module.exit_json(changed=True, result="Successfully deleted runner %s" % runner_description)
        else:
            module.exit_json(changed=False, result="Runner deleted or does not exists")

    if state == 'present':
        if gitlab_runner.createOrUpdateRunner(runner_description, {
                                              "active": runner_active,
                                              "tag_list": tag_list,
                                              "run_untagged": run_untagged,
                                              "locked": runner_locked,
                                              "access_level": access_level,
                                              "maximum_timeout": maximum_timeout,
                                              "registration_token": registration_token}):
            module.exit_json(changed=True, runner=gitlab_runner.runnerObject._attrs,
                             result="Successfully created or updated the runner %s" % runner_description)
        else:
            module.exit_json(changed=False, runner=gitlab_runner.runnerObject._attrs,
                             result="No need to update the runner %s" % runner_description)


if __name__ == '__main__':
    main()
