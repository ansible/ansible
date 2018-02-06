#!/usr/bin/python
#
# Copyright: (c) Ansible Project
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
short_description: Manage Github webhooks
version_added: "2.5"
description:
  - "Create and delete Github webhooks"
requirements:
  - "PyGithub >= 1.3.5"
options:
  repository:
    description:
      - Full name of the repository to configure a hook for
    required: true
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
      - The shared secret between Github and the payload URL.
    required: false
  insecure_ssl:
    description:
      - Skip SSL verification
    required: false
    default: false
  events:
    description:
      - >
        A list of Github events the hook is triggered for. Events are listed at
        U(https://developer.github.com/v3/activity/events/types/). Required
        unless C(state) is C(absent)
    required: false
  active:
    description:
      - Whether or not the hook is active
    required: false
    default: true
  state:
    description:
      - Whether the hook should be present or absent
    required: false
    choices: [ absent, present ]
    default: present
  user:
    description:
      - User to authenticate to Github as
    required: true
  password:
    description:
      - Password to authenticate to Github with
    required: false
  token:
    description:
      - Token to authenticate to Github with
    required: false
  github_url:
    description:
      - Base URL of the github api
    required: false
    default: https://api.github.com

author:
  - "Chris St. Pierre (@stpierre)"
'''

EXAMPLES = '''
# create a new webhook that triggers on push (password auth)
- github_webhook:
    repository: ansible/ansible
    url: https://www.example.com/hooks/
    events:
      - push
    user: "{{ github_user }}"
    password: "{{ github_password }}"

# create a new webhook in a github enterprise installation with
# multiple event triggers (token auth)
- github_webhook:
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

# delete a webhook (password auth)
- github_webhook:
    repository: ansible/ansible
    url: https://www.example.com/hooks/
    state: absent
    user: "{{ github_user }}"
    password: "{{ github_password }}"
'''

RETURN = '''
---
hook_id:
  description: The Github ID of the hook created/updated
  returned: when state is 'present'
  type: int
  sample: 6206
'''

import traceback

try:
    import github
    HAS_GITHUB = True
except ImportError:
    HAS_GITHUB = False

from ansible.module_utils.basic import AnsibleModule
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
    hook = repo.create_hook(
        name="web",
        config=config,
        events=module.params["events"],
        active=module.params["active"])

    data = {"hook_id": hook.id}
    return True, data


def update_hook(repo, hook, module):
    config = _create_hook_config(module)
    hook.update()
    hook.edit(
        name="web",
        config=config,
        events=module.params["events"],
        active=module.params["active"])

    changed = hook.update()
    data = {"hook_id": hook.id}
    return changed, data


def main():
    module = AnsibleModule(
        argument_spec=dict(
            repository=dict(type='str', required=True),
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
        mutually_exclusive=(('password', 'token'), ))

    if not HAS_GITHUB:
        module.fail_json(msg="PyGithub required for this module")

    if not module.params.get("password") and not module.params.get("token"):
        module.fail_json(msg="You must specify either 'password' or 'token'")

    if module.params["state"] == "present" and not module.params.get("events"):
        module.fail_json(msg="'events' is required when state is 'present'")

    github_conn = github.Github(
        module.params["user"],
        module.params.get("password") or module.params.get("token"),
        base_url=module.params["github_url"])

    repo = github_conn.get_repo(module.params["repository"])
    hook = None
    try:
        for hook in repo.get_hooks():
            if hook.url == module.params["url"]:
                break
    except github.GithubException as err:
        module.fail_json(
            msg="Unable to get hooks from repository %s: %s" % to_native(err),
            exception=traceback.format_exc())

    changed = False
    data = {}
    if hook is None and module.params["state"] == "present":
        changed, data = create_hook(repo, module)
    elif hook is not None and module.params["state"] == "absent":
        hook.delete()
        changed = True
    elif hook is not None and module.params["state"] == "present":
        changed, data = update_hook(repo, hook, module)
    # else, there is no hook and we want there to be no hook

    module.exit_json(changed=changed, **data)


if __name__ == '__main__':
    main()
