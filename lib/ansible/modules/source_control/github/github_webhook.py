#!/usr/bin/python
#
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: github_webhook
short_description: Manage GitHub webhooks
version_added: "2.8"
description:
  - "Create and delete GitHub webhooks"
requirements:
  - "PyGithub >= 1.3.5"
options:
  repository:
    description:
      - Full name of the repository to configure a hook for
    required: true
    aliases:
      - repo
  url:
    description:
      - URL to which payloads will be delivered
    required: true
  content_type:
    description:
      - The media type used to serialize the payloads
    required: false
    choices: [ form, json ]
    default: form
  secret:
    description:
      - The shared secret between GitHub and the payload URL.
    required: false
  insecure_ssl:
    description:
      - >
        Flag to indicate that GitHub should skip SSL verification when calling
        the hook.
    required: false
    type: bool
    default: false
  events:
    description:
      - >
        A list of GitHub events the hook is triggered for. Events are listed at
        U(https://developer.github.com/v3/activity/events/types/). Required
        unless C(state) is C(absent)
    required: false
  active:
    description:
      - Whether or not the hook is active
    required: false
    type: bool
    default: true
  state:
    description:
      - Whether the hook should be present or absent
    required: false
    choices: [ absent, present ]
    default: present
  user:
    description:
      - User to authenticate to GitHub as
    required: true
  password:
    description:
      - Password to authenticate to GitHub with
    required: false
  token:
    description:
      - Token to authenticate to GitHub with
    required: false
  github_url:
    description:
      - Base URL of the GitHub API
    required: false
    default: https://api.github.com

author:
  - "Chris St. Pierre (@stpierre)"
'''

EXAMPLES = '''
- name:  create a new webhook that triggers on push (password auth)
  github_webhook:
    repository: ansible/ansible
    url: https://www.example.com/hooks/
    events:
      - push
    user: "{{ github_user }}"
    password: "{{ github_password }}"

- name: create a new webhook in a github enterprise installation with multiple event triggers (token auth)
  github_webhook:
    repository: myorg/myrepo
    url: https://jenkins.example.com/ghprbhook/
    content_type: json
    secret: "{{ github_shared_secret }}"
    insecure_ssl: True
    events:
      - issue_comment
      - pull_request
    user: "{{ github_user }}"
    token: "{{ github_user_api_token }}"
    github_url: https://github.example.com

- name: delete a webhook (password auth)
  github_webhook:
    repository: ansible/ansible
    url: https://www.example.com/hooks/
    state: absent
    user: "{{ github_user }}"
    password: "{{ github_password }}"
'''

RETURN = '''
---
hook_id:
  description: The GitHub ID of the hook created/updated
  returned: when state is 'present'
  type: int
  sample: 6206
'''

import traceback

GITHUB_IMP_ERR = None
try:
    import github
    HAS_GITHUB = True
except ImportError:
    GITHUB_IMP_ERR = traceback.format_exc()
    HAS_GITHUB = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native


def _create_hook_config(module):
    return {
        "url": module.params["url"],
        "content_type": module.params["content_type"],
        "secret": module.params.get("secret"),
        "insecure_ssl": "1" if module.params["insecure_ssl"] else "0"
    }


def create_hook(repo, module):
    config = _create_hook_config(module)
    try:
        hook = repo.create_hook(
            name="web",
            config=config,
            events=module.params["events"],
            active=module.params["active"])
    except github.GithubException as err:
        module.fail_json(msg="Unable to create hook for repository %s: %s" % (
            repo.full_name, to_native(err)))

    data = {"hook_id": hook.id}
    return True, data


def update_hook(repo, hook, module):
    config = _create_hook_config(module)
    try:
        hook.update()
        hook.edit(
            name="web",
            config=config,
            events=module.params["events"],
            active=module.params["active"])

        changed = hook.update()
    except github.GithubException as err:
        module.fail_json(msg="Unable to modify hook for repository %s: %s" % (
            repo.full_name, to_native(err)))

    data = {"hook_id": hook.id}
    return changed, data


def main():
    module = AnsibleModule(
        argument_spec=dict(
            repository=dict(type='str', required=True, aliases=['repo']),
            url=dict(type='str', required=True),
            content_type=dict(
                type='str',
                choices=('json', 'form'),
                required=False,
                default='form'),
            secret=dict(type='str', required=False, no_log=True),
            insecure_ssl=dict(type='bool', required=False, default=False),
            events=dict(type='list', elements='str', required=False),
            active=dict(type='bool', required=False, default=True),
            state=dict(
                type='str',
                required=False,
                choices=('absent', 'present'),
                default='present'),
            user=dict(type='str', required=True),
            password=dict(type='str', required=False, no_log=True),
            token=dict(type='str', required=False, no_log=True),
            github_url=dict(
                type='str', required=False, default="https://api.github.com")),
        mutually_exclusive=(('password', 'token'),),
        required_one_of=(("password", "token"),),
        required_if=(("state", "present", ("events",)),),
    )

    if not HAS_GITHUB:
        module.fail_json(msg=missing_required_lib('PyGithub'),
                         exception=GITHUB_IMP_ERR)

    try:
        github_conn = github.Github(
            module.params["user"],
            module.params.get("password") or module.params.get("token"),
            base_url=module.params["github_url"])
    except github.GithubException as err:
        module.fail_json(msg="Could not connect to GitHub at %s: %s" % (
            module.params["github_url"], to_native(err)))

    try:
        repo = github_conn.get_repo(module.params["repository"])
    except github.BadCredentialsException as err:
        module.fail_json(msg="Could not authenticate to GitHub at %s: %s" % (
            module.params["github_url"], to_native(err)))
    except github.UnknownObjectException as err:
        module.fail_json(
            msg="Could not find repository %s in GitHub at %s: %s" % (
                module.params["repository"], module.params["github_url"],
                to_native(err)))
    except Exception as err:
        module.fail_json(
            msg="Could not fetch repository %s from GitHub at %s: %s" %
            (module.params["repository"], module.params["github_url"],
             to_native(err)),
            exception=traceback.format_exc())

    hook = None
    try:
        for hook in repo.get_hooks():
            if hook.config.get("url") == module.params["url"]:
                break
        else:
            hook = None
    except github.GithubException as err:
        module.fail_json(msg="Unable to get hooks from repository %s: %s" % (
            module.params["repository"], to_native(err)))

    changed = False
    data = {}
    if hook is None and module.params["state"] == "present":
        changed, data = create_hook(repo, module)
    elif hook is not None and module.params["state"] == "absent":
        try:
            hook.delete()
        except github.GithubException as err:
            module.fail_json(
                msg="Unable to delete hook from repository %s: %s" % (
                    repo.full_name, to_native(err)))
        else:
            changed = True
    elif hook is not None and module.params["state"] == "present":
        changed, data = update_hook(repo, hook, module)
    # else, there is no hook and we want there to be no hook

    module.exit_json(changed=changed, **data)


if __name__ == '__main__':
    main()
