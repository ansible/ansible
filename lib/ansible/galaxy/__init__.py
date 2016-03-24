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

from ansible.compat.six import string_types

from ansible.errors import AnsibleError

#      default_readme_template
#      default_meta_template


class Galaxy(object):
    ''' Keeps global galaxy info '''

    def __init__(self, options):

        self.options = options
        roles_paths = getattr(self.options, 'roles_path', [])
        if isinstance(roles_paths, string_types):
            self.roles_paths = [os.path.expanduser(roles_path) for roles_path in roles_paths.split(os.pathsep)]

        self.roles =  {}

        # load data path for resource usage
        this_dir, this_filename = os.path.split(__file__)
        self.DATA_PATH = os.path.join(this_dir, "data")

        self._default_readme = None
        self._default_meta = None
        self._default_test = None
        self._default_travis = None

    @property
    def default_readme(self):
        if self._default_readme is None:
            self._default_readme = self._str_from_data_file('readme')
        return self._default_readme

    @property
    def default_meta(self):
        if self._default_meta is None:
            self._default_meta = self._str_from_data_file('metadata_template.j2')
        return self._default_meta

    @property
    def default_test(self):
        if self._default_test is None:
            self._default_test = self._str_from_data_file('test_playbook.j2')
        return self._default_test

    @property
    def default_travis(self):
        if self._default_travis is None:
            self._default_travis = self._str_from_data_file('travis.j2')
        return self._default_travis

    def add_role(self, role):
        self.roles[role.name] = role

    def remove_role(self, role_name):
        del self.roles[role_name]

    def _str_from_data_file(self, filename):
        myfile = os.path.join(self.DATA_PATH, filename)
        try:
            return open(myfile).read()
        except Exception as e:
            raise AnsibleError("Could not open %s: %s" % (filename, str(e)))
