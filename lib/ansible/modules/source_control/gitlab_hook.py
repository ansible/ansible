#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
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
---
module: gitlab_hook
short_description: Manages GitLab project hooks.
description:
     - Adds, updates and removes project hook
version_added: "2.6"
author:
  - Marcus Watkins (@marwatk)
  - Guillaume Martinez (@Lunik)
requirements:
  - python >= 2.7
  - python-gitlab python module
extends_documentation_fragment:
    - auth_basic
options:
  api_token:
    description:
      - Gitlab token for logging in.
    version_added: "2.8"
    type: str
    aliases:
      - private_token
      - access_token
  project:
    description:
      - Id or Full path of the project in the form of group/name
    required: true
    type: str
  hook_url:
    description:
      - The url that you want GitLab to post to, this is used as the primary key for updates and deletion.
    required: true
    type: str
  state:
    description:
      - When C(present) the hook will be updated to match the input or created if it doesn't exist. When C(absent) it will be deleted if it exists.
    required: true
    default: present
    type: str
    choices: [ "present", "absent" ]
  push_events:
    description:
      - Trigger hook on push events
    type: bool
    default: yes
  issues_events:
    description:
      - Trigger hook on issues events
    type: bool
    default: no
  merge_requests_events:
    description:
      - Trigger hook on merge requests events
    type: bool
    default: no
  tag_push_events:
    description:
      - Trigger hook on tag push events
    type: bool
    default: no
  note_events:
    description:
      - Trigger hook on note events
    type: bool
    default: no
  job_events:
    description:
      - Trigger hook on job events
    type: bool
    default: no
  pipeline_events:
    description:
      - Trigger hook on pipeline events
    type: bool
    default: no
  wiki_page_events:
    description:
      - Trigger hook on wiki events
    type: bool
    default: no
  hook_validate_certs:
    description:
      - Whether GitLab will do SSL verification when triggering the hook
    type: bool
    default: no
    aliases: [ enable_ssl_verification ]
  token:
    description:
      - Secret token to validate hook messages at the receiver.
      - If this is present it will always result in a change as it cannot be retrieved from GitLab.
      - Will show up in the X-Gitlab-Token HTTP request header
    required: false
    type: str
'''

EXAMPLES = '''
- name: "Adding a project hook"
  gitlab_hook:
    api_url: https://gitlab.example.com/
    api_token: "{{ access_token }}"
    project: "my_group/my_project"
    hook_url: "https://my-ci-server.example.com/gitlab-hook"
    state: present
    push_events: yes
    tag_push_events: yes
    hook_validate_certs: no
    token: "my-super-secret-token-that-my-ci-server-will-check"

- name: "Delete the previous hook"
  gitlab_hook:
    api_url: https://gitlab.example.com/
    api_token: "{{ access_token }}"
    project: "my_group/my_project"
    hook_url: "https://my-ci-server.example.com/gitlab-hook"
    state: absent

- name: "Delete a hook by numeric project id"
  gitlab_hook:
    api_url: https://gitlab.example.com/
    api_token: "{{ access_token }}"
    project: 10
    hook_url: "https://my-ci-server.example.com/gitlab-hook"
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

hook:
  description: API object
  returned: always
  type: dict
