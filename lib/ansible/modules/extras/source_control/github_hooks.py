#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Phillip Gentry <phillip@cx.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import json
import base64

DOCUMENTATION = '''
---
module: github_hooks
short_description: Manages github service hooks.
description:
     - Adds service hooks and removes service hooks that have an error status.
version_added: "1.4"
options:
  user:
    description:
      - Github username.
    required: true
  oauthkey:
    description:
      - The oauth key provided by github. It can be found/generated on github under "Edit Your Profile" >> "Applications" >> "Personal Access Tokens"
    required: true
  repo:
    description:
      - "This is the API url for the repository you want to manage hooks for. It should be in the form of: https://api.github.com/repos/user:/repo:. Note this is different than the normal repo url."
    required: true
  hookurl:
    description:
      - When creating a new hook, this is the url that you want github to post to. It is only required when creating a new hook.
    required: false
  action:
    description:
      - This tells the githooks module what you want it to do.
    required: true
    choices: [ "create", "cleanall" ]
  validate_certs:
    description:
      - If C(no), SSL certificates for the target repo will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices: ['yes', 'no']
  content_type:
    description:
      - Content type to use for requests made to the webhook
    required: false
    default: 'json'
    choices: ['json', 'form']

author: Phillip Gentry, CX Inc
'''

EXAMPLES = '''
# Example creating a new service hook. It ignores duplicates.
- github_hooks: action=create hookurl=http://11.111.111.111:2222 user={{ gituser }} oauthkey={{ oauthkey }} repo=https://api.github.com/repos/pcgentry/Github-Auto-Deploy

# Cleaning all hooks for this repo that had an error on the last update. Since this works for all hooks in a repo it is probably best that this would be called from a handler.
- local_action: github_hooks action=cleanall user={{ gituser }} oauthkey={{ oauthkey }} repo={{ repo }}
'''

def _list(module, hookurl, oauthkey, repo, user):
    url = "%s/hooks" % repo
    auth = base64.encodestring('%s:%s' % (user, oauthkey)).replace('\n', '')
    headers = {
        'Authorization': 'Basic %s' % auth,
    }
    response, info = fetch_url(module, url, headers=headers)
    if info['status'] != 200:
        return False, ''
    else:
        return False, response.read()

def _clean504(module, hookurl, oauthkey, repo, user):
    current_hooks = _list(hookurl, oauthkey, repo, user)[1]
    decoded = json.loads(current_hooks)

    for hook in decoded:
        if hook['last_response']['code'] == 504:
            # print "Last response was an ERROR for hook:"
            # print hook['id']
            _delete(module, hookurl, oauthkey, repo, user, hook['id'])
            
    return 0, current_hooks

def _cleanall(module, hookurl, oauthkey, repo, user):
    current_hooks = _list(hookurl, oauthkey, repo, user)[1]
    decoded = json.loads(current_hooks)

    for hook in decoded:
        if hook['last_response']['code'] != 200:
            # print "Last response was an ERROR for hook:"
            # print hook['id']
            _delete(module, hookurl, oauthkey, repo, user, hook['id'])
            
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
    auth = base64.encodestring('%s:%s' % (user, oauthkey)).replace('\n', '')
    headers = {
        'Authorization': 'Basic %s' % auth,
    }
    response, info = fetch_url(module, url, data=data, headers=headers)
    if info['status'] != 200:
        return 0, '[]'
    else:
        return 0, response.read()

def _delete(module, hookurl, oauthkey, repo, user, hookid):
    url = "%s/hooks/%s" % (repo, hookid)
    auth = base64.encodestring('%s:%s' % (user, oauthkey)).replace('\n', '')
    headers = {
        'Authorization': 'Basic %s' % auth,
    }
    response, info = fetch_url(module, url, data=data, headers=headers, method='DELETE')
    return response.read()

def main():
    module = AnsibleModule(
        argument_spec=dict(
        action=dict(required=True),
        hookurl=dict(required=False),
        oauthkey=dict(required=True),
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
        (rc, out) = _list(module, hookurl, oauthkey, repo, user)

    if action == "clean504":
        (rc, out) = _clean504(module, hookurl, oauthkey, repo, user)

    if action == "cleanall":
        (rc, out) = _cleanall(module, hookurl, oauthkey, repo, user)

    if action == "create":
        (rc, out) = _create(module, hookurl, oauthkey, repo, user, content_type)

    if rc != 0:
        module.fail_json(msg="failed", result=out)

    module.exit_json(msg="success", result=out)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()
