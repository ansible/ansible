#!/usr/bin/python
# (c) 2016, Werner Dijkerman (ikben@werner-dijkerman.nl)
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: gitlab_hook
short_description: Creates/updates/deletes hooks on Gitlab projects
description:
   - When the hook does not exists in Gitlab, it will be created.
   - When the hook does exists and state=absent, the hook will be deleted.
   - When changes are made to the hook, the hook will be updated.
   - The project and group should already exists when executing this module.
version_added: "2.3"
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
    group:
        description:
            - The name of the group of which the projects belongs to.
            - If the project belongs to a user, the username should be used for this.
        required: true
        default: null
    project:
        description:
            - The name of the project on which the hook needs to be added or updated.
        required: true
        default: null
    push_events:
        description:
            - Trigger hook on push events.
        required: false
        default: true
        choices: ["true", "false"]
    issues_events:
        description:
            - Trigger hook on issues events.
        required: false
        default: false
        choices: ["true", "false"]
    merge_requests_events:
        description:
            - Trigger hook on merge requests events.
        required: false
        default: false
        choices: ["true", "false"]
    tag_push_events:
        description:
            - Trigger hook on tag push events.
        required: false
        default: false
        choices: ["true", "false"]
    note_events:
        description:
            - Trigger hook on note events.
        required: false
        default: false
        choices: ["true", "false"]
    build_events:
        description:
            - Trigger hook on build events.
        required: false
        default: false
        choices: ["true", "false"]
    pipeline_events:
        description:
            - Trigger hook on pipeline events.
        required: false
        default: false
        choices: ["true", "false"]
    enable_ssl_verification:
        description:
            - Do SSL verification when triggering the hook.
        required: false
        default: false
        choices: ["true", "false"]
    state:
        description:
            - create or delete hooks.
        required: false
        default: "present"
        choices: ["present", "absent"]

'''

EXAMPLES = '''

- name: "Create hooks"
  local_action:
    module: gitlab_hook
    server_url="http://gitlab.dj-wasabi.local"
    validate_certs=false
    login_token="WnUzDsxjy8230-Dy_k"
    group: my_first_group
    project: my_first_project
    url: http://example.com:8080/fancy
    note_events: True
    pipeline_events: True
    enable_ssl_verification: True
    state: present

- name: "Delete hooks"
  local_action:
    module: gitlab_hook
    server_url="http://gitlab.dj-wasabi.local"
    validate_certs=false
    login_token="WnUzDsxjy8230-Dy_k"
    group: my_first_group
    project: my_first_project
    url: http://example.com:8080/fancy
    state: absent

'''

RETURN = '''# '''

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import *
from ansible.module_utils.pycompat24 import get_exception


class GitLabHook(object):
    def __init__(self, module, git):
        self._module = module
        self._gitlab = git
        self.projectObject = None
        self.hookObject = None

    def createOrUpdateHook(self, url, push_events, issues_events, note_events, merge_requests_events, tag_push_events,
                           build_events, enable_ssl_verification, pipeline_events):
        """Create a hook or let it update."""
        project = self.projectObject
        if self.hookObject is None:
            if self._module.check_mode:
                self._module.exit_json(changed=True, result="Hook should have been created.")
            project.hooks.create({
                'url': url,
                'push_events': push_events,
                'issues_events': issues_events,
                'note_events': note_events,
                'merge_requests_events': merge_requests_events,
                'tag_push_events': tag_push_events,
                'build_events': build_events,
                'pipeline_events': pipeline_events,
                'enable_ssl_verification': enable_ssl_verification
            })
            return True
        else:
            if self.updateHook(push_events, issues_events, note_events, merge_requests_events, tag_push_events,
                               build_events, enable_ssl_verification, pipeline_events):
                return True
            else:
                return False

    def updateHook(self, push_events, issues_events, note_events, merge_requests_events, tag_push_events,
                   build_events, enable_ssl_verification, pipeline_events):
        """Update a hook."""
        hook = self.hookObject
        changed = False

        if hook.push_events != push_events:
            hook.push_events = push_events
            changed = True
        if hook.issues_events != issues_events:
            hook.issues_events = issues_events
            changed = True
        if hook.note_events != note_events:
            hook.note_events = note_events
            changed = True
        if hook.merge_requests_events != merge_requests_events:
            hook.merge_requests_events = merge_requests_events
            changed = True
        if hook.tag_push_events != tag_push_events:
            hook.tag_push_events = tag_push_events
            changed = True
        if hook.build_events != build_events:
            hook.build_events = build_events
            changed = True
        if hook.enable_ssl_verification != enable_ssl_verification:
            hook.enable_ssl_verification = enable_ssl_verification
            changed = True
        if hook.pipeline_events != pipeline_events:
            hook.pipeline_events = pipeline_events
            # This is always changing, even if they both have the same values.
            # changed = True

        if changed:
            if self._module.check_mode:
                module.exit_json(changed=True, result="Hook should have been updated.")
            hook.save()
            return True
        else:
            return False

    def existsHook(self, url):
        """Check if a hook exists."""
        project = self.projectObject

        hooks = project.hooks.list()
        for hook in hooks:
            if hook.url == url:
                self.hookObject = hook
                return True
        return False

    def getProject(self, group, project):
        """Validates if a project exists."""
        project_name = project
        projects = self._gitlab.projects.search(project_name)
        if len(projects) >= 1:
            for project in projects:
                if project.namespace.name == group:
                    self.projectObject = project
                    return True
        return False

    def deleteHook(self):
        """Delete a hook"""
        hook = self.hookObject
        if hook.delete():
            return True
        else:
            return False

