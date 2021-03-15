#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: pingdom
short_description: Pause/unpause Pingdom alerts
description:
    - This module will let you pause/unpause Pingdom alerts
version_added: "1.2"
author:
    - "Dylan Silva (@thaumos)"
    - "Justin Johns (!UNKNOWN)"
requirements:
    - "This pingdom python library: https://github.com/mbabineau/pingdom-python"
options:
    state:
        description:
            - Define whether or not the check should be running or paused.
        required: true
        choices: [ "running", "paused" ]
    checkid:
        description:
            - Pingdom ID of the check.
        required: true
    uid:
        description:
            - Pingdom user ID.
        required: true
    passwd:
        description:
            - Pingdom user password.
        required: true
    key:
        description:
            - Pingdom API key.
        required: true
notes:
    - This module does not yet have support to add/remove checks.
'''

EXAMPLES = '''
# Pause the check with the ID of 12345.
- pingdom:
    uid: example@example.com
    passwd: password123
    key: apipassword123
    checkid: 12345
    state: paused

# Unpause the check with the ID of 12345.
- pingdom:
    uid: example@example.com
    passwd: password123
    key: apipassword123
    checkid: 12345
    state: running
'''

import traceback

PINGDOM_IMP_ERR = None
try:
    import pingdom
    HAS_PINGDOM = True
except Exception:
    PINGDOM_IMP_ERR = traceback.format_exc()
    HAS_PINGDOM = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


def pause(checkid, uid, passwd, key):

    c = pingdom.PingdomConnection(uid, passwd, key)
    c.modify_check(checkid, paused=True)
    check = c.get_check(checkid)
    name = check.name
    result = check.status
    # if result != "paused":             # api output buggy - accept raw exception for now
    #    return (True, name, result)
    return (False, name, result)


def unpause(checkid, uid, passwd, key):

    c = pingdom.PingdomConnection(uid, passwd, key)
    c.modify_check(checkid, paused=False)
    check = c.get_check(checkid)
    name = check.name
    result = check.status
    # if result != "up":                 # api output buggy - accept raw exception for now
    #    return (True, name, result)
    return (False, name, result)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, choices=['running', 'paused', 'started', 'stopped']),
            checkid=dict(required=True),
            uid=dict(required=True),
            passwd=dict(required=True, no_log=True),
            key=dict(required=True, no_log=True)
        )
    )

    if not HAS_PINGDOM:
        module.fail_json(msg=missing_required_lib("pingdom"), exception=PINGDOM_IMP_ERR)

    checkid = module.params['checkid']
    state = module.params['state']
    uid = module.params['uid']
    passwd = module.params['passwd']
    key = module.params['key']

    if (state == "paused" or state == "stopped"):
        (rc, name, result) = pause(checkid, uid, passwd, key)

    if (state == "running" or state == "started"):
        (rc, name, result) = unpause(checkid, uid, passwd, key)

    if rc != 0:
        module.fail_json(checkid=checkid, name=name, status=result)

    module.exit_json(checkid=checkid, name=name, status=result)


if __name__ == '__main__':
    main()
