#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Phillip Gentry <phillip@cx.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: github_hooks
short_description: Manages GitHub service hooks.
deprecated:
  removed_in: "2.12"
  why: Replaced by more granular modules
  alternative: Use M(github_webhook) and M(github_webhook_info) instead.
description:
     - Adds service hooks and removes service hooks that have an error status.
version_added: "1.4"
options:
  user:
    description:
      - GitHub username.
    required: true
  oauthkey:
    description:
      - The oauth key provided by GitHub. It can be found/generated on GitHub under "Edit Your Profile" >> "Developer settings" >> "Personal Access Tokens"
    required: true
  repo:
    description:
      - >
        This is the API url for the repository you want to manage hooks for. It should be in the form of: https://api.github.com/repos/user:/repo:.
        Note this is different than the normal repo url.
    required: true
  hookurl:
    description:
      - When creating a new hook, this is the url that you want GitHub to post to. It is only required when creating a new hook.
    required: false
  action:
    description:
      - This tells the githooks module what you want it to do.
    required: true
    choices: [ "create", "cleanall", "list", "clean504" ]
  validate_certs:
    description:
      - If C(no), SSL certificates for the target repo will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    type: bool
  content_type:
    description:
      - Content type to use for requests made to the webhook
    required: false
    default: 'json'
    choices: ['json', 'form']

author: "Phillip Gentry, CX Inc (@pcgentry)"
'''

EXAMPLES = '''
# Example creating a new service hook. It ignores duplicates.
- github_hooks:
    action: create
    hookurl: http://11.111.111.111:2222
    user: '{{ gituser }}'
    oauthkey: '{{ oauthkey }}'
    repo: https://api.github.com/repos/pcgentry/Github-Auto-Deploy

# Cleaning all hooks for this repo that had an error on the last update. Since this works for all hooks in a repo it is probably best that this would
# be called from a handler.
- github_hooks:
    action: cleanall
    user: '{{ gituser }}'
    oauthkey: '{{ oauthkey }}'
    repo: '{{ repo }}'
  delegate_to: localhost
'''

import json
import base64

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_bytes


def request(module, url, user, oauthkey, data='', method='GET'):
    auth = base64.b64encode(to_bytes('%s:%s' % (user, oauthkey)).replace('\n', ''))
    headers = {
        'Authorization': 'Basic %s' % auth,
    }
    response, info = fetch_url(module, url, headers=headers, data=data, method=method)
    return response, info


def _list(module, oauthkey, repo, user):
    url = "%s/hooks" % repo
    response, info = request(module, url, user, oauthkey)
    if info['status'] != 200:
        return False, ''
    else:
        return False, response.read()


def _clean504(module, oauthkey, repo, user):
    current_hooks = _list(module, oauthkey, repo, user)[1]
    decoded = json.loads(current_hooks)

    for hook in decoded:
        if hook['last_response']['code'] == 504:
            _delete(module, oauthkey, repo, user, hook['id'])

    return 0, current_hooks


def _cleanall(module, oauthkey, repo, user):
    current_hooks = _list(module, oauthkey, repo, user)[1]
    decoded = json.loads(current_hooks)

    for hook in decoded:
        if hook['last_response']['code'] != 200:
            _delete(module, oauthkey, repo, user, hook['id'])

    return 0, current_hooks


def _create(module, hookurl, oauthkey, repo, user, content_type):
    url = "%s/hooks" % repo
    values = {
        "active": True,
        "name": "web",
        "config": {
            "url": "%s" % hookurl,
            "content_type": "%s" % content_type
        }
    }
    data = json.dumps(values)
    response, info = request(module, url, user, oauthkey, data=data, method='POST')
    if info['status'] != 200:
        return 0, '[]'
    else:
        return 0, response.read()


def _delete(module, oauthkey, repo, user, hookid):
    url = "%s/hooks/%s" % (repo, hookid)
    response, info = request(module, url, user, oauthkey, method='DELETE')
    return response.read()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True, choices=['list', 'clean504', 'cleanall', 'create']),
            hookurl=dict(required=False),
            oauthkey=dict(required=True, no_log=True),
            repo=dict(required=True),
            user=dict(required=True),
            validate_certs=dict(default='yes', type='bool'),
            content_type=dict(default='json', choices=['json', 'form']),
        )
    )

    action = module.params['action']
    hookurl = module.params['hookurl']
    oauthkey = module.params['oauthkey']
    repo = module.params['repo']
    user = module.params['user']
    content_type = module.params['content_type']

    if action == "list":
        (rc, out) = _list(module, oauthkey, repo, user)

    if action == "clean504":
        (rc, out) = _clean504(module, oauthkey, repo, user)

    if action == "cleanall":
        (rc, out) = _cleanall(module, oauthkey, repo, user)

    if action == "create":
        (rc, out) = _create(module, hookurl, oauthkey, repo, user, content_type)

    if rc != 0:
        module.fail_json(msg="failed", result=out)

    module.exit_json(msg="success", result=out)


if __name__ == '__main__':
    main()
