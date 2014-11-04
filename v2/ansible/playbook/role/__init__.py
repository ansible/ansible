# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from six import iteritems, string_types

import os

from hashlib import md5
from types import NoneType

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.parsing.yaml import DataLoader
from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.helpers import load_list_of_blocks
from ansible.playbook.role.include import RoleInclude
from ansible.playbook.role.metadata import RoleMetadata


__all__ = ['Role', 'ROLE_CACHE']


# The role cache is used to prevent re-loading roles, which
# may already exist. Keys into this cache are the MD5 hash
# of the role definition (for dictionary definitions, this
# will be based on the repr() of the dictionary object)
ROLE_CACHE = dict()


class Role:

    def __init__(self):
        self._role_name        = None
        self._role_path        = None
        self._role_params      = dict()
        self._loader           = None

        self._metadata         = None
        self._parents          = []
        self._dependencies     = []
        self._task_blocks      = []
        self._handler_blocks   = []
        self._default_vars     = dict()
        self._role_vars        = dict()
        
    def __repr__(self):
        return self.get_name()

    def get_name(self):
        return self._role_name

    @staticmethod
    def load(role_include, parent_role=None):
        # FIXME: add back in the role caching support
        try:
            r = Role()
            r._load_role_data(role_include, parent_role=parent_role)
        except RuntimeError:
            # FIXME: needs a better way to access the ds in the role include
            raise AnsibleError("A recursion loop was detected with the roles specified. Make sure child roles do not have dependencies on parent roles", obj=role_include._ds)
        return r

    def _load_role_data(self, role_include, parent_role=None):
        self._role_name   = role_include.role
        self._role_path   = role_include.get_role_path()
        self._role_params = role_include.get_role_params()
        self._loader      = role_include.get_loader()

        if parent_role:
            self.add_parent(parent_role)

        # load the role's files, if they exist
        metadata = self._load_role_yaml('meta')
        if metadata:
            self._metadata = RoleMetadata.load(metadata, owner=self, loader=self._loader)
            self._dependencies = self._load_dependencies()

        task_data = self._load_role_yaml('tasks')
        if task_data:
            self._task_blocks = load_list_of_blocks(task_data)

        handler_data = self._load_role_yaml('handlers')
        if handler_data:
            self._handler_blocks = load_list_of_blocks(handler_data)

        # vars and default vars are regular dictionaries
        self._role_vars    = self._load_role_yaml('vars')
        if not isinstance(self._role_vars, (dict, NoneType)):
            raise AnsibleParserError("The vars/main.yml file for role '%s' must contain a dictionary of variables" % self._role_name, obj=ds)

        self._default_vars = self._load_role_yaml('defaults')
        if not isinstance(self._default_vars, (dict, NoneType)):
            raise AnsibleParserError("The default/main.yml file for role '%s' must contain a dictionary of variables" % self._role_name, obj=ds)

    def _load_role_yaml(self, subdir):
        file_path = os.path.join(self._role_path, subdir)
        if self._loader.path_exists(file_path) and self._loader.is_directory(file_path):
            main_file = self._resolve_main(file_path)
            if self._loader.path_exists(main_file):
                return self._loader.load_from_file(main_file)
        return None

    def _resolve_main(self, basepath):
        ''' flexibly handle variations in main filenames '''
        possible_mains = (
            os.path.join(basepath, 'main.yml'),
            os.path.join(basepath, 'main.yaml'),
            os.path.join(basepath, 'main.json'),
            os.path.join(basepath, 'main'),
        )

        if sum([self._loader.is_file(x) for x in possible_mains]) > 1:
            raise AnsibleError("found multiple main files at %s, only one allowed" % (basepath))
        else:
            for m in possible_mains:
                if self._loader.is_file(m):
                    return m # exactly one main file
            return possible_mains[0] # zero mains (we still need to return something)

    def _load_dependencies(self):
        '''
        Recursively loads role dependencies from the metadata list of
        dependencies, if it exists
        '''

        deps = []
        if self._metadata:
            for role_include in self._metadata.dependencies:
                r = Role.load(role_include, parent_role=self)
                deps.append(r)

        return deps

    #------------------------------------------------------------------------------
    # other functions

    def add_parent(self, parent_role):
        ''' adds a role to the list of this roles parents '''
        assert isinstance(parent_role, Role)

        if parent_role not in self._parents:
            self._parents.append(parent_role)

    def get_parents(self):
        return self._parents

    # FIXME: not yet used
    #def get_variables(self):
    #    # returns the merged variables for this role, including
    #    # recursively merging those of all child roles
    #    return dict()

    def get_direct_dependencies(self):
        return self._dependencies[:]

    def get_all_dependencies(self):
        # returns a list built recursively, of all deps from
        # all child dependencies

        child_deps  = []
        direct_deps = self.get_direct_dependencies()

        for dep in direct_deps:
            dep_deps = dep.get_all_dependencies()
            for dep_dep in dep_deps:
                if dep_dep not in child_deps:
                    child_deps.append(dep_dep)

        return direct_deps + child_deps

