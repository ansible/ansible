#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (guillaume.lunik@gmail.com)
# Copyright: (c) 2018, Marcus Watkins <marwatk@marcuswatkins.net>
# Based on code:
# Copyright: (c) 2013, Phillip Gentry <phillip@cx.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: gitlab_deploy_key
short_description: Manages GitLab project deploy keys.
description:
     - Adds, updates and removes project deploy keys
version_added: "2.6"
author:
  - "Marcus Watkins (@marwatk)"
  - "Guillaume Martinez (@Lunik)"
requirements:
  - python >= 2.7
  - python-gitlab python module
options:
  server_url:
    description:
      - The URL of the Gitlab server, with protocol (i.e. http or https).
    required: true
    version_added: "2.8"
    aliases:
      - api_url
  validate_certs:
    description:
      - When using https if SSL certificate needs to be verified.
    type: bool
    default: yes
    version_added: "2.8"
  login_user:
    description:
      - Gitlab user name.
    version_added: "2.8"
  login_password:
    description:
      - Gitlab password for login_user
    version_added: "2.8"
  login_token:
    description:
      - Gitlab token for logging in.
    version_added: "2.8"
    aliases:
      - private_token
  project:
    description:
      - Id or Full path of project in the form of group/name
    required: true
  title:
    description:
      - Deploy key's title
    required: true
  key:
    description:
      - Deploy key
    required: true
  can_push:
    description:
      - Whether this key can push to the project
    type: bool
    default: no
  state:
    description:
      - When C(present) the deploy key added to the project if it doesn't exist.
      - When C(absent) it will be removed from the project if it exists
    required: true
    default: "present"
    choices: [ "present", "absent" ]
'''

EXAMPLES = '''
# Example adding a project deploy key
- gitlab_deploy_key:
    server_url: https://gitlab.example.com/api
    login_token: "{{ access_token }}"
    project: "my_group/my_project"
    title: "Jenkins CI"
    state: present
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9w..."

# Update the above deploy key to add push access
- gitlab_deploy_key:
    server_url: https://gitlab.example.com/api
    login_token: "{{ access_token }}"
    project: "my_group/my_project"
    title: "Jenkins CI"
    state: present
    can_push: yes

# Remove the previous deploy key from the project
- gitlab_deploy_key:
    server_url: https://gitlab.example.com/api
    login_token: "{{ access_token }}"
    project: "my_group/my_project"
    state: absent
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9w..."

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
  sample: "400: key is already in use"

deploy_key:
  description: API object
  returned: always
  type: dict
