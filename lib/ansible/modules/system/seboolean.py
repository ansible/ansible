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
  ignore_selinux_state:
    description:
    - Useful for scenarios (chrooted environment) that you can't get the real SELinux state.
    type: bool
    default: false
    version_added: '2.8'
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
import traceback

SELINUX_IMP_ERR = None
try:
    import selinux
    HAVE_SELINUX = True
except ImportError:
    SELINUX_IMP_ERR = traceback.format_exc()
    HAVE_SELINUX = False

SEMANAGE_IMP_ERR = None
try:
    import semanage
    HAVE_SEMANAGE = True
except ImportError:
    SEMANAGE_IMP_ERR = traceback.format_exc()
    HAVE_SEMANAGE = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six import binary_type
from ansible.module_utils._text import to_bytes, to_text


def get_runtime_status(ignore_selinux_state=False):
    return True if ignore_selinux_state is True else selinux.is_selinux_enabled()


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


def semanage_get_handle(module):
    handle = semanage.semanage_handle_create()
    if not handle:
        module.fail_json(msg="Failed to create semanage library handle")

    managed = semanage.semanage_is_managed(handle)
    if managed <= 0:
        semanage.semanage_handle_destroy(handle)
    if managed < 0:
        module.fail_json(msg="Failed to determine whether policy is manage")
    if managed == 0:
        if os.getuid() == 0:
            module.fail_json(msg="Cannot set persistent booleans without managed policy")
        else:
            module.fail_json(msg="Cannot set persistent booleans; please try as root")

    if semanage.semanage_connect(handle) < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to connect to semanage")

    return handle


def semanage_begin_transaction(module, handle):
    if semanage.semanage_begin_transaction(handle) < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to begin semanage transaction")


def semanage_set_boolean_value(module, handle, name, value):
    rc, t_b = semanage.semanage_bool_create(handle)
    if rc < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to create seboolean with semanage")

    if semanage.semanage_bool_set_name(handle, t_b, name) < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to set seboolean name with semanage")

    rc, boolkey = semanage.semanage_bool_key_extract(handle, t_b)
    if rc < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to extract boolean key with semanage")

    rc, exists = semanage.semanage_bool_exists(handle, boolkey)
    if rc < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to check if boolean is defined")
    if not exists:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="SELinux boolean %s is not defined in persistent policy" % name)

    rc, sebool = semanage.semanage_bool_query(handle, boolkey)
    if rc < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to query boolean in persistent policy")

    semanage.semanage_bool_set_value(sebool, value)

    if semanage.semanage_bool_modify_local(handle, boolkey, sebool) < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to modify boolean key with semanage")

    if semanage.semanage_bool_set_active(handle, boolkey, sebool) < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to set boolean key active with semanage")

    semanage.semanage_bool_key_free(boolkey)
    semanage.semanage_bool_free(t_b)
    semanage.semanage_bool_free(sebool)


def semanage_get_boolean_value(module, handle, name):
    rc, t_b = semanage.semanage_bool_create(handle)
    if rc < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to create seboolean with semanage")

    if semanage.semanage_bool_set_name(handle, t_b, name) < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to set seboolean name with semanage")

    rc, boolkey = semanage.semanage_bool_key_extract(handle, t_b)
    if rc < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to extract boolean key with semanage")

    rc, exists = semanage.semanage_bool_exists(handle, boolkey)
    if rc < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to check if boolean is defined")
    if not exists:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="SELinux boolean %s is not defined in persistent policy" % name)

    rc, sebool = semanage.semanage_bool_query(handle, boolkey)
    if rc < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to query boolean in persistent policy")

    value = semanage.semanage_bool_get_value(sebool)

    semanage.semanage_bool_key_free(boolkey)
    semanage.semanage_bool_free(t_b)
    semanage.semanage_bool_free(sebool)

    return value


def semanage_commit(module, handle, load=0):
    semanage.semanage_set_reload(handle, load)
    if semanage.semanage_commit(handle) < 0:
        semanage.semanage_handle_destroy(handle)
        module.fail_json(msg="Failed to commit changes to semanage")


def semanage_destroy_handle(module, handle):
    rc = semanage.semanage_disconnect(handle)
    semanage.semanage_handle_destroy(handle)
    if rc < 0:
        module.fail_json(msg="Failed to disconnect from semanage")


# The following method implements what setsebool.c does to change
# a boolean and make it persist after reboot..
def semanage_boolean_value(module, name, state):
    value = 0
    changed = False
    if state:
        value = 1
    try:
        handle = semanage_get_handle(module)
        semanage_begin_transaction(module, handle)
        cur_value = semanage_get_boolean_value(module, handle, name)
        if cur_value != value:
            changed = True
            if not module.check_mode:
                semanage_set_boolean_value(module, handle, name, value)
                semanage_commit(module, handle)
        semanage_destroy_handle(module, handle)
    except Exception as e:
        module.fail_json(msg=u"Failed to manage policy for boolean %s: %s" % (name, to_text(e)))
    return changed


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
            ignore_selinux_state=dict(type='bool', default=False),
            name=dict(type='str', required=True),
            persistent=dict(type='bool', default=False),
            state=dict(type='bool', required=True),
        ),
        supports_check_mode=True,
    )

    if not HAVE_SELINUX:
        module.fail_json(msg=missing_required_lib('libselinux-python'), exception=SELINUX_IMP_ERR)

    if not HAVE_SEMANAGE:
        module.fail_json(msg=missing_required_lib('libsemanage-python'), exception=SEMANAGE_IMP_ERR)

    ignore_selinux_state = module.params['ignore_selinux_state']

    if not get_runtime_status(ignore_selinux_state):
        module.fail_json(msg="SELinux is disabled on this host.")

    name = module.params['name']
    persistent = module.params['persistent']
    state = module.params['state']

    result = dict(
        name=name,
        persistent=persistent,
        state=state
    )
    changed = False

    if hasattr(selinux, 'selinux_boolean_sub'):
        # selinux_boolean_sub allows sites to rename a boolean and alias the old name
        # Feature only available in selinux library since 2012.
        name = selinux.selinux_boolean_sub(name)

    if not has_boolean_value(module, name):
        module.fail_json(msg="SELinux boolean %s does not exist." % name)

    if persistent:
        changed = semanage_boolean_value(module, name, state)
    else:
        cur_value = get_boolean_value(module, name)
        if cur_value != state:
            changed = True
            if not module.check_mode:
                changed = set_boolean_value(module, name, state)
                if not changed:
                    module.fail_json(msg="Failed to set boolean %s to %s" % (name, state))
                try:
                    selinux.security_commit_booleans()
                except Exception:
                    module.fail_json(msg="Failed to commit pending boolean %s value" % name)

    result['changed'] = changed

    module.exit_json(**result)


if __name__ == '__main__':
    main()
