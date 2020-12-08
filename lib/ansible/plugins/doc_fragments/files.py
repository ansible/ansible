# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment

    # Note: mode is overridden by the copy and template modules so if you change the description
    # here, you should also change it there.
    DOCUMENTATION = r'''
options:
  mode:
    description:
    - The permissions the resulting file or directory should have.
    - For those used to I(/usr/bin/chmod) remember that modes are actually octal numbers.
      You must either add a leading zero so that Ansible's YAML parser knows it is an octal number
      (like C(0644) or C(01777)) or quote it (like C('644') or C('1777')) so Ansible receives
      a string and can do its own conversion from string into number.
    - Giving Ansible a number without following one of these rules will end up with a decimal
      number which will have unexpected results.
    - As of Ansible 1.8, the mode may be specified as a symbolic mode (for example, C(u+rwx) or
      C(u=rw,g=r,o=r)).
    - If C(mode) is not specified and the destination file B(does not) exist, the default C(umask) on the system will be used
      when setting the mode for the newly created file.
    - If C(mode) is not specified and the destination file B(does) exist, the mode of the existing file will be used.
    - Specifying C(mode) is the best way to ensure files are created with the correct permissions.
      See CVE-2020-1736 for further details.
    type: raw
  owner:
    description:
    - Name of the user that should own the file/directory, as would be fed to I(chown).
    type: str
  group:
    description:
    - Name of the group that should own the file/directory, as would be fed to I(chown).
    type: str
  seuser:
    description:
    - The user part of the SELinux file context.
    - By default it uses the C(system) policy, where applicable.
    - When set to C(_default), it will use the C(user) portion of the policy if available.
    type: str
  serole:
    description:
    - The role part of the SELinux file context.
    - When set to C(_default), it will use the C(role) portion of the policy if available.
    type: str
  setype:
    description:
    - The type part of the SELinux file context.
    - When set to C(_default), it will use the C(type) portion of the policy if available.
    type: str
  selevel:
    description:
    - The level part of the SELinux file context.
    - This is the MLS/MCS attribute, sometimes known as the C(range).
    - When set to C(_default), it will use the C(level) portion of the policy if available.
    type: str
  unsafe_writes:
    description:
    - Influence when to use atomic operation to prevent data corruption or inconsistent reads from the target file.
    - By default this module uses atomic operations to prevent data corruption or inconsistent reads from the target files,
      but sometimes systems are configured or just broken in ways that prevent this. One example is docker mounted files,
      which cannot be updated atomically from inside the container and can only be written in an unsafe manner.
    - This option allows Ansible to fall back to unsafe methods of updating files when atomic operations fail
      (however, it doesn't force Ansible to perform unsafe writes).
    - IMPORTANT! Unsafe writes are subject to race conditions and can lead to data corruption.
    type: bool
    default: no
    version_added: '2.2'
  attributes:
    description:
    - The attributes the resulting file or directory should have.
    - To get supported flags look at the man page for I(chattr) on the target system.
    - This string should contain the attributes in the same order as the one displayed by I(lsattr).
    - The C(=) operator is assumed as default, otherwise C(+) or C(-) operators need to be included in the string.
    type: str
    aliases: [ attr ]
    version_added: '2.3'
'''
