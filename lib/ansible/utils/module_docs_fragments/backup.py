# Copyright (c) 2015 Ansible, Inc
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

    # Standard documentation fragment
    DOCUMENTATION = '''
options:
    backup:
        description:
          - Create a backup file including the timestamp information so you can get
            the original file back if you somehow clobbered it incorrectly.
        required: false
        choices: [ "yes", "no" ]
        default: "no"
'''
