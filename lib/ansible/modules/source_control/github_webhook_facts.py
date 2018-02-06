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
module: github_webhook_facts
short_description: Query information about Github webhooks
version_added: "2.5"
description:
  - "Query information about Github webhooks"
requirements:
  - "PyGithub >= 1.3.5"
options:
  repository:
    description:
      - Full name of the repository to configure a hook for
    required: true
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
# list hooks for a repository (password auth)
github_webhook_facts:
  repository: ansible/ansible
  user: "{{ github_user }}"
  password: "{{ github_password }}"
register: ansible_webhooks

# list hooks for a repository on github enterprise (token auth)
github_webhook_facts:
  repository: myorg/myrepo
  user: "{{ github_user }}"
  token: "{{ github_user_api_token }}"
  github_url: https://github.example.com/api/v3/
register: myrepo_webhooks
'''

RETURN = '''
---
hooks:
  description: A list of hooks that exist for the repo
  returned: always
  type: list
  sample: >
    [{"has_shared_secret": true,
      "url": "https://jenkins.example.com/ghprbhook/",
      "events": ["issue_comment", "pull_request"],
      "insecure_ssl": "1",
      "content_type": "json",
      "active": true,
      "id": 6206,
      "last_response": {"status": "active", "message": "OK", "code": 200}}]
'''

import traceback

try:
    import github
    HAS_GITHUB = True
except ImportError:
    HAS_GITHUB = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def _munge_hook(hook_obj):
    retval = {
        "active": hook_obj.active,
        "events": hook_obj.events,
        "id": hook_obj.id,
        "url": hook_obj.url,
    }
    retval.update(hook_obj.config)
    retval["has_shared_secret"] = "secret" in retval
    if "secret" in retval:
        del retval["secret"]

    retval["last_response"] = hook_obj.last_response.raw_data
    return retval


def main():
    module = AnsibleModule(
        argument_spec=dict(
            repository=dict(type='str', required=True),
            user=dict(type='str', required=True),
            password=dict(type='str', required=False, no_log=True),
            token=dict(type='str', required=False, no_log=True),
            github_url=dict(
                type='str', required=False, default="https://api.github.com")),
        mutually_exclusive=(('password', 'token'), ),
        supports_check_mode=True)

    if not HAS_GITHUB:
        module.fail_json(msg="PyGithub required for this module")

    if not module.params.get("password") and not module.params.get("token"):
        module.fail_json(msg="You must specify either 'password' or 'token'")

    github_conn = github.Github(
        module.params["user"],
        module.params.get("password") or module.params.get("token"),
        base_url=module.params["github_url"])

    repo = github_conn.get_repo(module.params["repository"])
    try:
        hooks = [_munge_hook(h) for h in repo.get_hooks()]
    except github.GithubException as err:
        module.fail_json(
            msg="Unable to get hooks from repository %s: %s" % to_native(err),
            exception=traceback.format_exc())

    module.exit_json(changed=False, hooks=hooks)


if __name__ == '__main__':
    main()
