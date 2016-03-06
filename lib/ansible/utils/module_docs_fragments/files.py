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
    DOCUMENTATION = """
options:
  mode:
    required: false
    default: null
    description:
      - mode the file or directory should be. For those used to I(/usr/bin/chmod) remember that modes are actually octal numbers (like 0644). Leaving off the leading zero will likely have unexpected results. As of version 1.8, the mode may be specified as a symbolic mode (for example, C(u+rwx) or C(u=rw,g=r,o=r)).
  owner:
    required: false
    default: null
    description:
      - name of the user that should own the file/directory, as would be fed to I(chown)
  group:
    required: false
    default: null
    description:
      - name of the group that should own the file/directory, as would be fed to I(chown)
  seuser:
    required: false
    default: null
    description:
      - user part of SELinux file context. Will default to system policy, if
        applicable. If set to C(_default), it will use the C(user) portion of the
        policy if available
  serole:
    required: false
    default: null
    description:
      - role part of SELinux file context, C(_default) feature works as for I(seuser).
  setype:
    required: false
    default: null
    description:
      - type part of SELinux file context, C(_default) feature works as for I(seuser).
  selevel:
    required: false
    default: "s0"
    description:
      - level part of the SELinux file context. This is the MLS/MCS attribute,
        sometimes known as the C(range). C(_default) feature works as for
        I(seuser).
"""
