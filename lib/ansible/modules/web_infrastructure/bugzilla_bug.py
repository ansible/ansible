#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Bhavik Bhavsar <9.bhavik@gmail.com>
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

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0'
}

DOCUMENTATION = '''
---
module: bugzilla_bug
short_description: Fetch details about a bug from a given bugzilla server
description:
    - Details such as status, resolution, severity, etc.,
      can be fetched for a particular I(bug_id).
version_added: "2.4"
author: Bhavik Bhavsar
requirements:
    - "python >= 2.6"
options:
    url:
        description:
            - U(url) of bugzilla server
        required: true
    bug_id:
        description:
            - Bugzilla ID from Bugzilla
        required: true
    url_username:
        description:
            - I(url_username) to login into Bugzilla server
              if access to private bug is required
        required: false
    url_password:
        description:
            - I(url_password) to login into Bugzilla server
              if access to private bug is required
        required: false
'''


EXAMPLES = '''

# For fetching details about non-private bug
- name: Get status for BZ 1429535
  bugzilla_bug:
    url: "https://bugzilla.redhat.com"
    bug_id: 1429535
  register: bug

# For fetching details about private bug
- name: Get status for BZ 14295
  bugzilla_bug:
    url: "https://bugzilla.redhat.com"
    bug_id: 14295
    url_username: userfoo
    url_password: passwordfoo
  register: bug

# Register bug holds all bug details it can be access as below
# For fetching status
- debug: var=bug.bug.result.bugs[0].status
# For fetching resolution
- debug: var=bug.bug.result.bugs[0].resolution
# For fetching severity
- debug: var=bug.bug.result.bugs[0].severity
'''

RETURN = '''
bug:
  description: Fetches details of bug
  returned: Bug Details
  type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, url_argument_spec
from ansible.module_utils.json_utils import json


def bz_get(module, url, data, method):
    """ Helper function which will only do one thing that is
    calling bugzilla server using fetch_url """
    headers = {'Content-Type': 'application/json'}
    url = url + "/jsonrpc.cgi?" + data
    resp, info = fetch_url(module, url, headers=headers, method=method)
    return resp, info


def main():
    argument_spec = url_argument_spec()
    argument_spec.update(
        url=dict(required=True, type='str'),
        bug_id=dict(required=True, type='str')
    )
    module = AnsibleModule(
        argument_spec=argument_spec
    )

    bug_id = module.params['bug_id']
    user = module.params['url_username']
    password = module.params['url_password']
    url = module.params['url']

    # Update module parameters by user's parameters if defined
    if 'params' in module.params and isinstance(module.params['params'], dict):
        module.params.update(module.params['params'])
    # Remove the params
    module.params.pop('params', None)

    # Constructing the data/parameter for jsonrpc
    if user and password:
        data = 'params=[{"Bugzilla_login":"%s","Bugzilla_password":"%s",' \
               '"ids":[%s]}]' % (user, password, bug_id)
    else:
        data = 'params=[{"ids":[%s]}]' % (bug_id)

    # Combining method and data
    data = "method=Bug.get&%s" % (data)
    resp, info = bz_get(module, url, data, 'GET')

    if info.get("status") != 200:
        module.fail_json(msg="HTTP error " +
                             str(info["status"]) + " " + info["msg"])

    response = resp.read()
    resp_json = json.loads(response)
    error = resp_json.get("error")

    # Addressing failure scenarios
    # when username password is incorrect or
    # accessing a private bug without credentials

    if error is not None:
        module.fail_json(msg=error)

    bug_detail = resp_json
    module.exit_json(bug=bug_detail)


if __name__ == '__main__':
    main()
