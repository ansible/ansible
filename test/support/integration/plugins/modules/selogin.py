#!/usr/bin/python

# (c) 2017, Petr Lautrbach <plautrba@redhat.com>
# Based on seport.py module (c) 2014, Dan Keder <dan.keder@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: selogin
short_description: Manages linux user to SELinux user mapping
description:
     - Manages linux user to SELinux user mapping
version_added: "2.8"
options:
  login:
    description:
      - a Linux user
    required: true
  seuser:
    description:
      - SELinux user name
    required: true
  selevel:
    aliases: [ serange ]
    description:
      - MLS/MCS Security Range (MLS/MCS Systems only) SELinux Range for SELinux login mapping defaults to the SELinux user record range.
    default: s0
  state:
    description:
      - Desired mapping value.
    required: true
    default: present
    choices: [ 'present', 'absent' ]
  reload:
    description:
      - Reload SELinux policy after commit.
    default: yes
  ignore_selinux_state:
    description:
    - Run independent of selinux runtime state
    type: bool
    default: false
notes:
   - The changes are persistent across reboots
   - Not tested on any debian based system
requirements: [ 'libselinux', 'policycoreutils' ]
author:
- Dan Keder (@dankeder)
- Petr Lautrbach (@bachradsusi)
- James Cassell (@jamescassell)
'''

EXAMPLES = '''
# Modify the default user on the system to the guest_u user
- selogin:
    login: __default__
    seuser: guest_u
    state: present

# Assign gijoe user on an MLS machine a range and to the staff_u user
- selogin:
    login: gijoe
    seuser: staff_u
    serange: SystemLow-Secret
    state: present

# Assign all users in the engineering group to the staff_u user
- selogin:
    login: '%engineering'
    seuser: staff_u
    state: present
'''

RETURN = r'''
# Default return values
'''


import traceback

SELINUX_IMP_ERR = None
try:
    import selinux
    HAVE_SELINUX = True
except ImportError:
    SELINUX_IMP_ERR = traceback.format_exc()
    HAVE_SELINUX = False

SEOBJECT_IMP_ERR = None
try:
    import seobject
    HAVE_SEOBJECT = True
except ImportError:
    SEOBJECT_IMP_ERR = traceback.format_exc()
    HAVE_SEOBJECT = False


from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native


def semanage_login_add(module, login, seuser, do_reload, serange='s0', sestore=''):
    """ Add linux user to SELinux user mapping

    :type module: AnsibleModule
    :param module: Ansible module

    :type login: str
    :param login: a Linux User or a Linux group if it begins with %

    :type seuser: str
    :param proto: An SELinux user ('__default__', 'unconfined_u', 'staff_u', ...), see 'semanage login -l'

    :type serange: str
    :param serange: SELinux MLS/MCS range (defaults to 's0')

    :type do_reload: bool
    :param do_reload: Whether to reload SELinux policy after commit

    :type sestore: str
    :param sestore: SELinux store

    :rtype: bool
    :return: True if the policy was changed, otherwise False
    """
    try:
        selogin = seobject.loginRecords(sestore)
        selogin.set_reload(do_reload)
        change = False
        all_logins = selogin.get_all()
        # module.fail_json(msg="%s: %s %s" % (all_logins, login, sestore))
        # for local_login in all_logins:
        if login not in all_logins.keys():
            change = True
            if not module.check_mode:
                selogin.add(login, seuser, serange)
        else:
            if all_logins[login][0] != seuser or all_logins[login][1] != serange:
                change = True
                if not module.check_mode:
                    selogin.modify(login, seuser, serange)

    except (ValueError, KeyError, OSError, RuntimeError) as e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, to_native(e)), exception=traceback.format_exc())

    return change


def semanage_login_del(module, login, seuser, do_reload, sestore=''):
    """ Delete linux user to SELinux user mapping

    :type module: AnsibleModule
    :param module: Ansible module

    :type login: str
    :param login: a Linux User or a Linux group if it begins with %

    :type seuser: str
    :param proto: An SELinux user ('__default__', 'unconfined_u', 'staff_u', ...), see 'semanage login -l'

    :type do_reload: bool
    :param do_reload: Whether to reload SELinux policy after commit

    :type sestore: str
    :param sestore: SELinux store

    :rtype: bool
    :return: True if the policy was changed, otherwise False
    """
    try:
        selogin = seobject.loginRecords(sestore)
        selogin.set_reload(do_reload)
        change = False
        all_logins = selogin.get_all()
        # module.fail_json(msg="%s: %s %s" % (all_logins, login, sestore))
        if login in all_logins.keys():
            change = True
            if not module.check_mode:
                selogin.delete(login)

    except (ValueError, KeyError, OSError, RuntimeError) as e:
        module.fail_json(msg="%s: %s\n" % (e.__class__.__name__, to_native(e)), exception=traceback.format_exc())

    return change


def get_runtime_status(ignore_selinux_state=False):
    return True if ignore_selinux_state is True else selinux.is_selinux_enabled()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ignore_selinux_state=dict(type='bool', default=False),
            login=dict(type='str', required=True),
            seuser=dict(type='str'),
            selevel=dict(type='str', aliases=['serange'], default='s0'),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            reload=dict(type='bool', default=True),
        ),
        required_if=[
            ["state", "present", ["seuser"]]
        ],
        supports_check_mode=True
    )
    if not HAVE_SELINUX:
        module.fail_json(msg=missing_required_lib("libselinux"), exception=SELINUX_IMP_ERR)

    if not HAVE_SEOBJECT:
        module.fail_json(msg=missing_required_lib("seobject from policycoreutils"), exception=SEOBJECT_IMP_ERR)

    ignore_selinux_state = module.params['ignore_selinux_state']

    if not get_runtime_status(ignore_selinux_state):
        module.fail_json(msg="SELinux is disabled on this host.")

    login = module.params['login']
    seuser = module.params['seuser']
    serange = module.params['selevel']
    state = module.params['state']
    do_reload = module.params['reload']

    result = {
        'login': login,
        'seuser': seuser,
        'serange': serange,
        'state': state,
    }

    if state == 'present':
        result['changed'] = semanage_login_add(module, login, seuser, do_reload, serange)
    elif state == 'absent':
        result['changed'] = semanage_login_del(module, login, seuser, do_reload)
    else:
        module.fail_json(msg='Invalid value of argument "state": {0}'.format(state))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
