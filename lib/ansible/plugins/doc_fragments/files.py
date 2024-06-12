# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


class ModuleDocFragment(object):

    # Standard files documentation fragment

    # Note: mode is overridden by the copy and template modules so if you change the description
    # here, you should also change it there.
    DOCUMENTATION = r'''
options:
  mode:
    description:
    - The permissions the resulting filesystem object should have.
    - For those used to C(/usr/bin/chmod) remember that modes are actually octal numbers.
      You must give Ansible enough information to parse them correctly.
      For consistent results, quote octal numbers (for example, V('644') or V('1777')) so Ansible receives
      a string and can do its own conversion from string into number.
      Adding a leading zero (for example, V(0755)) works sometimes, but can fail in loops and some other circumstances.
    - Giving Ansible a number without following either of these rules will end up with a decimal
      number which will have unexpected results.
    - As of Ansible 1.8, the mode may be specified as a symbolic mode (for example, V(u+rwx) or
      V(u=rw,g=r,o=r)).
    - If O(mode) is not specified and the destination filesystem object B(does not) exist, the default C(umask) on the system will be used
      when setting the mode for the newly created filesystem object.
    - If O(mode) is not specified and the destination filesystem object B(does) exist, the mode of the existing filesystem object will be used.
    - Specifying O(mode) is the best way to ensure filesystem objects are created with the correct permissions.
      See CVE-2020-1736 for further details.
    type: raw
  owner:
    description:
    - Name of the user that should own the filesystem object, as would be fed to C(chown).
    - When left unspecified, it uses the current user unless you are root, in which
      case it can preserve the previous ownership.
    - Specifying a numeric username will be assumed to be a user ID and not a username. Avoid numeric usernames to avoid this confusion.

    type: str
  group:
    description:
    - Name of the group that should own the filesystem object, as would be fed to C(chown).
    - When left unspecified, it uses the current group of the current user unless you are root,
      in which case it can preserve the previous ownership.
    type: str
  seuser:
    description:
    - The user part of the SELinux filesystem object context.
    - By default it uses the V(system) policy, where applicable.
    - When set to V(_default), it will use the C(user) portion of the policy if available.
    type: str
  serole:
    description:
    - The role part of the SELinux filesystem object context.
    - When set to V(_default), it will use the C(role) portion of the policy if available.
    type: str
  setype:
    description:
    - The type part of the SELinux filesystem object context.
    - When set to V(_default), it will use the C(type) portion of the policy if available.
    type: str
  selevel:
    description:
    - The level part of the SELinux filesystem object context.
    - This is the MLS/MCS attribute, sometimes known as the C(range).
    - When set to V(_default), it will use the C(level) portion of the policy if available.
    type: str
  unsafe_writes:
    description:
    - Influence when to use atomic operation to prevent data corruption or inconsistent reads from the target filesystem object.
    - By default this module uses atomic operations to prevent data corruption or inconsistent reads from the target filesystem objects,
      but sometimes systems are configured or just broken in ways that prevent this. One example is docker mounted filesystem objects,
      which cannot be updated atomically from inside the container and can only be written in an unsafe manner.
    - This option allows Ansible to fall back to unsafe methods of updating filesystem objects when atomic operations fail
      (however, it doesn't force Ansible to perform unsafe writes).
    - IMPORTANT! Unsafe writes are subject to race conditions and can lead to data corruption.
    type: bool
    default: no
    version_added: '2.2'
  attributes:
    description:
    - The attributes the resulting filesystem object should have.
    - To get supported flags look at the man page for C(chattr) on the target system.
    - This string should contain the attributes in the same order as the one displayed by C(lsattr).
    - The C(=) operator is assumed as default, otherwise C(+) or C(-) operators need to be included in the string.
    type: str
    aliases: [ attr ]
    version_added: '2.3'
'''
