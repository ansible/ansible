# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Stephen Fromm <sfromm@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
module: user
version_added: "0.2"
short_description: Manage user accounts
description:
    - Manage user accounts and user attributes.
    - For Windows targets, use the M(ansible.windows.win_user) module instead.
options:
    name:
        description:
            - Name of the user to create, remove or modify.
        type: str
        required: true
        aliases: [ user ]
    uid:
        description:
            - Optionally sets the I(UID) of the user.
        type: int
    comment:
        description:
            - Optionally sets the description (aka I(GECOS)) of user account.
            - On macOS, this defaults to the O(name) option.
        type: str
    hidden:
        description:
            - macOS only, optionally hide the user from the login window and system preferences.
            - The default will be V(true) if the O(system) option is used.
        type: bool
        version_added: "2.6"
    non_unique:
        description:
            - Optionally when used with the C(-u) option, this option allows to change the user ID to a non-unique value.
        type: bool
        default: no
        version_added: "1.1"
    seuser:
        description:
            - Optionally sets the C(seuser) type C(user_u) on SELinux enabled systems.
        type: str
        version_added: "2.1"
    group:
        description:
            - Optionally sets the user's primary group (takes a group name).
            - On macOS, this defaults to V(staff).
        type: str
    groups:
        description:
            - A list of supplementary groups which the user is also a member of.
            - By default, the user is removed from all other groups. Configure O(append) to modify this.
            - When set to an empty string V(''),
              the user is removed from all groups except the primary group.
            - Before Ansible 2.3, the only input format allowed was a comma separated string.
        type: list
        elements: str
    append:
        description:
            - If V(true), add the user to the groups specified in O(groups).
            - If V(false), user will only be added to the groups specified in O(groups),
              removing them from all other groups.
        type: bool
        default: no
    shell:
        description:
            - Optionally set the user's shell.
            - On macOS, before Ansible 2.5, the default shell for non-system users was V(/usr/bin/false).
              Since Ansible 2.5, the default shell for non-system users on macOS is V(/bin/bash).
            - On other operating systems, the default shell is determined by the underlying tool
              invoked by this module. See Notes for a per platform list of invoked tools.
            - From Ansible 2.18, the type is changed to I(path) from I(str).
        type: path
    home:
        description:
            - Optionally set the user's home directory.
        type: path
    skeleton:
        description:
            - Optionally set a home skeleton directory.
            - Requires O(create_home) option!
        type: str
        version_added: "2.0"
    password:
        description:
            - If provided, set the user's password to the provided encrypted hash (Linux) or plain text password (macOS).
            - B(Linux/Unix/POSIX:) Enter the hashed password as the value.
            - See L(FAQ entry,https://docs.ansible.com/ansible/latest/reference_appendices/faq.html#how-do-i-generate-encrypted-passwords-for-the-user-module)
              for details on various ways to generate the hash of a password.
            - To create an account with a locked/disabled password on Linux systems, set this to V('!') or V('*').
            - To create an account with a locked/disabled password on OpenBSD, set this to V('*************').
            - B(OS X/macOS:) Enter the cleartext password as the value. Be sure to take relevant security precautions.
            - On macOS, the password specified in the C(password) option will always be set, regardless of whether the user account already exists or not.
            - When the password is passed as an argument, the M(ansible.builtin.user) module will always return changed to C(true) for macOS systems.
              Since macOS no longer provides access to the hashed passwords directly.
        type: str
    state:
        description:
            - Whether the account should exist or not, taking action if the state is different from what is stated.
            - See this L(FAQ entry,https://docs.ansible.com/ansible/latest/reference_appendices/faq.html#running-on-macos-as-a-target)
              for additional requirements when removing users on macOS systems.
        type: str
        choices: [ absent, present ]
        default: present
    create_home:
        description:
            - Unless set to V(false), a home directory will be made for the user
              when the account is created or if the home directory does not exist.
            - Changed from O(createhome) to O(create_home) in Ansible 2.5.
        type: bool
        default: yes
        aliases: [ createhome ]
    move_home:
        description:
            - "If set to V(true) when used with O(home), attempt to move the user's old home
              directory to the specified directory if it isn't there already and the old home exists."
        type: bool
        default: no
    system:
        description:
            - When creating an account O(state=present), setting this to V(true) makes the user a system account.
            - This setting cannot be changed on existing users.
        type: bool
        default: no
    force:
        description:
            - This only affects O(state=absent), it forces removal of the user and associated directories on supported platforms.
            - The behavior is the same as C(userdel --force), check the man page for C(userdel) on your system for details and support.
            - When used with O(generate_ssh_key=yes) this forces an existing key to be overwritten.
        type: bool
        default: no
    remove:
        description:
            - This only affects O(state=absent), it attempts to remove directories associated with the user.
            - The behavior is the same as C(userdel --remove), check the man page for details and support.
        type: bool
        default: no
    login_class:
        description:
            - Optionally sets the user's login class, a feature of most BSD OSs.
        type: str
    generate_ssh_key:
        description:
            - Whether to generate a SSH key for the user in question.
            - This will B(not) overwrite an existing SSH key unless used with O(force=yes).
        type: bool
        default: no
        version_added: "0.9"
    ssh_key_bits:
        description:
            - Optionally specify number of bits in SSH key to create.
            - The default value depends on C(ssh-keygen).
        type: int
        version_added: "0.9"
    ssh_key_type:
        description:
            - Optionally specify the type of SSH key to generate.
            - Available SSH key types will depend on implementation
              present on target host.
        type: str
        default: rsa
        version_added: "0.9"
    ssh_key_file:
        description:
            - Optionally specify the SSH key filename.
            - If this is a relative filename then it will be relative to the user's home directory.
            - This parameter defaults to V(.ssh/id_rsa).
        type: path
        version_added: "0.9"
    ssh_key_comment:
        description:
            - Optionally define the comment for the SSH key.
        type: str
        default: ansible-generated on $HOSTNAME
        version_added: "0.9"
    ssh_key_passphrase:
        description:
            - Set a passphrase for the SSH key.
            - If no passphrase is provided, the SSH key will default to having no passphrase.
        type: str
        version_added: "0.9"
    update_password:
        description:
            - V(always) will update passwords if they differ.
            - V(on_create) will only set the password for newly created users.
        type: str
        choices: [ always, on_create ]
        default: always
        version_added: "1.3"
    expires:
        description:
            - An expiry time for the user in epoch, it will be ignored on platforms that do not support this.
            - Currently supported on GNU/Linux, FreeBSD, and DragonFlyBSD.
            - Since Ansible 2.6 you can remove the expiry time by specifying a negative value.
              Currently supported on GNU/Linux and FreeBSD.
        type: float
        version_added: "1.9"
    password_lock:
        description:
            - Lock the password (C(usermod -L), C(usermod -U), C(pw lock)).
            - Implementation differs by platform. This option does not always mean the user cannot login using other methods.
            - This option does not disable the user, only lock the password.
            - This must be set to V(false) in order to unlock a currently locked password. The absence of this parameter will not unlock a password.
            - Currently supported on Linux, FreeBSD, DragonFlyBSD, NetBSD, OpenBSD.
        type: bool
        version_added: "2.6"
    local:
        description:
            - Forces the use of "local" command alternatives on platforms that implement it.
            - This is useful in environments that use centralized authentication when you want to manipulate the local users
              (in other words, it uses C(luseradd) instead of C(useradd)).
            - This will check C(/etc/passwd) for an existing account before invoking commands. If the local account database
              exists somewhere other than C(/etc/passwd), this setting will not work properly.
            - This requires that the above commands as well as C(/etc/passwd) must exist on the target host, otherwise it will be a fatal error.
        type: bool
        default: no
        version_added: "2.4"
    profile:
        description:
            - Sets the profile of the user.
            - Can set multiple profiles using comma separation.
            - To delete all the profiles, use O(profile='').
            - Currently supported on Illumos/Solaris. Does nothing when used with other platforms.
        type: str
        version_added: "2.8"
    authorization:
        description:
            - Sets the authorization of the user.
            - Can set multiple authorizations using comma separation.
            - To delete all authorizations, use O(authorization='').
            - Currently supported on Illumos/Solaris. Does nothing when used with other platforms.
        type: str
        version_added: "2.8"
    role:
        description:
            - Sets the role of the user.
            - Can set multiple roles using comma separation.
            - To delete all roles, use O(role='').
            - Currently supported on Illumos/Solaris. Does nothing when used with other platforms.
        type: str
        version_added: "2.8"
    password_expire_max:
        description:
            - Maximum number of days between password change.
            - Supported on Linux only.
        type: int
        version_added: "2.11"
    password_expire_min:
        description:
            - Minimum number of days between password change.
            - Supported on Linux only.
        type: int
        version_added: "2.11"
    password_expire_warn:
        description:
            - Number of days of warning before password expires.
            - Supported on Linux only.
        type: int
        version_added: "2.16"
    umask:
        description:
            - Sets the umask of the user.
            - Currently supported on Linux. Does nothing when used with other platforms.
            - Requires O(local) is omitted or V(false).
        type: str
        version_added: "2.12"
    password_expire_account_disable:
        description:
            - Number of days after a password expires until the account is disabled.
            - Currently supported on AIX, Linux, NetBSD, OpenBSD.
        type: int
        version_added: "2.18"
    uid_min:
        description:
            - Sets the UID_MIN value for user creation.
            - Overwrites /etc/login.defs default value.
            - Currently supported on Linux. Does nothing when used with other platforms.
            - Requires O(local) is omitted or V(False).
        type: int
        version_added: "2.18"
    uid_max:
        description:
            - Sets the UID_MAX value for user creation.
            - Overwrites /etc/login.defs default value.
            - Currently supported on Linux. Does nothing when used with other platforms.
            - Requires O(local) is omitted or V(False).
        type: int
        version_added: "2.18"

extends_documentation_fragment: action_common_attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
    platform:
        platforms: posix
notes:
  - There are specific requirements per platform on user management utilities. However
    they generally come pre-installed with the system and Ansible will require they
    are present at runtime. If they are not, a descriptive error message will be shown.
  - On SunOS platforms, the shadow file is backed up automatically since this module edits it directly.
    On other platforms, the shadow file is backed up by the underlying tools used by this module.
  - On macOS, this module uses C(dscl) to create, modify, and delete accounts. C(dseditgroup) is used to
    modify group membership. Accounts are hidden from the login window by modifying
    C(/Library/Preferences/com.apple.loginwindow.plist).
  - On FreeBSD, this module uses C(pw useradd) and C(chpass) to create, C(pw usermod) and C(chpass) to modify,
    C(pw userdel) remove, C(pw lock) to lock, and C(pw unlock) to unlock accounts.
  - On all other platforms, this module uses C(useradd) to create, C(usermod) to modify, and
    C(userdel) to remove accounts.
seealso:
- module: ansible.posix.authorized_key
- module: ansible.builtin.group
- module: ansible.windows.win_user
author:
- Stephen Fromm (@sfromm)
"""

EXAMPLES = r"""
- name: Add the user 'johnd' with a specific uid and a primary group of 'admin'
  ansible.builtin.user:
    name: johnd
    comment: John Doe
    uid: 1040
    group: admin

- name: Create a user 'johnd' with a home directory
  ansible.builtin.user:
    name: johnd
    create_home: yes

- name: Add the user 'james' with a bash shell, appending the group 'admins' and 'developers' to the user's groups
  ansible.builtin.user:
    name: james
    shell: /bin/bash
    groups: admins,developers
    append: yes

- name: Remove the user 'johnd'
  ansible.builtin.user:
    name: johnd
    state: absent
    remove: yes

- name: Create a 2048-bit SSH key for user jsmith in ~jsmith/.ssh/id_rsa
  ansible.builtin.user:
    name: jsmith
    generate_ssh_key: yes
    ssh_key_bits: 2048
    ssh_key_file: .ssh/id_rsa

- name: Added a consultant whose account you want to expire
  ansible.builtin.user:
    name: james18
    shell: /bin/zsh
    groups: developers
    expires: 1422403387

- name: Starting at Ansible 2.6, modify user, remove expiry time
  ansible.builtin.user:
    name: james18
    expires: -1

- name: Set maximum expiration date for password
  ansible.builtin.user:
    name: ram19
    password_expire_max: 10

- name: Set minimum expiration date for password
  ansible.builtin.user:
    name: pushkar15
    password_expire_min: 5

- name: Set number of warning days for password expiration
  ansible.builtin.user:
    name: jane157
    password_expire_warn: 30

- name: Set number of days after password expires until account is disabled
  ansible.builtin.user:
    name: jimholden2016
    password_expire_account_disable: 15
"""

RETURN = r"""
append:
  description: Whether or not to append the user to groups.
  returned: When O(state) is V(present) and the user exists
  type: bool
  sample: True
comment:
  description: Comment section from passwd file, usually the user name.
  returned: When user exists
  type: str
  sample: Agent Smith
create_home:
  description: Whether or not to create the home directory.
  returned: When user does not exist and not check mode
  type: bool
  sample: True
force:
  description: Whether or not a user account was forcibly deleted.
  returned: When O(state) is V(absent) and user exists
  type: bool
  sample: False
group:
  description: Primary user group ID
  returned: When user exists
  type: int
  sample: 1001
groups:
  description: List of groups of which the user is a member.
  returned: When O(groups) is not empty and O(state) is V(present)
  type: str
  sample: 'chrony,apache'
home:
  description: "Path to user's home directory."
  returned: When O(state) is V(present)
  type: str
  sample: '/home/asmith'
move_home:
  description: Whether or not to move an existing home directory.
  returned: When O(state) is V(present) and user exists
  type: bool
  sample: False
name:
  description: User account name.
  returned: always
  type: str
  sample: asmith
password:
  description: Masked value of the password.
  returned: When O(state) is V(present) and O(password) is not empty
  type: str
  sample: 'NOT_LOGGING_PASSWORD'
remove:
  description: Whether or not to remove the user account.
  returned: When O(state) is V(absent) and user exists
  type: bool
  sample: True
shell:
  description: User login shell.
  returned: When O(state) is V(present)
  type: str
  sample: '/bin/bash'
ssh_fingerprint:
  description: Fingerprint of generated SSH key.
  returned: When O(generate_ssh_key) is V(True)
  type: str
  sample: '2048 SHA256:aYNHYcyVm87Igh0IMEDMbvW0QDlRQfE0aJugp684ko8 ansible-generated on host (RSA)'
ssh_key_file:
  description: Path to generated SSH private key file.
  returned: When O(generate_ssh_key) is V(True)
  type: str
  sample: /home/asmith/.ssh/id_rsa
ssh_public_key:
  description: Generated SSH public key file.
  returned: When O(generate_ssh_key) is V(True)
  type: str
  sample: >
    'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC95opt4SPEC06tOYsJQJIuN23BbLMGmYo8ysVZQc4h2DZE9ugbjWWGS1/pweUGjVstgzMkBEeBCByaEf/RJKNecKRPeGd2Bw9DCj/bn5Z6rGfNENKBmo
    618mUJBvdlEgea96QGjOwSB7/gmonduC7gsWDMNcOdSE3wJMTim4lddiBx4RgC9yXsJ6Tkz9BHD73MXPpT5ETnse+A3fw3IGVSjaueVnlUyUmOBf7fzmZbhlFVXf2Zi2rFTXqvbdGHKkzpw1U8eB8xFPP7y
    d5u1u0e6Acju/8aZ/l17IDFiLke5IzlqIMRTEbDwLNeO84YQKWTm9fODHzhYe0yvxqLiK07 ansible-generated on host'
stderr:
  description: Standard error from running commands.
  returned: When stderr is returned by a command that is run
  type: str
  sample: Group wheels does not exist
stdout:
  description: Standard output from running commands.
  returned: When standard output is returned by the command that is run
  type: str
  sample:
system:
  description: Whether or not the account is a system account.
  returned: When O(system) is passed to the module and the account does not exist
  type: bool
  sample: True
uid:
  description: User ID of the user account.
  returned: When O(uid) is passed to the module
  type: int
  sample: 1044
"""


import ctypes.util
from datetime import datetime
import grp
import calendar
import os
import re
import pty
import pwd
import select
import shutil
import socket
import subprocess
import time
import math
import typing as t

from ansible.module_utils import distro
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.locale import get_best_parsable_locale
from ansible.module_utils.common.sys_info import get_platform_subclass


class StructSpwdType(ctypes.Structure):
    _fields_ = [
        ('sp_namp', ctypes.c_char_p),
        ('sp_pwdp', ctypes.c_char_p),
        ('sp_lstchg', ctypes.c_long),
        ('sp_min', ctypes.c_long),
        ('sp_max', ctypes.c_long),
        ('sp_warn', ctypes.c_long),
        ('sp_inact', ctypes.c_long),
        ('sp_expire', ctypes.c_long),
        ('sp_flag', ctypes.c_ulong),
    ]


try:
    _LIBC = ctypes.cdll.LoadLibrary(
        t.cast(
            str,
            ctypes.util.find_library('c')
        )
    )
    _LIBC.getspnam.argtypes = (ctypes.c_char_p,)
    _LIBC.getspnam.restype = ctypes.POINTER(StructSpwdType)
    HAVE_SPWD = True
except AttributeError:
    HAVE_SPWD = False


_HASH_RE = re.compile(r'[^a-zA-Z0-9./=]')


def getspnam(b_name):
    return _LIBC.getspnam(b_name).contents


class User(object):
    """
    This is a generic User manipulation class that is subclassed
    based on platform.

    A subclass may wish to override the following action methods:-
      - create_user()
      - remove_user()
      - modify_user()
      - ssh_key_gen()
      - ssh_key_fingerprint()
      - user_exists()

    All subclasses MUST define platform and distribution (which may be None).
    """
    platform = 'Generic'
    distribution = None  # type: str | None
    PASSWORDFILE = '/etc/passwd'
    SHADOWFILE = '/etc/shadow'  # type: str | None
    SHADOWFILE_EXPIRE_INDEX = 7
    LOGIN_DEFS = '/etc/login.defs'
    DATE_FORMAT = '%Y-%m-%d'

    def __new__(cls, *args, **kwargs):
        new_cls = get_platform_subclass(User)
        return super(cls, new_cls).__new__(new_cls)

    def __init__(self, module):
        self.module = module
        self.state = module.params['state']
        self.name = module.params['name']
        self.uid = module.params['uid']
        self.hidden = module.params['hidden']
        self.non_unique = module.params['non_unique']
        self.seuser = module.params['seuser']
        self.group = module.params['group']
        self.comment = module.params['comment']
        self.shell = module.params['shell']
        self.password = module.params['password']
        self.force = module.params['force']
        self.remove = module.params['remove']
        self.create_home = module.params['create_home']
        self.move_home = module.params['move_home']
        self.skeleton = module.params['skeleton']
        self.system = module.params['system']
        self.login_class = module.params['login_class']
        self.append = module.params['append']
        self.sshkeygen = module.params['generate_ssh_key']
        self.ssh_bits = module.params['ssh_key_bits']
        self.ssh_type = module.params['ssh_key_type']
        self.ssh_comment = module.params['ssh_key_comment']
        self.ssh_passphrase = module.params['ssh_key_passphrase']
        self.update_password = module.params['update_password']
        self.home = module.params['home']
        self.expires = None
        self.password_lock = module.params['password_lock']
        self.groups = None
        self.local = module.params['local']
        self.profile = module.params['profile']
        self.authorization = module.params['authorization']
        self.role = module.params['role']
        self.password_expire_max = module.params['password_expire_max']
        self.password_expire_min = module.params['password_expire_min']
        self.password_expire_warn = module.params['password_expire_warn']
        self.umask = module.params['umask']
        self.inactive = module.params['password_expire_account_disable']
        self.uid_min = module.params['uid_min']
        self.uid_max = module.params['uid_max']

        if self.local:
            if self.umask is not None:
                module.fail_json(msg="'umask' can not be used with 'local'")
            if self.uid_min is not None:
                module.fail_json(msg="'uid_min' can not be used with 'local'")
            if self.uid_max is not None:
                module.fail_json(msg="'uid_max' can not be used with 'local'")

        if module.params['groups'] is not None:
            self.groups = ','.join(module.params['groups'])

        if module.params['expires'] is not None:
            try:
                self.expires = time.gmtime(module.params['expires'])
            except Exception as e:
                module.fail_json(msg="Invalid value for 'expires' %s: %s" % (self.expires, to_native(e)))

        if module.params['ssh_key_file'] is not None:
            self.ssh_file = module.params['ssh_key_file']
        else:
            self.ssh_file = os.path.join('.ssh', 'id_%s' % self.ssh_type)

        if self.groups is None and self.append:
            # Change the argument_spec in 2.14 and remove this warning
            # required_by={'append': ['groups']}
            module.warn("'append' is set, but no 'groups' are specified. Use 'groups' for appending new groups."
                        "This will change to an error in Ansible 2.14.")

    def check_password_encrypted(self):
        # Darwin needs cleartext password, so skip validation
        if self.module.params['password'] and self.platform != 'Darwin':
            maybe_invalid = False

            # Allow setting certain passwords in order to disable the account
            if self.module.params['password'] in set(['*', '!', '*************']):
                maybe_invalid = False
            else:
                # : for delimiter, * for disable user, ! for lock user
                # these characters are invalid in the password
                if any(char in self.module.params['password'] for char in ':*!'):
                    maybe_invalid = True
                if '$' not in self.module.params['password']:
                    maybe_invalid = True
                else:
                    fields = self.module.params['password'].split("$")
                    if len(fields) >= 3:
                        # contains character outside the crypto constraint
                        if bool(_HASH_RE.search(fields[-1])):
                            maybe_invalid = True
                        # md5
                        if fields[1] == '1' and len(fields[-1]) != 22:
                            maybe_invalid = True
                        # sha256
                        if fields[1] == '5' and len(fields[-1]) != 43:
                            maybe_invalid = True
                        # sha512
                        if fields[1] == '6' and len(fields[-1]) != 86:
                            maybe_invalid = True
                        # yescrypt
                        if fields[1] == 'y' and len(fields[-1]) != 43:
                            maybe_invalid = True
                    else:
                        maybe_invalid = True
            if maybe_invalid:
                self.module.warn("The input password appears not to have been hashed. "
                                 "The 'password' argument must be encrypted for this module to work properly.")

    def execute_command(self, cmd, use_unsafe_shell=False, data=None, obey_checkmode=True):
        if self.module.check_mode and obey_checkmode:
            self.module.debug('In check mode, would have run: "%s"' % cmd)
            return (0, '', '')
        else:
            # cast all args to strings ansible-modules-core/issues/4397
            cmd = [str(x) for x in cmd]
            return self.module.run_command(cmd, use_unsafe_shell=use_unsafe_shell, data=data)

    def backup_shadow(self):
        if not self.module.check_mode and self.SHADOWFILE:
            return self.module.backup_local(self.SHADOWFILE)

    def remove_user_userdel(self):
        if self.local:
            command_name = 'luserdel'
        else:
            command_name = 'userdel'

        cmd = [self.module.get_bin_path(command_name, True)]
        if self.force and not self.local:
            cmd.append('-f')
        if self.remove:
            cmd.append('-r')
        cmd.append(self.name)

        return self.execute_command(cmd)

    def create_user_useradd(self):

        if self.local:
            command_name = 'luseradd'
            lgroupmod_cmd = self.module.get_bin_path('lgroupmod', True)
            lchage_cmd = self.module.get_bin_path('lchage', True)
        else:
            command_name = 'useradd'

        cmd = [self.module.get_bin_path(command_name, True)]

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.seuser is not None:
            cmd.append('-Z')
            cmd.append(self.seuser)
        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            cmd.append('-g')
            cmd.append(self.group)
        elif self.group_exists(self.name):
            # use the -N option (no user group) if a group already
            # exists with the same name as the user to prevent
            # errors from useradd trying to create a group when
            # USERGROUPS_ENAB is set in /etc/login.defs.
            if self.local:
                # luseradd uses -n instead of -N
                cmd.append('-n')
            else:
                if os.path.exists('/etc/redhat-release'):
                    dist = distro.version()
                    major_release = int(dist.split('.')[0])
                    if major_release <= 5:
                        cmd.append('-n')
                    else:
                        cmd.append('-N')
                elif os.path.exists('/etc/SuSE-release'):
                    # -N did not exist in useradd before SLE 11 and did not
                    # automatically create a group
                    dist = distro.version()
                    major_release = int(dist.split('.')[0])
                    if major_release >= 12:
                        cmd.append('-N')
                else:
                    cmd.append('-N')

        if self.groups is not None and len(self.groups):
            groups = self.get_groups_set()
            if not self.local:
                cmd.append('-G')
                cmd.append(','.join(groups))

        if self.comment is not None:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            # If the specified path to the user home contains parent directories that
            # do not exist and create_home is True first create the parent directory
            # since useradd cannot create it.
            if self.create_home:
                parent = os.path.dirname(self.home)
                if not os.path.isdir(parent):
                    self.create_homedir(self.home)
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.expires is not None and not self.local:
            cmd.append('-e')
            if self.expires < time.gmtime(0):
                cmd.append('')
            else:
                cmd.append(time.strftime(self.DATE_FORMAT, self.expires))

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(int(self.inactive))

        if self.password is not None:
            cmd.append('-p')
            if self.password_lock:
                cmd.append('!%s' % self.password)
            else:
                cmd.append(self.password)

        if self.create_home:
            if not self.local:
                cmd.append('-m')

            if self.skeleton is not None:
                cmd.append('-k')
                cmd.append(self.skeleton)

            if self.umask is not None:
                cmd.append('-K')
                cmd.append('UMASK=' + self.umask)
        else:
            cmd.append('-M')

        if self.system:
            cmd.append('-r')

        if self.uid_min is not None:
            cmd.append('-K')
            cmd.append('UID_MIN=' + str(self.uid_min))

        if self.uid_max is not None:
            cmd.append('-K')
            cmd.append('UID_MAX=' + str(self.uid_max))

        cmd.append(self.name)
        (rc, out, err) = self.execute_command(cmd)
        if not self.local or rc != 0:
            return (rc, out, err)

        if self.expires is not None:
            if self.expires < time.gmtime(0):
                lexpires = -1
            else:
                # Convert seconds since Epoch to days since Epoch
                lexpires = int(math.floor(self.module.params['expires'])) // 86400
            (rc, _out, _err) = self.execute_command([lchage_cmd, '-E', to_native(lexpires), self.name])
            out += _out
            err += _err
            if rc != 0:
                return (rc, out, err)

        if self.groups is None or len(self.groups) == 0:
            return (rc, out, err)

        for add_group in groups:
            (rc, _out, _err) = self.execute_command([lgroupmod_cmd, '-M', self.name, add_group])
            out += _out
            err += _err
            if rc != 0:
                return (rc, out, err)
        return (rc, out, err)

    def _check_usermod_append(self):
        # check if this version of usermod can append groups

        if self.local:
            command_name = 'lusermod'
        else:
            command_name = 'usermod'

        usermod_path = self.module.get_bin_path(command_name, True)

        # for some reason, usermod --help cannot be used by non root
        # on RH/Fedora, due to lack of execute bit for others
        if not os.access(usermod_path, os.X_OK):
            return False

        cmd = [usermod_path, '--help']
        (rc, data1, data2) = self.execute_command(cmd, obey_checkmode=False)
        helpout = data1 + data2

        # check if --append exists
        lines = to_native(helpout).split('\n')
        for line in lines:
            if line.strip().startswith('-a, --append'):
                return True

        return False

    def modify_user_usermod(self):

        if self.local:
            command_name = 'lusermod'
            lgroupmod_cmd = self.module.get_bin_path('lgroupmod', True)
            lgroupmod_add = set()
            lgroupmod_del = set()
            lchage_cmd = self.module.get_bin_path('lchage', True)
            lexpires = None
        else:
            command_name = 'usermod'

        cmd = [self.module.get_bin_path(command_name, True)]
        info = self.user_info()
        has_append = self._check_usermod_append()

        if self.uid is not None and info[2] != int(self.uid):
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            ginfo = self.group_info(self.group)
            if info[3] != ginfo[2]:
                cmd.append('-g')
                cmd.append(ginfo[2])

        if self.groups is not None:
            # get a list of all groups for the user, including the primary
            current_groups = self.user_group_membership(exclude_primary=False)
            groups_need_mod = False
            groups = []

            if self.groups == '':
                if current_groups and not self.append:
                    groups_need_mod = True
            else:
                groups = self.get_groups_set(remove_existing=False, names_only=True)
                group_diff = set(current_groups).symmetric_difference(groups)

                if group_diff:
                    if self.append:
                        for g in groups:
                            if g in group_diff:
                                if has_append:
                                    cmd.append('-a')
                                groups_need_mod = True
                                break
                    else:
                        groups_need_mod = True

            if groups_need_mod:
                if self.local:
                    if self.append:
                        lgroupmod_add = set(groups).difference(current_groups)
                        lgroupmod_del = set()
                    else:
                        lgroupmod_add = set(groups).difference(current_groups)
                        lgroupmod_del = set(current_groups).difference(groups)
                else:
                    if self.append and not has_append:
                        cmd.append('-A')
                        cmd.append(','.join(group_diff))
                    else:
                        cmd.append('-G')
                        cmd.append(','.join(groups))

        if self.comment is not None and info[4] != self.comment:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None and info[5] != self.home:
            cmd.append('-d')
            cmd.append(self.home)
            if self.move_home:
                cmd.append('-m')

        if self.shell is not None and info[6] != self.shell:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.expires is not None:

            current_expires = self.user_password()[1] or '0'
            current_expires = int(current_expires)

            if self.expires < time.gmtime(0):
                if current_expires >= 0:
                    if self.local:
                        lexpires = -1
                    else:
                        cmd.append('-e')
                        cmd.append('')
            else:
                # Convert days since Epoch to seconds since Epoch as struct_time
                current_expire_date = time.gmtime(current_expires * 86400)

                # Current expires is negative or we compare year, month, and day only
                if current_expires < 0 or current_expire_date[:3] != self.expires[:3]:
                    if self.local:
                        # Convert seconds since Epoch to days since Epoch
                        lexpires = int(math.floor(self.module.params['expires'])) // 86400
                    else:
                        cmd.append('-e')
                        cmd.append(time.strftime(self.DATE_FORMAT, self.expires))

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)

        # Lock if no password or unlocked, unlock only if locked
        if self.password_lock and not info[1].startswith('!'):
            cmd.append('-L')
        elif self.password_lock is False and info[1].startswith('!'):
            # usermod will refuse to unlock a user with no password, module shows 'changed' regardless
            cmd.append('-U')

        if self.update_password == 'always' and self.password is not None and info[1].lstrip('!') != self.password.lstrip('!'):
            # Remove options that are mutually exclusive with -p
            cmd = [c for c in cmd if c not in ['-U', '-L']]
            cmd.append('-p')
            if self.password_lock:
                # Lock the account and set the hash in a single command
                cmd.append('!%s' % self.password)
            else:
                cmd.append(self.password)

        (rc, out, err) = (None, '', '')

        # skip if no usermod changes to be made
        if len(cmd) > 1:
            cmd.append(self.name)
            (rc, out, err) = self.execute_command(cmd)

        if not self.local or not (rc is None or rc == 0):
            return (rc, out, err)

        if lexpires is not None:
            (rc, _out, _err) = self.execute_command([lchage_cmd, '-E', to_native(lexpires), self.name])
            out += _out
            err += _err
            if rc != 0:
                return (rc, out, err)

        if len(lgroupmod_add) == 0 and len(lgroupmod_del) == 0:
            return (rc, out, err)

        for add_group in lgroupmod_add:
            (rc, _out, _err) = self.execute_command([lgroupmod_cmd, '-M', self.name, add_group])
            out += _out
            err += _err
            if rc != 0:
                return (rc, out, err)

        for del_group in lgroupmod_del:
            (rc, _out, _err) = self.execute_command([lgroupmod_cmd, '-m', self.name, del_group])
            out += _out
            err += _err
            if rc != 0:
                return (rc, out, err)
        return (rc, out, err)

    def group_exists(self, group):
        try:
            # Try group as a gid first
            grp.getgrgid(int(group))
            return True
        except (ValueError, KeyError):
            try:
                grp.getgrnam(group)
                return True
            except KeyError:
                return False

    def group_info(self, group):
        if not self.group_exists(group):
            return False
        try:
            # Try group as a gid first
            return list(grp.getgrgid(int(group)))
        except (ValueError, KeyError):
            return list(grp.getgrnam(group))

    def get_groups_set(self, remove_existing=True, names_only=False):
        if self.groups is None:
            return None
        info = self.user_info()
        groups = set(x.strip() for x in self.groups.split(',') if x)
        group_names = set()
        for g in groups.copy():
            if not self.group_exists(g):
                self.module.fail_json(msg="Group %s does not exist" % (g))
            group_info = self.group_info(g)
            if info and remove_existing and group_info[2] == info[3]:
                groups.remove(g)
            elif names_only:
                group_names.add(group_info[0])
        if names_only:
            return group_names
        return groups

    def user_group_membership(self, exclude_primary=True):
        """ Return a list of groups the user belongs to """
        groups = []
        info = self.get_pwd_info()
        for group in grp.getgrall():
            if self.name in group.gr_mem:
                # Exclude the user's primary group by default
                if not exclude_primary:
                    groups.append(group[0])
                else:
                    if info[3] != group.gr_gid:
                        groups.append(group[0])

        return groups

    def user_exists(self):
        # The pwd module does not distinguish between local and directory accounts.
        # It's output cannot be used to determine whether or not an account exists locally.
        # It returns True if the account exists locally or in the directory, so instead
        # look in the local PASSWORD file for an existing account.
        if self.local:
            if not os.path.exists(self.PASSWORDFILE):
                self.module.fail_json(msg="'local: true' specified but unable to find local account file {0} to parse.".format(self.PASSWORDFILE))

            exists = False
            name_test = '{0}:'.format(self.name)
            with open(self.PASSWORDFILE, 'rb') as f:
                reversed_lines = f.readlines()[::-1]
                for line in reversed_lines:
                    if line.startswith(to_bytes(name_test)):
                        exists = True
                        break

            return exists

        else:
            try:
                if pwd.getpwnam(self.name):
                    return True
            except KeyError:
                return False

    def get_pwd_info(self):
        if not self.user_exists():
            return False
        return list(pwd.getpwnam(self.name))

    def user_info(self):
        if not self.user_exists():
            return False
        info = self.get_pwd_info()
        if len(info[1]) == 1 or len(info[1]) == 0:
            info[1] = self.user_password()[0]
        return info

    def set_password_expire(self):
        min_needs_change = self.password_expire_min is not None
        max_needs_change = self.password_expire_max is not None
        warn_needs_change = self.password_expire_warn is not None

        if HAVE_SPWD:
            try:
                shadow_info = getspnam(to_bytes(self.name))
            except ValueError:
                return None, '', ''

            min_needs_change &= self.password_expire_min != shadow_info.sp_min
            max_needs_change &= self.password_expire_max != shadow_info.sp_max
            warn_needs_change &= self.password_expire_warn != shadow_info.sp_warn

        if not (min_needs_change or max_needs_change or warn_needs_change):
            return (None, '', '')  # target state already reached

        command_name = 'chage'
        cmd = [self.module.get_bin_path(command_name, True)]
        if min_needs_change:
            cmd.extend(["-m", self.password_expire_min])
        if max_needs_change:
            cmd.extend(["-M", self.password_expire_max])
        if warn_needs_change:
            cmd.extend(["-W", self.password_expire_warn])
        cmd.append(self.name)

        return self.execute_command(cmd)

    def user_password(self):
        passwd = ''
        expires = ''
        if HAVE_SPWD:
            try:
                shadow_info = getspnam(to_bytes(self.name))
                passwd = to_native(shadow_info.sp_pwdp)
                expires = shadow_info.sp_expire
                return passwd, expires
            except ValueError:
                return passwd, expires

        if not self.user_exists():
            return passwd, expires
        elif self.SHADOWFILE:
            passwd, expires = self.parse_shadow_file()

        return passwd, expires

    def parse_shadow_file(self):
        passwd = ''
        expires = ''
        if os.path.exists(self.SHADOWFILE) and os.access(self.SHADOWFILE, os.R_OK):
            with open(self.SHADOWFILE, 'r') as f:
                for line in f:
                    if line.startswith('%s:' % self.name):
                        passwd = line.split(':')[1]
                        expires = line.split(':')[self.SHADOWFILE_EXPIRE_INDEX] or -1
        return passwd, expires

    def get_ssh_key_path(self):
        info = self.user_info()
        if os.path.isabs(self.ssh_file):
            ssh_key_file = self.ssh_file
        else:
            if not os.path.exists(info[5]) and not self.module.check_mode:
                raise Exception('User %s home directory does not exist' % self.name)
            ssh_key_file = os.path.join(info[5], self.ssh_file)
        return ssh_key_file

    def ssh_key_gen(self):
        info = self.user_info()
        overwrite = None
        try:
            ssh_key_file = self.get_ssh_key_path()
            pub_file = f'{ssh_key_file}.pub'
        except Exception as e:
            return (1, '', to_native(e))
        ssh_dir = os.path.dirname(ssh_key_file)

        if not os.path.exists(ssh_dir):
            if self.module.check_mode:
                return (0, '', '')
            try:
                os.mkdir(ssh_dir, int('0700', 8))
                os.chown(ssh_dir, info[2], info[3])
            except OSError as e:
                return (1, '', 'Failed to create %s: %s' % (ssh_dir, to_native(e)))

        if os.path.exists(ssh_key_file):
            if self.force:
                self.module.warn(f'Overwriting existing ssh key private file "{ssh_key_file}"')
                overwrite = 'y'
            else:
                self.module.warn(f'Found existing ssh key private file "{ssh_key_file}", no force, so skipping ssh-keygen generation')
                return (None, 'Key already exists, use "force: yes" to overwrite', '')

        if os.path.exists(pub_file):
            if self.force:
                self.module.warn(f'Overwriting existing ssh key public file "{pub_file}"')
                os.unlink(pub_file)
            else:
                self.module.warn(f'Found existing ssh key public file "{pub_file}", no force, so skipping ssh-keygen generation')
                return (None, 'Public key already exists, use "force: yes" to overwrite', '')

        cmd = [self.module.get_bin_path('ssh-keygen', True)]
        cmd.append('-t')
        cmd.append(self.ssh_type)
        if self.ssh_bits > 0:
            cmd.append('-b')
            cmd.append(self.ssh_bits)
        cmd.append('-C')
        cmd.append(self.ssh_comment)
        cmd.append('-f')
        cmd.append(ssh_key_file)
        if self.ssh_passphrase is not None:
            if self.module.check_mode:
                self.module.debug('In check mode, would have run: "%s"' % cmd)
                return (0, '', '')

            master_in_fd, slave_in_fd = pty.openpty()
            master_out_fd, slave_out_fd = pty.openpty()
            master_err_fd, slave_err_fd = pty.openpty()
            env = os.environ.copy()
            env['LC_ALL'] = get_best_parsable_locale(self.module)
            try:
                p = subprocess.Popen([to_bytes(c) for c in cmd],
                                     stdin=slave_in_fd,
                                     stdout=slave_out_fd,
                                     stderr=slave_err_fd,
                                     preexec_fn=os.setsid,
                                     env=env)
                out_buffer = b''
                err_buffer = b''
                first_prompt = b'Enter passphrase'
                second_prompt = b'Enter same passphrase again'
                prompt = first_prompt
                start = datetime.now()
                timeout = 900
                while p.poll() is None:
                    r_list = select.select([master_out_fd, master_err_fd], [], [], 1)[0]
                    now = datetime.now()
                    if (now - start).seconds > timeout:
                        return (1, '', f'Timeout after {timeout} while reading passphrase for SSH key')
                    for fd in r_list:
                        if fd == master_out_fd:
                            chunk = os.read(master_out_fd, 10240)
                            out_buffer += chunk
                            if prompt in out_buffer:
                                os.write(master_in_fd, to_bytes(self.ssh_passphrase, errors='strict') + b'\r')
                                prompt = second_prompt
                        else:
                            chunk = os.read(master_err_fd, 10240)
                            err_buffer += chunk
                            if prompt in err_buffer:
                                os.write(master_in_fd, to_bytes(self.ssh_passphrase, errors='strict') + b'\r')
                                prompt = second_prompt
                        if b'Overwrite (y/n)?' in out_buffer or b'Overwrite (y/n)?' in err_buffer:
                            # The key was created between us checking for existence and now
                            return (None, 'Key already exists', '')

                rc = p.returncode
                out = to_native(out_buffer)
                err = to_native(err_buffer)
            except OSError as e:
                return (1, '', to_native(e))
        else:
            cmd.append('-N')
            cmd.append('')

            (rc, out, err) = self.execute_command(cmd, data=overwrite)

        if rc == 0 and not self.module.check_mode:
            # If the keys were successfully created, we should be able
            # to tweak ownership.
            os.chown(ssh_key_file, info[2], info[3])
            os.chown(pub_file, info[2], info[3])
        return (rc, out, err)

    def ssh_key_fingerprint(self):
        ssh_key_file = self.get_ssh_key_path()
        if not os.path.exists(ssh_key_file):
            return (1, 'SSH Key file %s does not exist' % ssh_key_file, '')
        cmd = [self.module.get_bin_path('ssh-keygen', True)]
        cmd.append('-l')
        cmd.append('-f')
        cmd.append(ssh_key_file)

        return self.execute_command(cmd, obey_checkmode=False)

    def get_ssh_public_key(self):
        ssh_public_key_file = '%s.pub' % self.get_ssh_key_path()
        try:
            with open(ssh_public_key_file, 'r') as f:
                ssh_public_key = f.read().strip()
        except OSError:
            return None
        return ssh_public_key

    def create_user(self):
        # by default we use the create_user_useradd method
        return self.create_user_useradd()

    def remove_user(self):
        # by default we use the remove_user_userdel method
        return self.remove_user_userdel()

    def modify_user(self):
        # by default we use the modify_user_usermod method
        return self.modify_user_usermod()

    def create_homedir(self, path):
        if not os.path.exists(path):
            if self.skeleton is not None:
                skeleton = self.skeleton
            else:
                skeleton = '/etc/skel'

            if os.path.exists(skeleton) and skeleton != os.devnull:
                try:
                    shutil.copytree(skeleton, path, symlinks=True)
                except OSError as e:
                    self.module.exit_json(failed=True, msg="%s" % to_native(e))
            else:
                try:
                    os.makedirs(path)
                except OSError as e:
                    self.module.exit_json(failed=True, msg="%s" % to_native(e))
            # get umask from /etc/login.defs and set correct home mode
            if os.path.exists(self.LOGIN_DEFS):
                # fallback if neither HOME_MODE nor UMASK are set;
                # follow behaviour of useradd initializing UMASK = 022
                mode = 0o755
                with open(self.LOGIN_DEFS, 'r') as fh:
                    for line in fh:
                        # HOME_MODE has higher precedence as UMASK
                        match = re.match(r'^HOME_MODE\s+(\d+)$', line)
                        if match:
                            mode = int(match.group(1), 8)
                            break  # higher precedence
                        match = re.match(r'^UMASK\s+(\d+)$', line)
                        if match:
                            umask = int(match.group(1), 8)
                            mode = 0o777 & ~umask
                try:
                    os.chmod(path, mode)
                except OSError as e:
                    self.module.exit_json(failed=True, msg=to_native(e))

    def chown_homedir(self, uid, gid, path):
        try:
            os.chown(path, uid, gid)
            for root, dirs, files in os.walk(path):
                for d in dirs:
                    os.chown(os.path.join(root, d), uid, gid)
                for f in files:
                    full_path = os.path.join(root, f)
                    if not os.path.islink(full_path):
                        os.chown(full_path, uid, gid)
        except OSError as e:
            self.module.exit_json(failed=True, msg="%s" % to_native(e))


# ===========================================

class FreeBsdUser(User):
    """
    This is a FreeBSD User manipulation class - it uses the pw command
    to manipulate the user database, followed by the chpass command
    to change the password.

    This overrides the following methods from the generic class:-
      - create_user()
      - remove_user()
      - modify_user()
    """

    platform = 'FreeBSD'
    distribution = None
    SHADOWFILE = '/etc/master.passwd'
    SHADOWFILE_EXPIRE_INDEX = 6
    DATE_FORMAT = '%d-%b-%Y'

    def _handle_lock(self):
        info = self.user_info()
        if self.password_lock and not info[1].startswith('*LOCKED*'):
            cmd = [
                self.module.get_bin_path('pw', True),
                'lock',
                self.name
            ]
            if self.uid is not None and info[2] != int(self.uid):
                cmd.append('-u')
                cmd.append(self.uid)
            return self.execute_command(cmd)
        elif self.password_lock is False and info[1].startswith('*LOCKED*'):
            cmd = [
                self.module.get_bin_path('pw', True),
                'unlock',
                self.name
            ]
            if self.uid is not None and info[2] != int(self.uid):
                cmd.append('-u')
                cmd.append(self.uid)
            return self.execute_command(cmd)

        return (None, '', '')

    def remove_user(self):
        cmd = [
            self.module.get_bin_path('pw', True),
            'userdel',
            '-n',
            self.name
        ]
        if self.remove:
            cmd.append('-r')

        return self.execute_command(cmd)

    def create_user(self):
        cmd = [
            self.module.get_bin_path('pw', True),
            'useradd',
            '-n',
            self.name,
        ]

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.comment is not None:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            cmd.append('-d')
            cmd.append(self.home)

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            cmd.append('-g')
            cmd.append(self.group)

        if self.groups is not None:
            groups = self.get_groups_set()
            cmd.append('-G')
            cmd.append(','.join(groups))

        if self.create_home:
            cmd.append('-m')

            if self.skeleton is not None:
                cmd.append('-k')
                cmd.append(self.skeleton)

            if self.umask is not None:
                cmd.append('-K')
                cmd.append('UMASK=' + self.umask)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.login_class is not None:
            cmd.append('-L')
            cmd.append(self.login_class)

        if self.expires is not None:
            cmd.append('-e')
            if self.expires < time.gmtime(0):
                cmd.append('0')
            else:
                cmd.append(str(calendar.timegm(self.expires)))

        if self.uid_min is not None:
            cmd.append('-K')
            cmd.append('UID_MIN=' + str(self.uid_min))

        if self.uid_max is not None:
            cmd.append('-K')
            cmd.append('UID_MAX=' + str(self.uid_max))

        # system cannot be handled currently - should we error if its requested?
        # create the user
        (rc, out, err) = self.execute_command(cmd)

        if rc is not None and rc != 0:
            self.module.fail_json(name=self.name, msg=err, rc=rc)

        # we have to set the password in a second command
        if self.password is not None:
            cmd = [
                self.module.get_bin_path('chpass', True),
                '-p',
                self.password,
                self.name
            ]
            _rc, _out, _err = self.execute_command(cmd)
            if rc is None:
                rc = _rc
            out += _out
            err += _err

        # we have to lock/unlock the password in a distinct command
        _rc, _out, _err = self._handle_lock()
        if rc is None:
            rc = _rc
        out += _out
        err += _err

        return (rc, out, err)

    def modify_user(self):
        cmd = [
            self.module.get_bin_path('pw', True),
            'usermod',
            '-n',
            self.name
        ]
        cmd_len = len(cmd)
        info = self.user_info()

        if self.uid is not None and info[2] != int(self.uid):
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.comment is not None and info[4] != self.comment:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            if (info[5] != self.home and self.move_home) or (not os.path.exists(self.home) and self.create_home):
                cmd.append('-m')
            if info[5] != self.home:
                cmd.append('-d')
                cmd.append(self.home)

            if self.skeleton is not None:
                cmd.append('-k')
                cmd.append(self.skeleton)

            if self.umask is not None:
                cmd.append('-K')
                cmd.append('UMASK=' + self.umask)

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            ginfo = self.group_info(self.group)
            if info[3] != ginfo[2]:
                cmd.append('-g')
                cmd.append(self.group)

        if self.shell is not None and info[6] != self.shell:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.login_class is not None:
            # find current login class
            user_login_class = None
            if os.path.exists(self.SHADOWFILE) and os.access(self.SHADOWFILE, os.R_OK):
                with open(self.SHADOWFILE, 'r') as f:
                    for line in f:
                        if line.startswith('%s:' % self.name):
                            user_login_class = line.split(':')[4]

            # act only if login_class change
            if self.login_class != user_login_class:
                cmd.append('-L')
                cmd.append(self.login_class)

        if self.groups is not None:
            current_groups = self.user_group_membership()
            groups = self.get_groups_set(names_only=True)

            group_diff = set(current_groups).symmetric_difference(groups)
            groups_need_mod = False

            if group_diff:
                if self.append:
                    for g in groups:
                        if g in group_diff:
                            groups_need_mod = True
                            break
                else:
                    groups_need_mod = True

            if groups_need_mod:
                cmd.append('-G')
                new_groups = groups
                if self.append:
                    new_groups = groups | set(current_groups)
                cmd.append(','.join(new_groups))

        if self.expires is not None:

            current_expires = self.user_password()[1] or '0'
            current_expires = int(current_expires)

            # If expiration is negative or zero and the current expiration is greater than zero, disable expiration.
            # In OpenBSD, setting expiration to zero disables expiration. It does not expire the account.
            if self.expires <= time.gmtime(0):
                if current_expires > 0:
                    cmd.append('-e')
                    cmd.append('0')
            else:
                # Convert days since Epoch to seconds since Epoch as struct_time
                current_expire_date = time.gmtime(current_expires)

                # Current expires is negative or we compare year, month, and day only
                if current_expires <= 0 or current_expire_date[:3] != self.expires[:3]:
                    cmd.append('-e')
                    cmd.append(str(calendar.timegm(self.expires)))

        (rc, out, err) = (None, '', '')

        # modify the user if cmd will do anything
        if cmd_len != len(cmd):
            (rc, _out, _err) = self.execute_command(cmd)
            out += _out
            err += _err

            if rc is not None and rc != 0:
                self.module.fail_json(name=self.name, msg=err, rc=rc)

        # we have to set the password in a second command
        if self.update_password == 'always' and self.password is not None and info[1].lstrip('*LOCKED*') != self.password.lstrip('*LOCKED*'):
            cmd = [
                self.module.get_bin_path('chpass', True),
                '-p',
                self.password,
                self.name
            ]
            _rc, _out, _err = self.execute_command(cmd)
            if rc is None:
                rc = _rc
            out += _out
            err += _err

        # we have to lock/unlock the password in a distinct command
        _rc, _out, _err = self._handle_lock()
        if rc is None:
            rc = _rc
        out += _out
        err += _err

        return (rc, out, err)


class DragonFlyBsdUser(FreeBsdUser):
    """
    This is a DragonFlyBSD User manipulation class - it inherits the
    FreeBsdUser class behaviors, such as using the pw command to
    manipulate the user database, followed by the chpass command
    to change the password.
    """

    platform = 'DragonFly'


class OpenBSDUser(User):
    """
    This is a OpenBSD User manipulation class.
    Main differences are that OpenBSD:-
     - has no concept of "system" account.
     - has no force delete user

    This overrides the following methods from the generic class:-
      - create_user()
      - remove_user()
      - modify_user()
    """

    platform = 'OpenBSD'
    distribution = None
    SHADOWFILE = '/etc/master.passwd'

    def create_user(self):
        cmd = [self.module.get_bin_path('useradd', True)]

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            cmd.append('-g')
            cmd.append(self.group)

        if self.groups is not None:
            groups = self.get_groups_set()
            cmd.append('-G')
            cmd.append(','.join(groups))

        if self.comment is not None:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.login_class is not None:
            cmd.append('-L')
            cmd.append(self.login_class)

        if self.password is not None and self.password != '*':
            cmd.append('-p')
            cmd.append(self.password)

        if self.create_home:
            cmd.append('-m')

            if self.skeleton is not None:
                cmd.append('-k')
                cmd.append(self.skeleton)

            if self.umask is not None:
                cmd.append('-K')
                cmd.append('UMASK=' + self.umask)

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)
        if self.uid_min is not None:
            cmd.append('-K')
            cmd.append('UID_MIN=' + str(self.uid_min))

        if self.uid_max is not None:
            cmd.append('-K')
            cmd.append('UID_MAX=' + str(self.uid_max))

        cmd.append(self.name)
        return self.execute_command(cmd)

    def remove_user_userdel(self):
        cmd = [self.module.get_bin_path('userdel', True)]
        if self.remove:
            cmd.append('-r')
        cmd.append(self.name)
        return self.execute_command(cmd)

    def modify_user(self):
        cmd = [self.module.get_bin_path('usermod', True)]
        info = self.user_info()

        if self.uid is not None and info[2] != int(self.uid):
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            ginfo = self.group_info(self.group)
            if info[3] != ginfo[2]:
                cmd.append('-g')
                cmd.append(self.group)

        if self.groups is not None:
            current_groups = self.user_group_membership()
            groups_need_mod = False
            groups_option = '-S'
            groups = []

            if self.groups == '':
                if current_groups and not self.append:
                    groups_need_mod = True
            else:
                groups = self.get_groups_set(names_only=True)
                group_diff = set(current_groups).symmetric_difference(groups)

                if group_diff:
                    if self.append:
                        for g in groups:
                            if g in group_diff:
                                groups_option = '-G'
                                groups_need_mod = True
                                break
                    else:
                        groups_need_mod = True

            if groups_need_mod:
                cmd.append(groups_option)
                cmd.append(','.join(groups))

        if self.comment is not None and info[4] != self.comment:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None and info[5] != self.home:
            if self.move_home:
                cmd.append('-m')
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None and info[6] != self.shell:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)

        if self.login_class is not None:
            # find current login class
            user_login_class = None
            userinfo_cmd = [self.module.get_bin_path('userinfo', True), self.name]
            (rc, out, err) = self.execute_command(userinfo_cmd, obey_checkmode=False)

            for line in out.splitlines():
                tokens = line.split()

                if tokens[0] == 'class' and len(tokens) == 2:
                    user_login_class = tokens[1]

            # act only if login_class change
            if self.login_class != user_login_class:
                cmd.append('-L')
                cmd.append(self.login_class)

        if self.password_lock and not info[1].startswith('*'):
            cmd.append('-Z')
        elif self.password_lock is False and info[1].startswith('*'):
            cmd.append('-U')

        if self.update_password == 'always' and self.password is not None \
                and self.password != '*' and info[1] != self.password:
            cmd.append('-p')
            cmd.append(self.password)

        # skip if no changes to be made
        if len(cmd) == 1:
            return (None, '', '')

        cmd.append(self.name)
        return self.execute_command(cmd)


class NetBSDUser(User):
    """
    This is a NetBSD User manipulation class.
    Main differences are that NetBSD:-
     - has no concept of "system" account.
     - has no force delete user


    This overrides the following methods from the generic class:-
      - create_user()
      - remove_user()
      - modify_user()
    """

    platform = 'NetBSD'
    distribution = None
    SHADOWFILE = '/etc/master.passwd'

    def create_user(self):
        cmd = [self.module.get_bin_path('useradd', True)]

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            cmd.append('-g')
            cmd.append(self.group)

        if self.groups is not None:
            groups = self.get_groups_set()
            if len(groups) > 16:
                self.module.fail_json(msg="Too many groups (%d) NetBSD allows for 16 max." % len(groups))
            cmd.append('-G')
            cmd.append(','.join(groups))

        if self.comment is not None:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.login_class is not None:
            cmd.append('-L')
            cmd.append(self.login_class)

        if self.password is not None:
            cmd.append('-p')
            cmd.append(self.password)

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)

        if self.create_home:
            cmd.append('-m')

            if self.skeleton is not None:
                cmd.append('-k')
                cmd.append(self.skeleton)

            if self.umask is not None:
                cmd.append('-K')
                cmd.append('UMASK=' + self.umask)

        if self.uid_min is not None:
            cmd.append('-K')
            cmd.append('UID_MIN=' + str(self.uid_min))

        if self.uid_max is not None:
            cmd.append('-K')
            cmd.append('UID_MAX=' + str(self.uid_max))

        cmd.append(self.name)
        return self.execute_command(cmd)

    def remove_user_userdel(self):
        cmd = [self.module.get_bin_path('userdel', True)]
        if self.remove:
            cmd.append('-r')
        cmd.append(self.name)
        return self.execute_command(cmd)

    def modify_user(self):
        cmd = [self.module.get_bin_path('usermod', True)]
        info = self.user_info()

        if self.uid is not None and info[2] != int(self.uid):
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            ginfo = self.group_info(self.group)
            if info[3] != ginfo[2]:
                cmd.append('-g')
                cmd.append(self.group)

        if self.groups is not None:
            current_groups = self.user_group_membership()
            groups_need_mod = False
            groups = []

            if self.groups == '':
                if current_groups and not self.append:
                    groups_need_mod = True
            else:
                groups = self.get_groups_set(names_only=True)
                group_diff = set(current_groups).symmetric_difference(groups)

                if group_diff:
                    if self.append:
                        for g in groups:
                            if g in group_diff:
                                groups = set(current_groups).union(groups)
                                groups_need_mod = True
                                break
                    else:
                        groups_need_mod = True

            if groups_need_mod:
                if len(groups) > 16:
                    self.module.fail_json(msg="Too many groups (%d) NetBSD allows for 16 max." % len(groups))
                cmd.append('-G')
                cmd.append(','.join(groups))

        if self.comment is not None and info[4] != self.comment:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None and info[5] != self.home:
            if self.move_home:
                cmd.append('-m')
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None and info[6] != self.shell:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.login_class is not None:
            cmd.append('-L')
            cmd.append(self.login_class)

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)

        if self.update_password == 'always' and self.password is not None and info[1] != self.password:
            cmd.append('-p')
            cmd.append(self.password)

        if self.password_lock and not info[1].startswith('*LOCKED*'):
            cmd.append('-C yes')
        elif self.password_lock is False and info[1].startswith('*LOCKED*'):
            cmd.append('-C no')

        # skip if no changes to be made
        if len(cmd) == 1:
            return (None, '', '')

        cmd.append(self.name)
        return self.execute_command(cmd)


class SunOS(User):
    """
    This is a SunOS User manipulation class - The main difference between
    this class and the generic user class is that Solaris-type distros
    don't support the concept of a "system" account and we need to
    edit the /etc/shadow file manually to set a password. (Ugh)

    This overrides the following methods from the generic class:-
      - create_user()
      - remove_user()
      - modify_user()
      - user_info()
    """

    platform = 'SunOS'
    distribution = None
    SHADOWFILE = '/etc/shadow'
    USER_ATTR = '/etc/user_attr'

    def get_password_defaults(self):
        # Read password aging defaults
        try:
            minweeks = ''
            maxweeks = ''
            warnweeks = ''
            with open("/etc/default/passwd", 'r') as f:
                for line in f:
                    line = line.strip()
                    if (line.startswith('#') or line == ''):
                        continue
                    m = re.match(r'^([^#]*)#(.*)$', line)
                    if m:  # The line contains a hash / comment
                        line = m.group(1)
                    key, value = line.split('=')
                    if key == "MINWEEKS":
                        minweeks = value.rstrip('\n')
                    elif key == "MAXWEEKS":
                        maxweeks = value.rstrip('\n')
                    elif key == "WARNWEEKS":
                        warnweeks = value.rstrip('\n')
        except Exception as err:
            self.module.fail_json(msg="failed to read /etc/default/passwd: %s" % to_native(err))

        return (minweeks, maxweeks, warnweeks)

    def remove_user(self):
        cmd = [self.module.get_bin_path('userdel', True)]
        if self.remove:
            cmd.append('-r')
        cmd.append(self.name)

        return self.execute_command(cmd)

    def create_user(self):
        cmd = [self.module.get_bin_path('useradd', True)]

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            cmd.append('-g')
            cmd.append(self.group)

        if self.groups is not None:
            groups = self.get_groups_set()
            cmd.append('-G')
            cmd.append(','.join(groups))

        if self.comment is not None:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.create_home:
            cmd.append('-m')

            if self.skeleton is not None:
                cmd.append('-k')
                cmd.append(self.skeleton)

            if self.umask is not None:
                cmd.append('-K')
                cmd.append('UMASK=' + self.umask)

        if self.profile is not None:
            cmd.append('-P')
            cmd.append(self.profile)

        if self.authorization is not None:
            cmd.append('-A')
            cmd.append(self.authorization)

        if self.role is not None:
            cmd.append('-R')
            cmd.append(self.role)

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)
        if self.uid_min is not None:
            cmd.append('-K')
            cmd.append('UID_MIN=' + str(self.uid_min))

        if self.uid_max is not None:
            cmd.append('-K')
            cmd.append('UID_MAX=' + str(self.uid_max))

        cmd.append(self.name)

        (rc, out, err) = self.execute_command(cmd)
        if rc is not None and rc != 0:
            self.module.fail_json(name=self.name, msg=err, rc=rc)

        if not self.module.check_mode:
            # we have to set the password by editing the /etc/shadow file
            if self.password is not None:
                self.backup_shadow()
                minweeks, maxweeks, warnweeks = self.get_password_defaults()
                try:
                    lines = []
                    with open(self.SHADOWFILE, 'rb') as f:
                        for line in f:
                            line = to_native(line, errors='surrogate_or_strict')
                            fields = line.strip().split(':')
                            if not fields[0] == self.name:
                                lines.append(line)
                                continue
                            fields[1] = self.password
                            fields[2] = str(int(time.time() // 86400))
                            if minweeks:
                                try:
                                    fields[3] = str(int(minweeks) * 7)
                                except ValueError:
                                    # mirror solaris, which allows for any value in this field, and ignores anything that is not an int.
                                    pass
                            if maxweeks:
                                try:
                                    fields[4] = str(int(maxweeks) * 7)
                                except ValueError:
                                    # mirror solaris, which allows for any value in this field, and ignores anything that is not an int.
                                    pass
                            if warnweeks:
                                try:
                                    fields[5] = str(int(warnweeks) * 7)
                                except ValueError:
                                    # mirror solaris, which allows for any value in this field, and ignores anything that is not an int.
                                    pass
                            line = ':'.join(fields)
                            lines.append('%s\n' % line)
                    with open(self.SHADOWFILE, 'w+') as f:
                        f.writelines(lines)
                except Exception as err:
                    self.module.fail_json(msg="failed to update users password: %s" % to_native(err))

        return (rc, out, err)

    def modify_user_usermod(self):
        cmd = [self.module.get_bin_path('usermod', True)]
        cmd_len = len(cmd)
        info = self.user_info()

        if self.uid is not None and info[2] != int(self.uid):
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            ginfo = self.group_info(self.group)
            if info[3] != ginfo[2]:
                cmd.append('-g')
                cmd.append(self.group)

        if self.groups is not None:
            current_groups = self.user_group_membership()
            groups = self.get_groups_set(names_only=True)
            group_diff = set(current_groups).symmetric_difference(groups)
            groups_need_mod = False

            if group_diff:
                if self.append:
                    for g in groups:
                        if g in group_diff:
                            groups_need_mod = True
                            break
                else:
                    groups_need_mod = True

            if groups_need_mod:
                cmd.append('-G')
                new_groups = groups
                if self.append:
                    new_groups.update(current_groups)
                cmd.append(','.join(new_groups))

        if self.comment is not None and info[4] != self.comment:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None and info[5] != self.home:
            if self.move_home:
                cmd.append('-m')
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None and info[6] != self.shell:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.profile is not None and info[7] != self.profile:
            cmd.append('-P')
            cmd.append(self.profile)

        if self.authorization is not None and info[8] != self.authorization:
            cmd.append('-A')
            cmd.append(self.authorization)

        if self.role is not None and info[9] != self.role:
            cmd.append('-R')
            cmd.append(self.role)

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)

        # modify the user if cmd will do anything
        if cmd_len != len(cmd):
            cmd.append(self.name)
            (rc, out, err) = self.execute_command(cmd)
            if rc is not None and rc != 0:
                self.module.fail_json(name=self.name, msg=err, rc=rc)
        else:
            (rc, out, err) = (None, '', '')

        # we have to set the password by editing the /etc/shadow file
        if self.update_password == 'always' and self.password is not None and info[1] != self.password:
            self.backup_shadow()
            (rc, out, err) = (0, '', '')
            if not self.module.check_mode:
                minweeks, maxweeks, warnweeks = self.get_password_defaults()
                try:
                    lines = []
                    with open(self.SHADOWFILE, 'rb') as f:
                        for line in f:
                            line = to_native(line, errors='surrogate_or_strict')
                            fields = line.strip().split(':')
                            if not fields[0] == self.name:
                                lines.append(line)
                                continue
                            fields[1] = self.password
                            fields[2] = str(int(time.time() // 86400))
                            if minweeks:
                                fields[3] = str(int(minweeks) * 7)
                            if maxweeks:
                                fields[4] = str(int(maxweeks) * 7)
                            if warnweeks:
                                fields[5] = str(int(warnweeks) * 7)
                            line = ':'.join(fields)
                            lines.append('%s\n' % line)
                    with open(self.SHADOWFILE, 'w+') as f:
                        f.writelines(lines)
                    rc = 0
                except Exception as err:
                    self.module.fail_json(msg="failed to update users password: %s" % to_native(err))

        return (rc, out, err)

    def user_info(self):
        info = super(SunOS, self).user_info()
        if info:
            info += self._user_attr_info()
        return info

    def _user_attr_info(self):
        info = [''] * 3
        with open(self.USER_ATTR, 'r') as file_handler:
            for line in file_handler:
                lines = line.strip().split('::::')
                if lines[0] == self.name:
                    tmp = dict(x.split('=') for x in lines[1].split(';'))
                    info[0] = tmp.get('profiles', '')
                    info[1] = tmp.get('auths', '')
                    info[2] = tmp.get('roles', '')
        return info


class DarwinUser(User):
    """
    This is a Darwin macOS User manipulation class.
    Main differences are that Darwin:-
      - Handles accounts in a database managed by dscl(1)
      - Has no useradd/groupadd
      - Does not create home directories
      - User password must be cleartext
      - UID must be given
      - System users must ben under 500

    This overrides the following methods from the generic class:-
      - user_exists()
      - create_user()
      - remove_user()
      - modify_user()
    """
    platform = 'Darwin'
    distribution = None
    SHADOWFILE = None

    dscl_directory = '.'

    fields = [
        ('comment', 'RealName'),
        ('home', 'NFSHomeDirectory'),
        ('shell', 'UserShell'),
        ('uid', 'UniqueID'),
        ('group', 'PrimaryGroupID'),
        ('hidden', 'IsHidden'),
    ]

    def __init__(self, module):

        super(DarwinUser, self).__init__(module)

        # make the user hidden if option is set or defer to system option
        if self.hidden is None:
            if self.system:
                self.hidden = 1
        elif self.hidden:
            self.hidden = 1
        else:
            self.hidden = 0

        # add hidden to processing if set
        if self.hidden is not None:
            self.fields.append(('hidden', 'IsHidden'))

    def _get_dscl(self):
        return [self.module.get_bin_path('dscl', True), self.dscl_directory]

    def _list_user_groups(self):
        cmd = self._get_dscl()
        cmd += ['-search', '/Groups', 'GroupMembership', self.name]
        (rc, out, err) = self.execute_command(cmd, obey_checkmode=False)
        groups = []
        for line in out.splitlines():
            if line.startswith(' ') or line.startswith(')'):
                continue
            groups.append(line.split()[0])
        return groups

    def _get_user_property(self, property):
        """Return user PROPERTY as given my dscl(1) read or None if not found."""
        cmd = self._get_dscl()
        cmd += ['-read', '/Users/%s' % self.name, property]
        (rc, out, err) = self.execute_command(cmd, obey_checkmode=False)
        if rc != 0:
            return None
        # from dscl(1)
        # if property contains embedded spaces, the list will instead be
        # displayed one entry per line, starting on the line after the key.
        lines = out.splitlines()
        # sys.stderr.write('*** |%s| %s -> %s\n' %  (property, out, lines))
        if len(lines) == 1:
            return lines[0].split(': ')[1]
        if len(lines) > 2:
            return '\n'.join([lines[1].strip()] + lines[2:])
        if len(lines) == 2:
            return lines[1].strip()
        return None

    def _get_next_uid(self, system=None):
        """
        Return the next available uid. If system=True, then
        uid should be below of 500, if possible.
        """
        cmd = self._get_dscl()
        cmd += ['-list', '/Users', 'UniqueID']
        (rc, out, err) = self.execute_command(cmd, obey_checkmode=False)
        if rc != 0:
            self.module.fail_json(
                msg="Unable to get the next available uid",
                rc=rc,
                out=out,
                err=err
            )

        max_uid = 0
        max_system_uid = 0
        for line in out.splitlines():
            current_uid = int(line.split(' ')[-1])
            if max_uid < current_uid:
                max_uid = current_uid
            if max_system_uid < current_uid and current_uid < 500:
                max_system_uid = current_uid

        if system and (0 < max_system_uid < 499):
            return max_system_uid + 1
        return max_uid + 1

    def _change_user_password(self):
        """Change password for SELF.NAME against SELF.PASSWORD.

        Please note that password must be cleartext.
        """
        # some documentation on how is stored passwords on OSX:
        # http://null-byte.wonderhowto.com/how-to/hack-mac-os-x-lion-passwords-0130036/
        # http://pastebin.com/RYqxi7Ca
        # on OSX 10.8+ hash is SALTED-SHA512-PBKDF2
        # https://passlib.readthedocs.io/en/stable/lib/passlib.hash.pbkdf2_digest.html
        # https://gist.github.com/nueh/8252572
        cmd = self._get_dscl()
        if self.password:
            cmd += ['-passwd', '/Users/%s' % self.name, self.password]
        else:
            cmd += ['-create', '/Users/%s' % self.name, 'Password', '*']
        (rc, out, err) = self.execute_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Error when changing password', err=err, out=out, rc=rc)
        return (rc, out, err)

    def _make_group_numerical(self):
        """Convert SELF.GROUP to is stringed numerical value suitable for dscl."""
        if self.group is None:
            self.group = 'nogroup'
        try:
            self.group = grp.getgrnam(self.group).gr_gid
        except KeyError:
            self.module.fail_json(msg='Group "%s" not found. Try to create it first using "group" module.' % self.group)
        # We need to pass a string to dscl
        self.group = str(self.group)

    def __modify_group(self, group, action):
        """Add or remove SELF.NAME to or from GROUP depending on ACTION.
        ACTION can be 'add' or 'remove' otherwise 'remove' is assumed. """
        if action == 'add':
            option = '-a'
        else:
            option = '-d'
        cmd = ['dseditgroup', '-o', 'edit', option, self.name, '-t', 'user', group]
        (rc, out, err) = self.execute_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Cannot %s user "%s" to group "%s".'
                                      % (action, self.name, group), err=err, out=out, rc=rc)
        return (rc, out, err)

    def _modify_group(self):
        """Add or remove SELF.NAME to or from GROUP depending on ACTION.
        ACTION can be 'add' or 'remove' otherwise 'remove' is assumed. """

        rc = 0
        out = ''
        err = ''
        changed = False

        current = set(self._list_user_groups())
        if self.groups is not None:
            target = self.get_groups_set(names_only=True)
        else:
            target = set([])

        if self.append is False:
            for remove in current - target:
                (_rc, _out, _err) = self.__modify_group(remove, 'delete')
                rc += rc
                out += _out
                err += _err
                changed = True

        for add in target - current:
            (_rc, _out, _err) = self.__modify_group(add, 'add')
            rc += _rc
            out += _out
            err += _err
            changed = True

        return (rc, out, err, changed)

    def _update_system_user(self):
        """Hide or show user on login window according SELF.SYSTEM.

        Returns 0 if a change has been made, None otherwise."""

        plist_file = '/Library/Preferences/com.apple.loginwindow.plist'

        # http://support.apple.com/kb/HT5017?viewlocale=en_US
        cmd = ['defaults', 'read', plist_file, 'HiddenUsersList']
        (rc, out, err) = self.execute_command(cmd, obey_checkmode=False)
        # returned value is
        # (
        #   "_userA",
        #   "_UserB",
        #   userc
        # )
        hidden_users = []
        for x in out.splitlines()[1:-1]:
            try:
                x = x.split('"')[1]
            except IndexError:
                x = x.strip()
            hidden_users.append(x)

        if self.system:
            if self.name not in hidden_users:
                cmd = ['defaults', 'write', plist_file, 'HiddenUsersList', '-array-add', self.name]
                (rc, out, err) = self.execute_command(cmd)
                if rc != 0:
                    self.module.fail_json(msg='Cannot user "%s" to hidden user list.' % self.name, err=err, out=out, rc=rc)
                return 0
        else:
            if self.name in hidden_users:
                del (hidden_users[hidden_users.index(self.name)])

                cmd = ['defaults', 'write', plist_file, 'HiddenUsersList', '-array'] + hidden_users
                (rc, out, err) = self.execute_command(cmd)
                if rc != 0:
                    self.module.fail_json(msg='Cannot remove user "%s" from hidden user list.' % self.name, err=err, out=out, rc=rc)
                return 0

    def user_exists(self):
        """Check is SELF.NAME is a known user on the system."""
        cmd = self._get_dscl()
        cmd += ['-read', '/Users/%s' % self.name, 'UniqueID']
        (rc, out, err) = self.execute_command(cmd, obey_checkmode=False)
        return rc == 0

    def remove_user(self):
        """Delete SELF.NAME. If SELF.FORCE is true, remove its home directory."""
        info = self.user_info()

        cmd = self._get_dscl()
        cmd += ['-delete', '/Users/%s' % self.name]
        (rc, out, err) = self.execute_command(cmd)

        if rc != 0:
            self.module.fail_json(msg='Cannot delete user "%s".' % self.name, err=err, out=out, rc=rc)

        if self.force:
            if os.path.exists(info[5]):
                shutil.rmtree(info[5])
                out += "Removed %s" % info[5]

        return (rc, out, err)

    def create_user(self, command_name='dscl'):
        cmd = self._get_dscl()
        cmd += ['-create', '/Users/%s' % self.name]
        (rc, out, err) = self.execute_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Cannot create user "%s".' % self.name, err=err, out=out, rc=rc)

        # Make the Gecos (alias display name) default to username
        if self.comment is None:
            self.comment = self.name

        # Make user group default to 'staff'
        if self.group is None:
            self.group = 'staff'

        self._make_group_numerical()
        if self.uid is None:
            self.uid = str(self._get_next_uid(self.system))

        # Homedir is not created by default
        if self.create_home:
            if self.home is None:
                self.home = '/Users/%s' % self.name
            if not self.module.check_mode:
                if not os.path.exists(self.home):
                    os.makedirs(self.home)
                self.chown_homedir(int(self.uid), int(self.group), self.home)

        # dscl sets shell to /usr/bin/false when UserShell is not specified
        # so set the shell to /bin/bash when the user is not a system user
        if not self.system and self.shell is None:
            self.shell = '/bin/bash'

        for field in self.fields:
            if field[0] in self.__dict__ and self.__dict__[field[0]]:

                cmd = self._get_dscl()
                cmd += ['-create', '/Users/%s' % self.name, field[1], self.__dict__[field[0]]]
                (rc, _out, _err) = self.execute_command(cmd)
                if rc != 0:
                    self.module.fail_json(msg='Cannot add property "%s" to user "%s".' % (field[0], self.name), err=err, out=out, rc=rc)

                out += _out
                err += _err
                if rc != 0:
                    return (rc, _out, _err)

        (rc, _out, _err) = self._change_user_password()
        out += _out
        err += _err

        self._update_system_user()
        # here we don't care about change status since it is a creation,
        # thus changed is always true.
        if self.groups:
            (rc, _out, _err, changed) = self._modify_group()
            out += _out
            err += _err
        return (rc, out, err)

    def modify_user(self):
        changed = None
        out = ''
        err = ''

        if self.group:
            self._make_group_numerical()

        for field in self.fields:
            if field[0] in self.__dict__ and self.__dict__[field[0]]:
                current = self._get_user_property(field[1])
                if current is None or current != to_text(self.__dict__[field[0]]):
                    cmd = self._get_dscl()
                    cmd += ['-create', '/Users/%s' % self.name, field[1], self.__dict__[field[0]]]
                    (rc, _out, _err) = self.execute_command(cmd)
                    if rc != 0:
                        self.module.fail_json(
                            msg='Cannot update property "%s" for user "%s".'
                                % (field[0], self.name), err=err, out=out, rc=rc)
                    changed = rc
                    out += _out
                    err += _err
        if self.update_password == 'always' and self.password is not None:
            (rc, _out, _err) = self._change_user_password()
            out += _out
            err += _err
            changed = rc

        if self.groups:
            (rc, _out, _err, _changed) = self._modify_group()
            out += _out
            err += _err

            if _changed is True:
                changed = rc

        rc = self._update_system_user()
        if rc == 0:
            changed = rc

        return (changed, out, err)


class AIX(User):
    """
    This is a AIX User manipulation class.

    This overrides the following methods from the generic class:-
      - create_user()
      - remove_user()
      - modify_user()
      - parse_shadow_file()
    """

    platform = 'AIX'
    distribution = None
    SHADOWFILE = '/etc/security/passwd'

    def remove_user(self):
        cmd = [self.module.get_bin_path('userdel', True)]
        if self.remove:
            cmd.append('-r')
        cmd.append(self.name)

        return self.execute_command(cmd)

    def create_user_useradd(self, command_name='useradd'):
        cmd = [self.module.get_bin_path(command_name, True)]

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            cmd.append('-g')
            cmd.append(self.group)

        if self.groups is not None and len(self.groups):
            groups = self.get_groups_set()
            cmd.append('-G')
            cmd.append(','.join(groups))

        if self.comment is not None:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.create_home:
            cmd.append('-m')

            if self.skeleton is not None:
                cmd.append('-k')
                cmd.append(self.skeleton)

            if self.umask is not None:
                cmd.append('-K')
                cmd.append('UMASK=' + self.umask)

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)
        if self.uid_min is not None:
            cmd.append('-K')
            cmd.append('UID_MIN=' + str(self.uid_min))

        if self.uid_max is not None:
            cmd.append('-K')
            cmd.append('UID_MAX=' + str(self.uid_max))

        cmd.append(self.name)
        (rc, out, err) = self.execute_command(cmd)

        # set password with chpasswd
        if self.password is not None:
            cmd = []
            cmd.append(self.module.get_bin_path('chpasswd', True))
            cmd.append('-e')
            cmd.append('-c')
            self.execute_command(cmd, data="%s:%s" % (self.name, self.password))

        return (rc, out, err)

    def modify_user_usermod(self):
        cmd = [self.module.get_bin_path('usermod', True)]
        info = self.user_info()

        if self.uid is not None and info[2] != int(self.uid):
            cmd.append('-u')
            cmd.append(self.uid)

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            ginfo = self.group_info(self.group)
            if info[3] != ginfo[2]:
                cmd.append('-g')
                cmd.append(self.group)

        if self.groups is not None:
            current_groups = self.user_group_membership()
            groups_need_mod = False
            groups = []

            if self.groups == '':
                if current_groups and not self.append:
                    groups_need_mod = True
            else:
                groups = self.get_groups_set(names_only=True)
                group_diff = set(current_groups).symmetric_difference(groups)

                if group_diff:
                    if self.append:
                        for g in groups:
                            if g in group_diff:
                                groups_need_mod = True
                                break
                    else:
                        groups_need_mod = True

            if groups_need_mod:
                cmd.append('-G')
                cmd.append(','.join(groups))

        if self.comment is not None and info[4] != self.comment:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None and info[5] != self.home:
            if self.move_home:
                cmd.append('-m')
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None and info[6] != self.shell:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.inactive is not None:
            cmd.append('-f')
            cmd.append(self.inactive)

        # skip if no changes to be made
        if len(cmd) == 1:
            (rc, out, err) = (None, '', '')
        else:
            cmd.append(self.name)
            (rc, out, err) = self.execute_command(cmd)

        # set password with chpasswd
        if self.update_password == 'always' and self.password is not None and info[1] != self.password:
            cmd = []
            cmd.append(self.module.get_bin_path('chpasswd', True))
            cmd.append('-e')
            cmd.append('-c')
            (rc2, out2, err2) = self.execute_command(cmd, data="%s:%s" % (self.name, self.password))
        else:
            (rc2, out2, err2) = (None, '', '')

        if rc is not None:
            return (rc, out + out2, err + err2)
        else:
            return (rc2, out + out2, err + err2)

    def parse_shadow_file(self):
        """Example AIX shadowfile data:
        nobody:
                password = *

        operator1:
                password = {ssha512}06$xxxxxxxxxxxx....
                lastupdate = 1549558094

        test1:
                password = *
                lastupdate = 1553695126

        """

        b_name = to_bytes(self.name)
        b_passwd = b''
        b_expires = b''
        if os.path.exists(self.SHADOWFILE) and os.access(self.SHADOWFILE, os.R_OK):
            with open(self.SHADOWFILE, 'rb') as bf:
                b_lines = bf.readlines()

            b_passwd_line = b''
            b_expires_line = b''
            try:
                for index, b_line in enumerate(b_lines):
                    # Get password and lastupdate lines which come after the username
                    if b_line.startswith(b'%s:' % b_name):
                        b_passwd_line = b_lines[index + 1]
                        b_expires_line = b_lines[index + 2]
                        break

                # Sanity check the lines because sometimes both are not present
                if b' = ' in b_passwd_line:
                    b_passwd = b_passwd_line.split(b' = ', 1)[-1].strip()

                if b' = ' in b_expires_line:
                    b_expires = b_expires_line.split(b' = ', 1)[-1].strip()

            except IndexError:
                self.module.fail_json(msg='Failed to parse shadow file %s' % self.SHADOWFILE)

        passwd = to_native(b_passwd)
        expires = to_native(b_expires) or -1
        return passwd, expires


class HPUX(User):
    """
    This is a HP-UX User manipulation class.

    This overrides the following methods from the generic class:-
      - create_user()
      - remove_user()
      - modify_user()
    """

    platform = 'HP-UX'
    distribution = None
    SHADOWFILE = '/etc/shadow'

    def create_user(self):
        cmd = ['/usr/sam/lbin/useradd.sam']

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            cmd.append('-g')
            cmd.append(self.group)

        if self.groups is not None and len(self.groups):
            groups = self.get_groups_set()
            cmd.append('-G')
            cmd.append(','.join(groups))

        if self.comment is not None:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            cmd.append('-d')
            cmd.append(self.home)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.password is not None:
            cmd.append('-p')
            cmd.append(self.password)

        if self.create_home:
            cmd.append('-m')
        else:
            cmd.append('-M')

        if self.system:
            cmd.append('-r')

        cmd.append(self.name)
        return self.execute_command(cmd)

    def remove_user(self):
        cmd = ['/usr/sam/lbin/userdel.sam']
        if self.force:
            cmd.append('-F')
        if self.remove:
            cmd.append('-r')
        cmd.append(self.name)
        return self.execute_command(cmd)

    def modify_user(self):
        cmd = ['/usr/sam/lbin/usermod.sam']
        info = self.user_info()

        if self.uid is not None and info[2] != int(self.uid):
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            ginfo = self.group_info(self.group)
            if info[3] != ginfo[2]:
                cmd.append('-g')
                cmd.append(self.group)

        if self.groups is not None:
            current_groups = self.user_group_membership()
            groups_need_mod = False
            groups = []

            if self.groups == '':
                if current_groups and not self.append:
                    groups_need_mod = True
            else:
                groups = self.get_groups_set(remove_existing=False, names_only=True)
                group_diff = set(current_groups).symmetric_difference(groups)

                if group_diff:
                    if self.append:
                        for g in groups:
                            if g in group_diff:
                                groups_need_mod = True
                                break
                    else:
                        groups_need_mod = True

            if groups_need_mod:
                cmd.append('-G')
                new_groups = groups
                if self.append:
                    new_groups = groups | set(current_groups)
                cmd.append(','.join(new_groups))

        if self.comment is not None and info[4] != self.comment:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None and info[5] != self.home:
            cmd.append('-d')
            cmd.append(self.home)
            if self.move_home:
                cmd.append('-m')

        if self.shell is not None and info[6] != self.shell:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.update_password == 'always' and self.password is not None and info[1] != self.password:
            cmd.append('-F')
            cmd.append('-p')
            cmd.append(self.password)

        # skip if no changes to be made
        if len(cmd) == 1:
            return (None, '', '')

        cmd.append(self.name)
        return self.execute_command(cmd)


class BusyBox(User):
    """
    This is the BusyBox class for use on systems that have adduser, deluser,
    and delgroup commands. It overrides the following methods:
        - create_user()
        - remove_user()
        - modify_user()
    """

    def create_user(self):
        cmd = [self.module.get_bin_path('adduser', True)]

        cmd.append('-D')

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg='Group {0} does not exist'.format(self.group))
            cmd.append('-G')
            cmd.append(self.group)

        if self.comment is not None:
            cmd.append('-g')
            cmd.append(self.comment)

        if self.home is not None:
            cmd.append('-h')
            cmd.append(self.home)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if not self.create_home:
            cmd.append('-H')

        if self.skeleton is not None:
            cmd.append('-k')
            cmd.append(self.skeleton)

        if self.umask is not None:
            cmd.append('-K')
            cmd.append('UMASK=' + self.umask)

        if self.system:
            cmd.append('-S')

        if self.uid_min is not None:
            cmd.append('-K')
            cmd.append('UID_MIN=' + str(self.uid_min))

        if self.uid_max is not None:
            cmd.append('-K')
            cmd.append('UID_MAX=' + str(self.uid_max))

        cmd.append(self.name)

        rc, out, err = self.execute_command(cmd)

        if rc is not None and rc != 0:
            self.module.fail_json(name=self.name, msg=err, rc=rc)

        if self.password is not None:
            cmd = [self.module.get_bin_path('chpasswd', True)]
            cmd.append('--encrypted')
            data = '{name}:{password}'.format(name=self.name, password=self.password)
            rc, out, err = self.execute_command(cmd, data=data)

            if rc is not None and rc != 0:
                self.module.fail_json(name=self.name, msg=err, rc=rc)

        # Add to additional groups
        if self.groups is not None and len(self.groups):
            groups = self.get_groups_set()
            add_cmd_bin = self.module.get_bin_path('adduser', True)
            for group in groups:
                cmd = [add_cmd_bin, self.name, group]
                rc, out, err = self.execute_command(cmd)
                if rc is not None and rc != 0:
                    self.module.fail_json(name=self.name, msg=err, rc=rc)

        return rc, out, err

    def remove_user(self):

        cmd = [
            self.module.get_bin_path('deluser', True),
            self.name
        ]

        if self.remove:
            cmd.append('--remove-home')

        return self.execute_command(cmd)

    def modify_user(self):
        current_groups = self.user_group_membership()
        groups = []
        rc = None
        out = ''
        err = ''
        info = self.user_info()
        add_cmd_bin = self.module.get_bin_path('adduser', True)
        remove_cmd_bin = self.module.get_bin_path('delgroup', True)

        # Manage group membership
        if self.groups is not None and len(self.groups):
            groups = self.get_groups_set()
            group_diff = set(current_groups).symmetric_difference(groups)

            if group_diff:
                for g in groups:
                    if g in group_diff:
                        add_cmd = [add_cmd_bin, self.name, g]
                        rc, out, err = self.execute_command(add_cmd)
                        if rc is not None and rc != 0:
                            self.module.fail_json(name=self.name, msg=err, rc=rc)

                for g in group_diff:
                    if g not in groups and not self.append:
                        remove_cmd = [remove_cmd_bin, self.name, g]
                        rc, out, err = self.execute_command(remove_cmd)
                        if rc is not None and rc != 0:
                            self.module.fail_json(name=self.name, msg=err, rc=rc)

        # Manage password
        if self.update_password == 'always' and self.password is not None and info[1] != self.password:
            cmd = [self.module.get_bin_path('chpasswd', True)]
            cmd.append('--encrypted')
            data = '{name}:{password}'.format(name=self.name, password=self.password)
            rc, out, err = self.execute_command(cmd, data=data)

            if rc is not None and rc != 0:
                self.module.fail_json(name=self.name, msg=err, rc=rc)

        return rc, out, err


class Alpine(BusyBox):
    """
    This is the Alpine User manipulation class. It inherits the BusyBox class
    behaviors such as using adduser and deluser commands.
    """
    platform = 'Linux'
    distribution = 'Alpine'


class Buildroot(BusyBox):
    platform = 'Linux'
    distribution = 'Buildroot'


def main():
    ssh_defaults = dict(
        bits=0,
        type='rsa',
        passphrase=None,
        comment='ansible-generated on %s' % socket.gethostname()
    )
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            name=dict(type='str', required=True, aliases=['user']),
            uid=dict(type='int'),
            non_unique=dict(type='bool', default=False),
            group=dict(type='str'),
            groups=dict(type='list', elements='str'),
            comment=dict(type='str'),
            home=dict(type='path'),
            shell=dict(type='path'),
            password=dict(type='str', no_log=True),
            login_class=dict(type='str'),
            password_expire_max=dict(type='int', no_log=False),
            password_expire_min=dict(type='int', no_log=False),
            password_expire_warn=dict(type='int', no_log=False),
            # following options are specific to macOS
            hidden=dict(type='bool'),
            # following options are specific to selinux
            seuser=dict(type='str'),
            # following options are specific to userdel
            force=dict(type='bool', default=False),
            remove=dict(type='bool', default=False),
            # following options are specific to useradd
            create_home=dict(type='bool', default=True, aliases=['createhome']),
            skeleton=dict(type='str'),
            system=dict(type='bool', default=False),
            # following options are specific to usermod
            move_home=dict(type='bool', default=False),
            append=dict(type='bool', default=False),
            # following are specific to ssh key generation
            generate_ssh_key=dict(type='bool'),
            ssh_key_bits=dict(type='int', default=ssh_defaults['bits']),
            ssh_key_type=dict(type='str', default=ssh_defaults['type']),
            ssh_key_file=dict(type='path'),
            ssh_key_comment=dict(type='str', default=ssh_defaults['comment']),
            ssh_key_passphrase=dict(type='str', no_log=True),
            update_password=dict(type='str', default='always', choices=['always', 'on_create'], no_log=False),
            expires=dict(type='float'),
            password_lock=dict(type='bool', no_log=False),
            local=dict(type='bool'),
            profile=dict(type='str'),
            authorization=dict(type='str'),
            role=dict(type='str'),
            umask=dict(type='str'),
            password_expire_account_disable=dict(type='int', no_log=False),
            uid_min=dict(type='int'),
            uid_max=dict(type='int'),
        ),
        supports_check_mode=True,
    )

    user = User(module)
    user.check_password_encrypted()

    module.debug('User instantiated - platform %s' % user.platform)
    if user.distribution:
        module.debug('User instantiated - distribution %s' % user.distribution)

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = user.name
    result['state'] = user.state
    if user.state == 'absent':
        if user.user_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = user.remove_user()
            if rc != 0:
                module.fail_json(name=user.name, msg=err, rc=rc)
            result['force'] = user.force
            result['remove'] = user.remove
    elif user.state == 'present':
        if not user.user_exists():
            if module.check_mode:
                module.exit_json(changed=True)

            # Check to see if the provided home path contains parent directories
            # that do not exist.
            path_needs_parents = False
            if user.home and user.create_home:
                parent = os.path.dirname(user.home)
                if not os.path.isdir(parent):
                    path_needs_parents = True

            (rc, out, err) = user.create_user()

            # If the home path had parent directories that needed to be created,
            # make sure file permissions are correct in the created home directory.
            if path_needs_parents:
                info = user.user_info()
                if info is not False:
                    user.chown_homedir(info[2], info[3], user.home)

            if module.check_mode:
                result['system'] = user.name
            else:
                result['system'] = user.system
                result['create_home'] = user.create_home
        else:
            # modify user (note: this function is check mode aware)
            (rc, out, err) = user.modify_user()
            result['append'] = user.append
            result['move_home'] = user.move_home
        if rc is not None and rc != 0:
            module.fail_json(name=user.name, msg=err, rc=rc)
        if user.password is not None:
            result['password'] = 'NOT_LOGGING_PASSWORD'

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True
    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    if user.user_exists() and user.state == 'present':
        info = user.user_info()
        if info is False:
            result['msg'] = "failed to look up user name: %s" % user.name
            result['failed'] = True
        result['uid'] = info[2]
        result['group'] = info[3]
        result['comment'] = info[4]
        result['home'] = info[5]
        result['shell'] = info[6]
        if user.groups is not None:
            result['groups'] = user.groups

        # handle missing homedirs
        info = user.user_info()
        if user.home is None:
            user.home = info[5]
        if not os.path.exists(user.home) and user.create_home:
            if not module.check_mode:
                user.create_homedir(user.home)
                user.chown_homedir(info[2], info[3], user.home)
            result['changed'] = True

        # deal with ssh key
        if user.sshkeygen:
            # generate ssh key (note: this function is check mode aware)
            (rc, out, err) = user.ssh_key_gen()
            if rc is not None and rc != 0:
                module.fail_json(name=user.name, msg=err, rc=rc)
            if rc == 0:
                result['changed'] = True
            (rc, out, err) = user.ssh_key_fingerprint()
            if rc == 0:
                result['ssh_fingerprint'] = out.strip()
            else:
                result['ssh_fingerprint'] = err.strip()
            result['ssh_key_file'] = user.get_ssh_key_path()
            result['ssh_public_key'] = user.get_ssh_public_key()

        (rc, out, err) = user.set_password_expire()
        if rc is None:
            pass  # target state reached, nothing to do
        else:
            if rc != 0:
                module.fail_json(name=user.name, msg=err, rc=rc)
            else:
                result['changed'] = True

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
