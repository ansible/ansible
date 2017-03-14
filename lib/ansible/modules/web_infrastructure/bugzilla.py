#!/usr/bin/python
#
# Created on Mar 10, 2017
# @author: Bhavik Bhavsar (9.bhavik@gmail.com)
#
#
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
#

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}


DOCUMENTATION = '''
---
module: bugzilla
short_description: Perform various actions with bugzilla
description:
    - Fetch status of particular bugzilla id from Bugzilla url provided.
version_added: "2.3"
author: Bhavik Bhavsar
requirements:
    - "python >= 2.6"
    - "python-bugzilla >= 2.0.0"
options:
    url:
        description:
            - url of bugzilla server
        required: true
    bug_id:
        description:
            - Bugzilla ID from Bugzilla
        required: true
    user:
        description:
            - username to login into Bugzilla
        required: false
    password:
        description:
            - password to login into Bugzilla
        required: false
    get_status:
        description:
            - Enable to fetch status of particular bugzilla id
        required: false
'''


EXAMPLES = '''

#for private bug

- name: Get status for BZ 14295
  bugzilla:
    url: "bugzilla.redhat.com"
    bug_id: 14295
    user: <username>
    password: <password>
    get_status: True
  register: status

#for non-private bug

- name: Get status for BZ 1429535
  bugzilla:
    url: "bugzilla.redhat.com"
    bug_id: 1429535
    get_status: True
  register: status

'''


RETURN = '''
status:
  description: Fetches status of bugzilla
  returned: Only when commands get_status is set to True and Bug_id is provided
  type: string
  sample: "NEW"
'''

from ansible.module_utils.basic import AnsibleModule

import bugzilla
import xmlrpclib
import sys

def bugzilla_status(bug):
    return bug.status


def main():
    module = AnsibleModule(
        argument_spec = dict(
            url = dict(required=True, type='str'),
            bug_id = dict(required=True, type='int'),
            user = dict(required=False, type='str'),
            password = dict(required=False, type='str', no_log=True),
            get_status = dict(required=False, type='bool')
        ),
        required_together=[['user', 'password']]
    )

    url = module.params['url']
    bug_id = module.params['bug_id']
    user = module.params['user']
    password = module.params['password']
    get_status = module.params['get_status']

    if not bug_id:
        module.fail_json(msg="bug_id missing")

    if not get_status:
        module.fail_json(msg="get_status param not set")

    try:
        bzapi = bugzilla.Bugzilla(url, user, password)
        bug = bzapi.getbug(bug_id)

    except:
        t, e = sys.exc_info()[:2]
        response = {e.faultCode:e.faultString}
        module.fail_json(msg="FaultError", FaultError=response)

    else:
        status = bugzilla_status(bug)
        module.exit_json(changed=False, status=status)

if __name__ == '__main__':
    main()
