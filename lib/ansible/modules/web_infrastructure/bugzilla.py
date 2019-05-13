#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Chuang Cao <chcao@redhat.com>
# Atlassian open-source approval reference OSR-76.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: bugzilla
version_added: "2.9"
short_description: modify bugs in a Bugzilla instance by xmlrpc
description:
  - Modifybugs in a Bugzilla instance.

options:
  uri:
    required: true
    description:
      - Base URI for the Bugzilla instance.

  operation:
    required: true
    aliases: [ command ]
    choices: [ comment, transition, fetch ]
    description:
      - The operation to perform.

  username:
    required: true
    description:
      - The username to log-in with.

  password:
    required: true
    description:
      - The password to log-in with.

  bug:
    required: false
    description:
     - An existing bug number to operate on.

  comment:
    required: false
    description:
     - The comment text to add.

  status:
    required: false
    description:
     - The desired status; only relevant for the transition operation.

  timeout:
    required: false
    description:
      - Set timeout, in seconds, on requests to Bugzilla API.
    default: 10

notes:
  - "Currently this only works with REST API."

author: "Chuang Cao (@cc)"
"""

EXAMPLES = """
# Add a comment to bug:
- name: Comment on bug
  bugzilla:
    uri: '{{ server }}'
    username: '{{ user }}'
    password: '{{ pass }}'
    bug: '{{ bug.id }}'
    operation: comment
    comment: A comment added by Ansible

# Retrieve metadata for an issue and use it to create an account
- name: Get an issue
  bugzilla:
    uri: '{{ server }}'
    username: '{{ user }}'
    password: '{{ pass }}'
    operation: fetch
    bug: 123456
  register: bug

# Transition an issue by target status
- name: Change bug's status to ON_QA
  bugzilla:
    uri: '{{ server }}'
    username: '{{ user }}'
    password: '{{ pass }}'
    bug: '{{ bug.id }}'
    operation: transition
    status: ON_QA
"""

RETURN = '''
bug:
    description: This is the is of bug
    type: str
    returned: always
'''

import base64
import json
import sys

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


# Handle request by ansible lib
def handle_request(url, timeout, data=None, method='GET'):
    data = json.dumps(data)
    response, info = fetch_url(module, url, data=data, method=method, timeout=timeout,
                               headers={'Content-Type': 'application/json'})
    if info['status'] not in (200, 201, 204):
        module.fail_json(msg=info['msg'])
    body = response.read()
    if body:
        return json.loads(body)
    else:
        return {}


def comment(restbase, user, passwd, params):
    data = {
        'comment': params['comment'],
        'Bugzilla_login': user,
        'Bugzilla_password': passwd,
    }
    url = restbase + '/bug/' + params['bug'] + '/comment'
    ret = handle_request(url, params['timeout'], data, 'POST')
    return ret


def fetch(restbase, user, passwd, params):
    url = restbase + '/bug/' + params['bug'] + "?Bugzilla_login=" + user + "&Bugzilla_password=" + passwd
    ret = handle_request(url, params['timeout'])
    return ret


def transition(restbase, user, passwd, params):
    data = {
        'status': params['status'],
        'Bugzilla_login': user,
        'Bugzilla_password': passwd,
    }
    url = restbase + '/bug/' + params['bug']
    ret = handle_request(url, params['timeout'], data, 'PUT')
    return ret


# Some parameters are required depending on the operation:
OP_REQUIRED = dict(comment=['bug', 'comment'],
                   fetch=['bug'],
                   transition=['bug', 'status'])


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            uri=dict(required=True),
            operation=dict(choices=['comment', 'fetch', 'transition'],
                           aliases=['command'], required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            comment=dict(),
            status=dict(),
            bug=dict(),
            timeout=dict(type='float', default=10),
        ),
        supports_check_mode=False
    )

    op = module.params['operation']

    # Check we have the necessary per-operation parameters
    missing = []
    for parm in OP_REQUIRED[op]:
        if not module.params[parm]:
            missing.append(parm)
    if missing:
        module.fail_json(msg="Operation %s require the following missing parameters: %s" % (op, ",".join(missing)))

    uri = module.params['uri']
    user = module.params['username']
    passwd = module.params['password']

    if not uri.endswith('/'):
        uri = uri + '/'
    restbase = uri + 'rest'

    try:
        # Lookup the corresponding method for this operation.
        thismod = sys.modules[__name__]
        method = getattr(thismod, op)

        ret = method(restbase, user, passwd, module.params)

    except Exception as e:
        return module.fail_json(msg=e.message)

    module.exit_json(changed=True, meta=ret)


if __name__ == '__main__':
    main()
