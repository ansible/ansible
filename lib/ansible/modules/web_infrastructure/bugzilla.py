#!/usr/bin/python

DOCUMENTATION = '''
---
module: bugzilla
short_description: Perform various actions with bugzilla
description:
    - Fetch status of particular bugzilla id from Bugzilla url provided.
version_added: "2.2"
author: Bhavik Bhavsar
requirements:
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


import bugzilla
import xmlrpclib


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

    except xmlrpclib.Fault as err:
        response = {err.faultCode:err.faultString}
        module.fail_json(msg="FaultError", FaultError=response)

    else:
        status = bugzilla_status(bug)
        module.exit_json(changed=False, status=status)

from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
