#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Steve Smith <ssmith@atlassian.com>
# Atlassian open-source approval reference OSR-76.
#
# This file is part of Ansible.
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
#

DOCUMENTATION = """
module: jira
version_added: "1.6"
short_description: create and modify issues in a JIRA instance
description:
  - Create and modify issues in a JIRA instance.

options:
  uri:
    required: true
    description:
      - Base URI for the JIRA instance

  operation:
    required: true
    aliases: [ command ]
    choices: [ create, comment, edit, fetch, transition ]
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

  project:
    aliases: [ prj ]
    required: false
    description:
      - The project for this operation. Required for issue creation.

  summary:
    required: false
    description:
     - The issue summary, where appropriate.

  description:
    required: false
    description:
     - The issue description, where appropriate.

  issuetype:
    required: false
    description:
     - The issue type, for issue creation.

  issue:
    required: false
    description:
     - An existing issue key to operate on.

  comment:
    required: false
    description:
     - The comment text to add.

  status:
    required: false
    description:
     - The desired status; only relevant for the transition operation.

  assignee:
    required: false
    description:
     - Sets the assignee on create or transition operations. Note not all transitions will allow this.

  fields:
    required: false
    description:
     - This is a free-form data structure that can contain arbitrary data. This is passed directly to the JIRA REST API (possibly after merging with other required data, as when passed to create). See examples for more information, and the JIRA REST API for the structure required for various fields.

notes:
  - "Currently this only works with basic-auth."

author: "Steve Smith (@tarka)"
"""

EXAMPLES = """
# Create a new issue and add a comment to it:
- name: Create an issue
  jira: uri={{server}} username={{user}} password={{pass}}
        project=ANS operation=create
        summary="Example Issue" description="Created using Ansible" issuetype=Task
  register: issue

- name: Comment on issue
  jira: uri={{server}} username={{user}} password={{pass}}
        issue={{issue.meta.key}} operation=comment 
        comment="A comment added by Ansible"

# Assign an existing issue using edit
- name: Assign an issue using free-form fields
  jira: uri={{server}} username={{user}} password={{pass}}
        issue={{issue.meta.key}} operation=edit
        assignee=ssmith

# Create an issue with an existing assignee
- name: Create an assigned issue
  jira: uri={{server}} username={{user}} password={{pass}}
        project=ANS operation=create
        summary="Assigned issue" description="Created and assigned using Ansible" 
        issuetype=Task assignee=ssmith

# Edit an issue using free-form fields
- name: Set the labels on an issue using free-form fields
  jira: uri={{server}} username={{user}} password={{pass}}
        issue={{issue.meta.key}} operation=edit 
  args: { fields: {labels: ["autocreated", "ansible"]}}

- name: Set the labels on an issue, YAML version
  jira: uri={{server}} username={{user}} password={{pass}}
        issue={{issue.meta.key}} operation=edit 
  args: 
    fields: 
      labels:
        - "autocreated"
        - "ansible"
        - "yaml"

# Retrieve metadata for an issue and use it to create an account
- name: Get an issue
  jira: uri={{server}} username={{user}} password={{pass}}
        project=ANS operation=fetch issue="ANS-63"
  register: issue

- name: Create a unix account for the reporter
  sudo: true
  user: name="{{issue.meta.fields.creator.name}}" comment="{{issue.meta.fields.creator.displayName}}"

# Transition an issue by target status
- name: Close the issue
  jira: uri={{server}} username={{user}} password={{pass}}
        issue={{issue.meta.key}} operation=transition status="Done"
"""

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # Let snippet from module_utils/basic.py return a proper error in this case
        pass

import base64

