########################################################################
#
# (C) 2015, Brian Coca <bcoca@ansible.com>
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
#
########################################################################
''' This manages remote shared Ansible objects, mainly roles'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types

#      default_readme_template
#      default_meta_template


class Galaxy(object):
    ''' Keeps global galaxy info '''

    def __init__(self, options):

        self.options = options
        # self.options.roles_path needs to be a list and will be by default
        roles_path = getattr(self.options, 'roles_path', [])
        # cli option handling is responsible for making roles_path a list
        self.roles_paths = roles_path

        self.roles = {}

        # load data path for resource usage
        this_dir, this_filename = os.path.split(__file__)
        type_path = getattr(self.options, 'role_type', "default")
        self.DATA_PATH = os.path.join(this_dir, 'data', type_path)

    @property
    def default_role_skeleton_path(self):
        return self.DATA_PATH

    def add_role(self, role):
        self.roles[role.name] = role

    def remove_role(self, role_name):
        del self.roles[role_name]
