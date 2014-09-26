#!/usr/bin/python

DOCUMENTATION = '''

module: pingdom
short_description: Pause/unpause Pingdom alerts
description:
    - This module will let you pause/unpause Pingdom alerts
version_added: "1.2"
author: Justin Johns
requirements:
    - "This pingdom python library: https://github.com/mbabineau/pingdom-python"
options:
    state:
        description:
            - Define whether or not the check should be running or paused.
        required: true
        default: null
        choices: [ "running", "paused" ]
        aliases: []
    checkid:
        description:
            - Pingdom ID of the check.
        required: true
        default: null
        choices: []
        aliases: []
    uid:
        description:
            - Pingdom user ID.
        required: true
        default: null
        choices: []
        aliases: []
    passwd:
        description:
            - Pingdom user password.
        required: true
        default: null
        choices: []
        aliases: []
    key:
        description:
            - Pingdom API key.
        required: true
        default: null
        choices: []
        aliases: []
notes:
    - This module does not yet have support to add/remove checks.
'''

EXAMPLES = '''
# Pause the check with the ID of 12345.
- pingdom: uid=example@example.com
           passwd=password123
           key=apipassword123
           checkid=12345
           state=paused

# Unpause the check with the ID of 12345.
- pingdom: uid=example@example.com
           passwd=password123
           key=apipassword123
           checkid=12345
           state=running
'''

try:
    import pingdom
    HAS_PINGDOM = True
except:
    HAS_PINGDOM = False



def pause(checkid, uid, passwd, key):

    c = pingdom.PingdomConnection(uid, passwd, key)
    c.modify_check(checkid, paused=True)
    check = c.get_check(checkid)
    name = check.name
    result = check.status
    #if result != "paused":             # api output buggy - accept raw exception for now
    #    return (True, name, result)
    return (False, name, result)


def unpause(checkid, uid, passwd, key):

    c = pingdom.PingdomConnection(uid, passwd, key)
    c.modify_check(checkid, paused=False)
    check = c.get_check(checkid)
    name = check.name
    result = check.status
    #if result != "up":                 # api output buggy - accept raw exception for now
    #    return (True, name, result)
    return (False, name, result)


def main():

    module = AnsibleModule(
        argument_spec=dict(
        state=dict(required=True, choices=['running', 'paused', 'started', 'stopped']),
        checkid=dict(required=True),
        uid=dict(required=True),
        passwd=dict(required=True),
        key=dict(required=True)
        )
    )

    if not HAS_PINGDOM:
        module.fail_json(msg="Missing requried pingdom module (check docs)")

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

# import module snippets
from ansible.module_utils.basic import *
main()
