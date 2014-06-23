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
  path:
    description:
      - 'path to the file being managed.  Aliases: I(dest), I(name)'
    required: true
    default: []
    aliases: ['dest', 'name'] 
  state:
    description:
      - If C(directory), all immediate subdirectories will be created if they
        do not exist, since 1.7 they will be created with the supplied permissions.
        If C(file), the file will NOT be created if it does not exist, see the M(copy)
        or M(template) module if you want that behavior.  If C(link), the symbolic
        link will be created or changed. Use C(hard) for hardlinks. If C(absent),
        directories will be recursively deleted, and files or symlinks will be unlinked.
        If C(touch) (new in 1.4), an empty file will be created if the c(path) does not
        exist, while an existing file or directory will receive updated file access and
        modification times (similar to the way `touch` works from the command line).
    required: false
    default: file
    choices: [ file, link, directory, hard, touch, absent ]
  mode:
    required: false
    default: null
    choices: []
    description:
      - mode the file or directory should be, such as 0644 as would be fed to I(chmod)
  owner:
    required: false
    default: null
    choices: []
    description:
      - name of the user that should own the file/directory, as would be fed to I(chown)
  group:
    required: false
    default: null
    choices: []
    description:
      - name of the group that should own the file/directory, as would be fed to I(chown)
  src:
    required: false
    default: null
    choices: []
    description:
      - path of the file to link to (applies only to C(state=link)). Will accept absolute,
        relative and nonexisting paths. Relative paths are not expanded.
  seuser:
    required: false
    default: null
    choices: []
    description:
      - user part of SELinux file context. Will default to system policy, if
        applicable. If set to C(_default), it will use the C(user) portion of the
        policy if available
  serole:
    required: false
    default: null
    choices: []
    description:
      - role part of SELinux file context, C(_default) feature works as for I(seuser).
  setype:
    required: false
    default: null
    choices: []
    description:
      - type part of SELinux file context, C(_default) feature works as for I(seuser).
  selevel:
    required: false
    default: "s0"
    choices: []
    description:
      - level part of the SELinux file context. This is the MLS/MCS attribute,
        sometimes known as the C(range). C(_default) feature works as for
        I(seuser).
  recurse:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    version_added: "1.1"
    description:
      - recursively set the specified file attributes (applies only to state=directory)
  force:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    description:
      - 'force the creation of the symlinks in two cases: the source file does 
        not exist (but will appear later); the destination exists and is a file (so, we need to unlink the
        "path" file and create symlink to the "src" file in place of it).'
"""
