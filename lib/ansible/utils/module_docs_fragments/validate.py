# (c) 2014, Joel <jjshoe@gmail.com>
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
    DOCUMENTATION = """
options:
  validate:
    description:
      - A validation command to run before copying into place. The path of the file to
        validate is passed in via the required argument '%s', just like the visudo example below.
        The command is passed securely, as a result shell features like expansion and pipes don't work.
    required: false
    default: ""
"""