'''

import os
import re

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except Exception:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.gitlab import findProject


class GitLabDeployKey(object):
    def __init__(self, module, gitlab_instance):
        self._module = module
        self._gitlab = gitlab_instance
        self.deployKeyObject = None

    '''
    @param project Project object
    @param key_title Title of the key
    @param key_key String of the key
    @param key_can_push Option of the deployKey
    @param options Deploy key options
    '''
    def createOrUpdateDeployKey(self, project, key_title, key_key, options):
        changed = False

        # Because we have already call existsDeployKey in main()
        if self.deployKeyObject is None:
            deployKey = self.createDeployKey(project, {
                'title': key_title,
                'key': key_key,
                'can_push': options['can_push']})
            changed = True
        else:
            changed, deployKey = self.updateDeployKey(self.deployKeyObject, {
                'can_push': options['can_push']})

        self.deployKeyObject = deployKey
        if changed:
            if self._module.check_mode:
                self._module.exit_json(changed=True, msg="Deploy_key should have been updated.")

            try:
                deployKey.save()
            except Exception as e:
                self._module.fail_json(msg="Failed to update a deploy_key: %s " % e)
            return True
        else:
            return False

    '''
    @param project Project Object
    @param arguments Attributs of the deployKey
    '''
    def createDeployKey(self, project, arguments):
        if self._module.check_mode:
                self._module.exit_json(changed=True, msg="Deploy_key should have been created.")
        try:
            deployKey = project.keys.create(arguments)
        except (gitlab.exceptions.GitlabCreateError) as e:
            self._module.fail_json(msg="Failed to create a deploy_key: %s " % to_native(e))

        return deployKey

    '''
    @param deployKey Deploy Key Object
    @param arguments Attributs of the deployKey
    '''
    def updateDeployKey(self, deployKey, arguments):
        changed = False

        for arg_key, arg_value in arguments.items():
            if arguments[arg_key] is not None:
                if getattr(deployKey, arg_key) != arguments[arg_key]:
                    setattr(deployKey, arg_key, arguments[arg_key])
                    changed = True

        return (changed, deployKey)

    '''
    @param project Project object
    @param key_title Title of the key
    '''
    def findDeployKey(self, project, key_title):
        deployKeys = project.keys.list()
        for deployKey in deployKeys:
            if (deployKey.title == key_title):
                return deployKey

    '''
    @param project Project object
    @param key_title Title of the key
    '''
    def existsDeployKey(self, project, key_title):
        # When project exists, object will be stored in self.projectObject.
        deployKey = self.findDeployKey(project, key_title)
        if deployKey:
            self.deployKeyObject = deployKey
            return True
        return False

    def deleteDeployKey(self):
        if self._module.check_mode:
                self._module.exit_json(changed=True, msg="Deploy_key should have been deleted.")

        return self.deployKeyObject.delete()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=["api_url"]),
            validate_certs=dict(type='bool', default=True),
            login_user=dict(type='str', no_log=True),
            login_password=dict(type='str', no_log=True),
            login_token=dict(type='str', no_log=True, aliases=["private_token"]),
            state=dict(type='str', default="present", choices=["absent", "present"]),
            project=dict(type='str', required=True),
            key=dict(type='str', required=True),
            can_push=dict(type='bool', default=False),
            title=dict(type='str', required=True),
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
        supports_check_mode=True,
    )

    server_url = re.sub('/api.*', '', module.params['server_url'])
    validate_certs = module.params['validate_certs']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
    state = module.params['state']
    project_identifier = module.params['project']
    key_title = module.params['title']
    key_keyfile = module.params['key']
    key_can_push = module.params['can_push']

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg="Missing required gitlab module (check docs or install with: pip install python-gitlab")

    try:
        gitlab_instance = gitlab.Gitlab(url=server_url, ssl_verify=validate_certs, email=login_user, password=login_password,
                                        private_token=login_token, api_version=4)
        gitlab_instance.auth()
    except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabGetError) as e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s" % to_native(e))
    except (gitlab.exceptions.GitlabHttpError) as e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s. \
            Gitlab remove Session API now that private tokens are removed from user API endpoints since version 10.2." % to_native(e))

    gitlab_deploy_key = GitLabDeployKey(module, gitlab_instance)

    project = findProject(gitlab_instance, project_identifier)

    if project is None:
        module.fail_json(msg="Failed to create deploy_key: project %s doesn't exists" % project_identifier)

    deployKey_exists = gitlab_deploy_key.existsDeployKey(project, key_title)

    if state == 'absent':
        if deployKey_exists:
            gitlab_deploy_key.deleteDeployKey()
            module.exit_json(changed=True, msg="Successfully deleted deploy_key %s" % key_title)
        else:
            module.exit_json(changed=False, msg="Deploy_key deleted or does not exists")

    if state == 'present':
        if gitlab_deploy_key.createOrUpdateDeployKey(project, key_title, key_keyfile, {'can_push': key_can_push}):

            module.exit_json(changed=True, msg="Successfully created or updated the deploy_key %s" % key_title,
                             deploy_key=gitlab_deploy_key.deployKeyObject._attrs)
        else:
            module.exit_json(changed=False, msg="No need to update the deploy_key %s" % key_title,
                             deploy_key=gitlab_deploy_key.deployKeyObject._attrs)


if __name__ == '__main__':
    main()
