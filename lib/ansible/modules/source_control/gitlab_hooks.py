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
module: gitlab_hooks
short_description: Manages GitLab project hooks.
description:
     - Adds, updates and removes project hooks
version_added: "2.6"
options:
  server_url:
    description:
      - Url of Gitlab server, with protocol (http or https).
    required: true
    version_added: "2.8"
  verify_ssl:
    description:
      - When using https if SSL certificate needs to be verified.
    type: bool
    default: 'yes'
    aliases:
      - validate_certs
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
  project:
    description:
      - Full path of the project in the form of group/name
    required: true
  hook_url:
    description:
      - The url that you want GitLab to post to, this is used as the primary key for updates and deletion.
    required: true
  state:
    description:
      - When C(present) the hook will be updated to match the input or created if it doesn't exist. When C(absent) it will be deleted if it exists.
    required: true
    default: present
    choices: [ "present", "absent" ]
  push_events:
    description:
      - Trigger hook on push events
    type: bool
    default: 'yes'
  issues_events:
    description:
      - Trigger hook on issues events
    type: bool
    default: 'no'
  merge_requests_events:
    description:
      - Trigger hook on merge requests events
    type: bool
    default: 'no'
  tag_push_events:
    description:
      - Trigger hook on tag push events
    type: bool
    default: 'no'
  note_events:
    description:
      - Trigger hook on note events
    type: bool
    default: 'no'
  job_events:
    description:
      - Trigger hook on job events
    type: bool
    default: 'no'
  pipeline_events:
    description:
      - Trigger hook on pipeline events
    type: bool
    default: 'no'
  wiki_page_events:
    description:
      - Trigger hook on wiki events
    type: bool
    default: 'no'
  enable_ssl_verification:
    description:
      - Whether GitLab will do SSL verification when triggering the hook
    type: bool
    default: 'no'
  token:
    description:
      - Secret token to validate hook messages at the receiver.
      - If this is present it will always result in a change as it cannot be retrieved from GitLab.
      - Will show up in the X-Gitlab-Token HTTP request header
    required: false
author: "Marcus Watkins (@marwatk)"
'''

EXAMPLES = '''
- gitlab_hooks:
    server_url: https://gitlab.example.com
    login_token: "{{ access_token }}"
    project: "my_group/my_project"
    hook_url: "https://my-ci-server.example.com/gitlab-hook"
    state: present
    push_events: yes
    tag_push_events: yes
    enable_ssl_verification: no
    token: "my-super-secret-token-that-my-ci-server-will-check"
# Delete the previous hook
- gitlab_hooks:
    server_url: https://gitlab.example.com
    login_token: "{{ access_token }}"
    project: "my_group/my_project"
    hook_url: "https://my-ci-server.example.com/gitlab-hook"
    state: absent
# Delete a hook by numeric project id
- gitlab_hooks:
    server_url: https://gitlab.example.com
    login_token: "{{ access_token }}"
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

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except Exception:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


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
                self._module.exit_json(changed=True, result="Hook should have updated.")

            try:
                hook.save()
            except Exception as e:
                self._module.fail_json(msg="Failed to create or update a hook: %s " % e)
            return True
        else:
            return False

    '''
    @param project Project Object
    @param arguments Attributs of the hook
    '''
    def createHook(self, project, arguments):
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
    def existsHooks(self, project, hook_url):
        # When project exists, object will be stored in self.projectObject.
        hook = self.findHook(project, hook_url)
        if hook:
            self.hookObject = hook
            return True
        return False

    '''
    @param name Name of the project
    @param full_path Full path of the project
    '''
    def findProject(self, name, full_path):
        projects = self._gitlab.projects.list(search=name, as_list=False)
        for project in projects:
            if (project.path_with_namespace == full_path):
                return self._gitlab.projects.get(project.id)

    def deleteHook(self):
        self.hookObject.delete()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            verify_ssl=dict(required=False, default=True, type='bool', aliases=['validate_certs']),
            login_user=dict(required=False, no_log=True),
            login_password=dict(required=False, no_log=True),
            login_token=dict(required=False, no_log=True),
            state=dict(default="present", choices=["present", 'absent']),
            project=dict(required=True),
            hook_url=dict(required=True),
            push_events=dict(default=True, type='bool'),
            issues_events=dict(default=False, type='bool'),
            merge_requests_events=dict(default=False, type='bool'),
            tag_push_events=dict(default=False, type='bool'),
            note_events=dict(default=False, type='bool'),
            job_events=dict(default=False, type='bool'),
            pipeline_events=dict(default=False, type='bool'),
            wiki_page_events=dict(default=False, type='bool'),
            enable_ssl_verification=dict(default=False, type='bool'),
            token=dict(required=False, no_log=True)
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
    project_path = module.params['project']
    hook_url = module.params['hook_url']
    push_events = module.params['push_events']
    issues_events = module.params['issues_events']
    merge_requests_events = module.params['merge_requests_events']
    tag_push_events = module.params['tag_push_events']
    note_events = module.params['note_events']
    job_events = module.params['job_events']
    pipeline_events = module.params['pipeline_events']
    wiki_page_events = module.params['wiki_page_events']
    enable_ssl_verification = module.params['enable_ssl_verification']
    hook_token = module.params['token']

    project_name = project_path.split('/').pop()

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
            Gitlab remove Session API now that private tokens are removed from user API endpoints since version 10.2." % to_native(e))

    gitlab_hook = GitLabHook(module, gitlab_instance)

    project = gitlab_hook.findProject(project_name, project_path)

    if project is None:
        module.fail_json(msg="Failed to create hook: project %s doesn't exists" % project_path)

    hook_exists = gitlab_hook.existsHooks(project, hook_url)

    if state == 'absent':
        if hook_exists:
            gitlab_hook.deleteHook()
            module.exit_json(changed=True, result="Successfully deleted hook %s" % hook_url)
        else:
            module.exit_json(changed=False, result="Hook deleted or does not exists")

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

            module.exit_json(changed=True, result="Successfully created or updated the hook %s" % hook_url, hook=gitlab_hook.hookObject._attrs)
        else:
            module.exit_json(changed=False, result="No need to update the hook %s" % hook_url, hook=gitlab_hook.hookObject._attrs)


if __name__ == '__main__':
    main()
