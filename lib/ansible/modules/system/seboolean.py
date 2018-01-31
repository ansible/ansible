#!/usr/bin/python

# Copyright: (c) 2012, Stephen Fromm <sfromm@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: seboolean
short_description: Toggles SELinux booleans
description:
     - Toggles SELinux booleans.
version_added: "0.7"
options:
  name:
    description:
      - Name of the boolean to configure.
    required: true
  persistent:
    description:
      - Set to C(yes) if the boolean setting should survive a reboot.
    type: bool
    default: 'no'
  state:
    description:
      - Desired boolean value
    type: bool
    required: true
notes:
   - Not tested on any Debian based system.
requirements:
- libselinux-python
- libsemanage-python
author:
- Stephen Fromm (@sfromm)
'''

EXAMPLES = '''
- name: Set httpd_can_network_connect flag on and keep it persistent across reboots
  seboolean:
    name: httpd_can_network_connect
    state: yes
    persistent: yes
'''

import os

try:
    import selinux
    HAVE_SELINUX = True
except ImportError:
    HAVE_SELINUX = False

try:
    import semanage
    HAVE_SEMANAGE = True
except ImportError:
    HAVE_SEMANAGE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import binary_type
from ansible.module_utils._text import to_bytes


def has_boolean_value(module, name):
    bools = []
    try:
        rc, bools = selinux.security_get_boolean_names()
    except OSError:
        module.fail_json(msg="Failed to get list of boolean names")
    # work around for selinux who changed its API, see
    # https://github.com/ansible/ansible/issues/25651
    if len(bools) > 0:
        if isinstance(bools[0], binary_type):
            name = to_bytes(name)
    if name in bools:
        return True
    else:
        return False


def get_boolean_value(module, name):
    state = 0
    try:
        state = selinux.security_get_boolean_active(name)
    except OSError:
        module.fail_json(msg="Failed to determine current state for boolean %s" % name)
    if state == 1:
        return True
    else:
        return False


# The following method implements what setsebool.c does to change
# a boolean and make it persist after reboot..
def semanage_boolean_value(module, name, state):
    rc = 0
    value = 0
    if state:
        value = 1
    handle = semanage.semanage_handle_create()
    if handle is None:
        module.fail_json(msg="Failed to create semanage library handle")
    try:
        managed = semanage.semanage_is_managed(handle)
        if managed < 0:
            module.fail_json(msg="Failed to determine whether policy is manage")
        if managed == 0:
            if os.getuid() == 0:
                module.fail_json(msg="Cannot set persistent booleans without managed policy")
            else:
                module.fail_json(msg="Cannot set persistent booleans; please try as root")
        if semanage.semanage_connect(handle) < 0:
            module.fail_json(msg="Failed to connect to semanage")

        if semanage.semanage_begin_transaction(handle) < 0:
            module.fail_json(msg="Failed to begin semanage transaction")

        rc, sebool = semanage.semanage_bool_create(handle)
        if rc < 0:
            module.fail_json(msg="Failed to create seboolean with semanage")
        if semanage.semanage_bool_set_name(handle, sebool, name) < 0:
            module.fail_json(msg="Failed to set seboolean name with semanage")
        semanage.semanage_bool_set_value(sebool, value)

        rc, boolkey = semanage.semanage_bool_key_extract(handle, sebool)
        if rc < 0:
            module.fail_json(msg="Failed to extract boolean key with semanage")

        if semanage.semanage_bool_modify_local(handle, boolkey, sebool) < 0:
            module.fail_json(msg="Failed to modify boolean key with semanage")

        if semanage.semanage_bool_set_active(handle, boolkey, sebool) < 0:
            module.fail_json(msg="Failed to set boolean key active with semanage")

        semanage.semanage_bool_key_free(boolkey)
        semanage.semanage_bool_free(sebool)

        semanage.semanage_set_reload(handle, 0)
        if semanage.semanage_commit(handle) < 0:
            module.fail_json(msg="Failed to commit changes to semanage")

        semanage.semanage_disconnect(handle)
        semanage.semanage_handle_destroy(handle)
    except Exception as e:
        module.fail_json(msg="Failed to manage policy for boolean %s: %s" % (name, str(e)))
    return True


def set_boolean_value(module, name, state):
    rc = 0
    value = 0
    if state:
        value = 1
    try:
        rc = selinux.security_set_boolean(name, value)
    except OSError:
        module.fail_json(msg="Failed to set boolean %s to %s" % (name, value))
    if rc == 0:
        return True
    else:
        return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            persistent=dict(type='bool', default=False),
            state=dict(type='bool', required=True),
        ),
        supports_check_mode=True,
    )

    if not HAVE_SELINUX:
        module.fail_json(msg="This module requires libselinux-python support")

    if not HAVE_SEMANAGE:
        module.fail_json(msg="This module requires libsemanage-python support")

    if not selinux.is_selinux_enabled():
        module.fail_json(msg="SELinux is disabled on this host.")

    name = module.params['name']
    persistent = module.params['persistent']
    state = module.params['state']

    result = dict(
        name=name,
    )

    if hasattr(selinux, 'selinux_boolean_sub'):
        # selinux_boolean_sub allows sites to rename a boolean and alias the old name
        # Feature only available in selinux library since 2012.
        name = selinux.selinux_boolean_sub(name)

    if not has_boolean_value(module, name):
        module.fail_json(msg="SELinux boolean %s does not exist." % name)

    cur_value = get_boolean_value(module, name)

    if cur_value == state:
        module.exit_json(changed=False, state=cur_value, **result)

    if module.check_mode:
        module.exit_json(changed=True)

    if persistent:
        r = semanage_boolean_value(module, name, state)
    else:
        r = set_boolean_value(module, name, state)

    result['changed'] = r
    if not r:
        module.fail_json(msg="Failed to set boolean %s to %s" % (name, state))
    try:
        selinux.security_commit_booleans()
    except:
        module.fail_json(msg="Failed to commit pending boolean %s value" % name)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
