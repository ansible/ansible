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
        do not exist. If C(file), the file will NOT be created if it does not
        exist, see the M(copy) or M(template) module if you want that behavior.
        If C(link), the symbolic link will be created or changed. Use C(hard)
        for hardlinks. If C(absent), directories will be recursively deleted,
        and files or symlinks will be unlinked. If C(touch) (new in 1.4), an empty file will
        be created if the c(path) does not exist, while an existing file or
        directory will receive updated file access and modification times (similar
        to the way `touch` works from the command line).
    required: false
    default: file
    choices: [ file, link, directory, hard, touch, absent ]
  src:
    required: false
    default: null
    choices: []
    description:
      - path of the file to link to (applies only to C(state= link or hard)). Will accept absolute,
        relative and nonexisting (with C(force)) paths. Relative paths are not expanded.
  recurse:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    version_added: "1.1"
    description:
      - recursively set the specified file attributes (applies only to state=directory)
"""