'''

import os
import re
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

from ansible.module_utils.gitlab import findProject


class GitLabHook(object):
    def __init__(self, module, gitlab_instance):
        self._module = module
        self._gitlab = gitlab_instance
        self.hookObject = None

    '''
    @param prokect Project Object
    @param hook_url Url to call on event
    @param description Description of the group
    @param parent Parent group full path
    '''
    def createOrUpdateHook(self, project, hook_url, options):
        changed = False

        # Because we have already call userExists in main()
        if self.hookObject is None:
            hook = self.createHook(project, {
                'url': hook_url,
                'push_events': options['push_events'],
                'issues_events': options['issues_events'],
                'merge_requests_events': options['merge_requests_events'],
                'tag_push_events': options['tag_push_events'],
                'note_events': options['note_events'],
                'job_events': options['job_events'],
                'pipeline_events': options['pipeline_events'],
                'wiki_page_events': options['wiki_page_events'],
                'enable_ssl_verification': options['enable_ssl_verification'],
                'token': options['token']})
            changed = True
        else:
            changed, hook = self.updateHook(self.hookObject, {
                'push_events': options['push_events'],
                'issues_events': options['issues_events'],
                'merge_requests_events': options['merge_requests_events'],
                'tag_push_events': options['tag_push_events'],
                'note_events': options['note_events'],
                'job_events': options['job_events'],
                'pipeline_events': options['pipeline_events'],
                'wiki_page_events': options['wiki_page_events'],
                'enable_ssl_verification': options['enable_ssl_verification'],
                'token': options['token']})

        self.hookObject = hook
        if changed:
            if self._module.check_mode:
                self._module.exit_json(changed=True, msg="Successfully created or updated the hook %s" % hook_url)

            try:
                hook.save()
            except Exception as e:
                self._module.fail_json(msg="Failed to update hook: %s " % e)
            return True
        else:
            return False

    '''
    @param project Project Object
    @param arguments Attributs of the hook
    '''
    def createHook(self, project, arguments):
        if self._module.check_mode:
            return True

        hook = project.hooks.create(arguments)

        return hook

    '''
    @param hook Hook Object
    @param arguments Attributs of the hook
    '''
    def updateHook(self, hook, arguments):
        changed = False

        for arg_key, arg_value in arguments.items():
            if arguments[arg_key] is not None:
                if getattr(hook, arg_key) != arguments[arg_key]:
                    setattr(hook, arg_key, arguments[arg_key])
                    changed = True

        return (changed, hook)

    '''
    @param project Project object
    @param hook_url Url to call on event
    '''
    def findHook(self, project, hook_url):
        hooks = project.hooks.list()
        for hook in hooks:
            if (hook.url == hook_url):
                return hook

    '''
    @param project Project object
    @param hook_url Url to call on event
    '''
    def existsHook(self, project, hook_url):
        # When project exists, object will be stored in self.projectObject.
        hook = self.findHook(project, hook_url)
        if hook:
            self.hookObject = hook
            return True
        return False

    def deleteHook(self):
        if self._module.check_mode:
            return True

        return self.hookObject.delete()


def deprecation_warning(module):
    deprecated_aliases = ['private_token', 'access_token']

    module.deprecate("Aliases \'{aliases}\' are deprecated".format(aliases='\', \''.join(deprecated_aliases)), "2.10")


def main():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        api_token=dict(type='str', no_log=True, aliases=["private_token", "access_token"]),
        state=dict(type='str', default="present", choices=["absent", "present"]),
        project=dict(type='str', required=True),
        hook_url=dict(type='str', required=True),
        push_events=dict(type='bool', default=True),
        issues_events=dict(type='bool', default=False),
        merge_requests_events=dict(type='bool', default=False),
        tag_push_events=dict(type='bool', default=False),
        note_events=dict(type='bool', default=False),
        job_events=dict(type='bool', default=False),
        pipeline_events=dict(type='bool', default=False),
        wiki_page_events=dict(type='bool', default=False),
        hook_validate_certs=dict(type='bool', default=False, aliases=['enable_ssl_verification']),
        token=dict(type='str', no_log=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['api_username', 'api_token'],
            ['api_password', 'api_token']
        ],
        required_together=[
            ['api_username', 'api_password']
        ],
        required_one_of=[
            ['api_username', 'api_token']
        ],
        supports_check_mode=True,
    )

    deprecation_warning(module)

    gitlab_url = re.sub('/api.*', '', module.params['api_url'])
    validate_certs = module.params['validate_certs']
    gitlab_user = module.params['api_username']
    gitlab_password = module.params['api_password']
    gitlab_token = module.params['api_token']

    state = module.params['state']
    project_identifier = module.params['project']
    hook_url = module.params['hook_url']
    push_events = module.params['push_events']
    issues_events = module.params['issues_events']
    merge_requests_events = module.params['merge_requests_events']
    tag_push_events = module.params['tag_push_events']
    note_events = module.params['note_events']
    job_events = module.params['job_events']
    pipeline_events = module.params['pipeline_events']
    wiki_page_events = module.params['wiki_page_events']
    enable_ssl_verification = module.params['hook_validate_certs']
    hook_token = module.params['token']

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg=missing_required_lib("python-gitlab"), exception=GITLAB_IMP_ERR)

    try:
        gitlab_instance = gitlab.Gitlab(url=gitlab_url, ssl_verify=validate_certs, email=gitlab_user, password=gitlab_password,
                                        private_token=gitlab_token, api_version=4)
        gitlab_instance.auth()
    except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabGetError) as e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s" % to_native(e))
    except (gitlab.exceptions.GitlabHttpError) as e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s. \
            Gitlab remove Session API now that private tokens are removed from user API endpoints since version 10.2." % to_native(e))

    gitlab_hook = GitLabHook(module, gitlab_instance)

    project = findProject(gitlab_instance, project_identifier)

    if project is None:
        module.fail_json(msg="Failed to create hook: project %s doesn't exists" % project_identifier)

    hook_exists = gitlab_hook.existsHook(project, hook_url)

    if state == 'absent':
        if hook_exists:
            gitlab_hook.deleteHook()
            module.exit_json(changed=True, msg="Successfully deleted hook %s" % hook_url)
        else:
            module.exit_json(changed=False, msg="Hook deleted or does not exists")

    if state == 'present':
        if gitlab_hook.createOrUpdateHook(project, hook_url, {
                                          "push_events": push_events,
                                          "issues_events": issues_events,
                                          "merge_requests_events": merge_requests_events,
                                          "tag_push_events": tag_push_events,
                                          "note_events": note_events,
                                          "job_events": job_events,
                                          "pipeline_events": pipeline_events,
                                          "wiki_page_events": wiki_page_events,
                                          "enable_ssl_verification": enable_ssl_verification,
                                          "token": hook_token}):

            module.exit_json(changed=True, msg="Successfully created or updated the hook %s" % hook_url, hook=gitlab_hook.hookObject._attrs)
        else:
            module.exit_json(changed=False, msg="No need to update the hook %s" % hook_url, hook=gitlab_hook.hookObject._attrs)


if __name__ == '__main__':
    main()
