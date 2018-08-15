# (c) 2014, Matt Martz <matt@sivel.net>
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


class ModuleDocFragment(object):

    # Standard files documentation fragment

    # Note: mode is overridden by the copy and template modules so if you change the description
    # here, you should also change it there.
    DOCUMENTATION = """
options:
  mode:
    description:
      - "Mode the file or directory should be. For those used to I(/usr/bin/chmod) remember that modes are actually octal numbers.
        You must either specify the leading zero so that Ansible's YAML parser knows it is an octal
        number (like C(0644) or C(01777)) or quote it (like C('644') or C('0644') so Ansible
        receives a string and can do its own conversion from string into number.  Giving Ansible a number
        without following one of these rules will end up with a decimal number which will have unexpected results.
        As of version 1.8, the mode may be specified as a symbolic mode (for example, C(u+rwx) or C(u=rw,g=r,o=r))."
  owner:
    description:
      - Name of the user that should own the file/directory, as would be fed to I(chown).
  group:
    description:
      - Name of the group that should own the file/directory, as would be fed to I(chown).
  seuser:
    description:
      - User part of SELinux file context. Will default to system policy, if
        applicable. If set to C(_default), it will use the C(user) portion of the
        policy if available.
  serole:
    description:
      - Role part of SELinux file context, C(_default) feature works as for I(seuser).
  setype:
    description:
      - Type part of SELinux file context, C(_default) feature works as for I(seuser).
  selevel:
    description:
      - Level part of the SELinux file context. This is the MLS/MCS attribute,
        sometimes known as the C(range). C(_default) feature works as for
        I(seuser).
    default: "s0"
  unsafe_writes:
    description:
      -  Normally this module uses atomic operations to prevent data corruption or inconsistent reads from the target files,
         sometimes systems are configured or just broken in ways that prevent this. One example are docker mounted files,
         they cannot be updated atomically and can only be done in an unsafe manner.
      -  This boolean option allows ansible to fall back to unsafe methods of updating files for those cases in which you do
         not have any other choice. Be aware that this is subject to race conditions and can lead to data corruption.
    type: bool
    default: 'no'
    version_added: "2.2"
  attributes:
    description:
      - Attributes the file or directory should have. To get supported flags look at the man page for I(chattr) on the target system.
        This string should contain the attributes in the same order as the one displayed by I(lsattr).
      - C(=) operator is assumed as default, otherwise C(+) or C(-) operators need to be included in the string.
    aliases: ['attr']
    version_added: "2.3"
"""