def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            validate_certs=dict(required=False, default=True, type='bool', aliases=['verify_ssl']),
            login_user=dict(required=False, no_log=True),
            login_password=dict(required=False, no_log=True),
            login_token=dict(required=False, no_log=True),
            group=dict(required=True),
            project=dict(required=True),
            url=dict(required=True),
            push_events=dict(default=True, type='bool'),
            pipeline_events=dict(default=True, type='bool'),
            issues_events=dict(default=False, type='bool'),
            note_events=dict(default=False, type='bool'),
            merge_requests_events=dict(default=False, type='bool'),
            tag_push_events=dict(default=False, type='bool'),
            build_events=dict(default=False, type='bool'),
            enable_ssl_verification=dict(default=True, type='bool'),
            state=dict(default="present", choices=["present", 'absent']),
        ),
        supports_check_mode=True
    )

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg="Missing required gitlab module (check docs or install with: pip install python-gitlab")

    server_url = module.params['server_url']
    verify_ssl = module.params['validate_certs']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
    project = module.params['project']
    group = module.params['group']
    hook_url = module.params['url']
    push_events = module.params['push_events']
    issues_events = module.params['issues_events']
    note_events = module.params['note_events']
    pipeline_events = module.params['pipeline_events']
    merge_requests_events = module.params['merge_requests_events']
    tag_push_events = module.params['tag_push_events']
    build_events = module.params['build_events']
    enable_ssl_verification = module.params['enable_ssl_verification']
    state = module.params['state']
    use_credentials = None

    # Validate some credentials configuration parameters.
    if login_user is not None and login_password is not None:
        use_credentials = True
    elif login_token is not None:
        use_credentials = False
    else:
        module.fail_json(msg="No login credentials are given. Use login_user with login_password, or login_token")

    if login_token and login_user:
        module.fail_json(msg="You can either use 'login_token' or 'login_user' and 'login_password'")

    try:
        if use_credentials:
            git = gitlab.Gitlab(server_url, email=login_user, password=login_password, ssl_verify=verify_ssl)
            git.auth()
        else:
            git = gitlab.Gitlab(server_url, private_token=login_token, ssl_verify=verify_ssl)
            git.auth()
    except Exception:
        e = get_exception()
        module.fail_json(msg="Failed to connect to Gitlab server: %s " % e)

    hook = GitLabHook(module, git)
    project = hook.getProject(group=group, project=project)
    if not project:
        module.fail_json(msg="The project or the group does not exists. We can not create a hook.")

    project_hook = hook.existsHook(url=hook_url)
    if project_hook:
        if state == "absent":
            if module.check_mode:
                module.exit_json(changed=True, result="Hook should have been deleted.")
            if hook.deleteHook():
                module.exit_json(changed=True, result="Hook is deleted.")
            else:
                module.exit_json(changed=False, result="Something went wrong with deleting the hook.")
        else:
            if hook.createOrUpdateHook(url=hook_url, push_events=push_events, issues_events=issues_events,
                                       note_events=note_events, merge_requests_events=merge_requests_events,
                                       tag_push_events=tag_push_events, pipeline_events=pipeline_events,
                                       build_events=build_events, enable_ssl_verification=enable_ssl_verification):
                module.exit_json(changed=True, result="Updated the hook")
            else:
                module.exit_json(changed=False, result="There was no need for updating the hook.")
    else:
        if state == "absent":
            module.exit_json(changed=False, result="Hook does not exists.")
        else:
            if hook.createOrUpdateHook(url=hook_url, push_events=push_events, issues_events=issues_events,
                                       note_events=note_events, merge_requests_events=merge_requests_events,
                                       tag_push_events=tag_push_events, pipeline_events=pipeline_events,
                                       build_events=build_events, enable_ssl_verification=enable_ssl_verification):
                module.exit_json(changed=True, result="Hook is been created.")
            else:
                module.exit_json(changed=False, result="Something went wrong creating hook.")

if __name__ == '__main__':
    main()
