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


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception

try:
    import bugzilla

    HAS_BUGZILLA = True
except ImportError:
    HAS_BUGZILLA = False


ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0'
}

DOCUMENTATION = '''
---
module: bugzilla
short_description: Perform various actions with bugzilla
description:
  - Fetch status of particular bugzilla id from Bugzilla URL provided.
version_added: '2.3'
author:
  - Bhavik Bhavsar (@bhavik)
requirements:
  - python >= 2.6
  - python-bugzilla >= 2.0.0
options:
  url:
    description:
      - URL of bugzilla server
    required: true
  bug_id:
    description:
      - I(bug_id) from Bugzilla
    required: true
  user:
    description:
      - I(user) to login into Bugzilla
    required: false
  password:
    description:
      - I(password) along with I(user) to login to Bugzilla
    required: false
  get_status:
    required: false
    choices: [ yes, no ]
    default: yes
    description:
      - Enable to fetch status of particular I(bug_id)
'''


EXAMPLES = '''
# For private bug
- name: Get status for BZ 14295
  bugzilla:
    url: bugzilla.redhat.com
    bug_id: 14295
    user: userfoo
    password: password123
    get_status: yes
  register: status

# For non-private bug
- name: Get status for BZ 1429535
  bugzilla:
    url: bugzilla.redhat.com
    bug_id: 1429535
    get_status: yes
  register: status
'''


RETURN = '''
status:
  description: Fetches status of bugzilla
  returned: Only when commands I(get_status) is set to C(yes)
            and I(bug_id) is provided
  type: string
  sample: NEW
'''


def bugzilla_status(bug):
    return bug.status


def main():
    module = AnsibleModule(
        argument_spec=dict(url=dict(
            required=True, type='str'),
            bug_id=dict(required=True, type='int'),
            user=dict(required=False, type='str'),
            password=dict(required=False,
                          type='str',
                          no_log=True),
            get_status=dict(required=False,
                            choices=['yes', 'no'],
                            default='yes')
        ),
        required_together=[['user', 'password']]
    )

    url = module.params['url']
    bug_id = module.params['bug_id']
    user = module.params['user']
    password = module.params['password']
    get_status = module.params['get_status']

    if not HAS_BUGZILLA:
        module.fail_json(
            msg="Missing required 'python-bugzilla' module "
                "(pip install python-bugzilla)")

    try:
        bzapi = bugzilla.Bugzilla(url, user, password)
        bug = bzapi.getbug(bug_id)
    except:
        e = get_exception()
        module.fail_json(msg="Error", Error=str(e))
    else:
        if get_status == 'yes':
            status = bugzilla_status(bug)
            module.exit_json(changed=False, status=status)
        else:
            module.fail_json(msg='Please set get_status as "yes"')


if __name__ == '__main__':
    main()