def request(url, user, passwd, data=None, method=None):
    if data:
        data = json.dumps(data)

    # NOTE: fetch_url uses a password manager, which follows the
    # standard request-then-challenge basic-auth semantics. However as
    # JIRA allows some unauthorised operations it doesn't necessarily
    # send the challenge, so the request occurs as the anonymous user,
    # resulting in unexpected results. To work around this we manually
    # inject the basic-auth header up-front to ensure that JIRA treats
    # the requests as authorized for this user.
    auth = base64.encodestring('%s:%s' % (user, passwd)).replace('\n', '')
    response, info = fetch_url(module, url, data=data, method=method, 
                               headers={'Content-Type':'application/json',
                                        'Authorization':"Basic %s" % auth})

    if info['status'] not in (200, 204):
        module.fail_json(msg=info['msg'])

    body = response.read()

    if body:
        return json.loads(body)
    else:
        return {}

def post(url, user, passwd, data):
    return request(url, user, passwd, data=data, method='POST')

def put(url, user, passwd, data):
    return request(url, user, passwd, data=data, method='PUT')

def get(url, user, passwd):
    return request(url, user, passwd)


def create(restbase, user, passwd, params):
    createfields = {
        'project': { 'key': params['project'] },
        'summary': params['summary'],
        'description': params['description'],
        'issuetype': { 'name': params['issuetype'] }}

    # Merge in any additional or overridden fields
    if params['fields']:
        createfields.update(params['fields'])

    data = {'fields': createfields}

    url = restbase + '/issue/'

    ret = post(url, user, passwd, data) 

    return ret


def comment(restbase, user, passwd, params):
    data = {
        'body': params['comment']
        }

    url = restbase + '/issue/' + params['issue'] + '/comment'

    ret = post(url, user, passwd, data)

    return ret


def edit(restbase, user, passwd, params):
    data = {
        'fields': params['fields']
        }

    url = restbase + '/issue/' + params['issue']    

    ret = put(url, user, passwd, data) 

    return ret


def fetch(restbase, user, passwd, params):
    url = restbase + '/issue/' + params['issue']
    ret = get(url, user, passwd) 
    return ret


def transition(restbase, user, passwd, params):
    # Find the transition id
    turl = restbase + '/issue/' + params['issue'] + "/transitions"
    tmeta = get(turl, user, passwd)

    target = params['status']
    tid = None
    for t in tmeta['transitions']:
        if t['name'] == target:
            tid = t['id']
            break

    if not tid:
        raise ValueError("Failed find valid transition for '%s'" % target)

    # Perform it
    url = restbase + '/issue/' + params['issue'] + "/transitions"
    data = { 'transition': { "id" : tid },
             'fields': params['fields']}

    ret = post(url, user, passwd, data)

    return ret


# Some parameters are required depending on the operation:
OP_REQUIRED = dict(create=['project', 'issuetype', 'summary', 'description'],
                   comment=['issue', 'comment'],
                   edit=[],
                   fetch=['issue'],
                   transition=['status'])

def main():

    global module
    module = AnsibleModule(
        argument_spec=dict(
            uri=dict(required=True),
            operation=dict(choices=['create', 'comment', 'edit', 'fetch', 'transition'],
                           aliases=['command'], required=True),
            username=dict(required=True),
            password=dict(required=True),
            project=dict(),
            summary=dict(),
            description=dict(),
            issuetype=dict(),
            issue=dict(aliases=['ticket']),
            comment=dict(),
            status=dict(),
            assignee=dict(),
            fields=dict(default={})
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

    # Handle rest of parameters
    uri = module.params['uri']
    user = module.params['username']
    passwd = module.params['password']
    if module.params['assignee']:
        module.params['fields']['assignee'] = { 'name': module.params['assignee'] }

    if not uri.endswith('/'):
        uri = uri+'/'
    restbase = uri + 'rest/api/2'

    # Dispatch
    try:
        
        # Lookup the corresponding method for this operation. This is
        # safe as the AnsibleModule should remove any unknown operations.
        thismod = sys.modules[__name__]
        method = getattr(thismod, op)

        ret = method(restbase, user, passwd, module.params)

    except Exception, e:
        return module.fail_json(msg=e.message)


    module.exit_json(changed=True, meta=ret)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
main()
