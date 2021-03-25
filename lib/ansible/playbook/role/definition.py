# (c) 2014 Michael DeHaan, <michael@ansible.com>
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

import os

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils.six import iteritems, string_types
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleMapping
from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.collectionsearch import CollectionSearch
from ansible.playbook.conditional import Conditional
from ansible.playbook.taggable import Taggable
from ansible.template import Templar
from ansible.utils.collection_loader import AnsibleCollectionRef
from ansible.utils.collection_loader._collection_finder import _get_collection_role_path
from ansible.utils.path import unfrackpath
from ansible.utils.display import Display
from ansible.utils.role_finder import AnsibleRoleFinder


__all__ = ['RoleDefinition']

display = Display()


class RoleDefinition(Base, Conditional, Taggable, CollectionSearch):

    _role = FieldAttribute(isa='string')

    def __init__(self, play=None, role_basedir=None, variable_manager=None, loader=None, collection_list=None):

        super(RoleDefinition, self).__init__()

        self._play = play
        self._variable_manager = variable_manager
        self._loader = loader

        self._role_path = None
        self._role_collection = None
        self._role_basedir = role_basedir
        self._role_params = dict()
        self._collection_list = collection_list

    # def __repr__(self):
    #     return 'ROLEDEF: ' + self._attributes.get('role', '<no name set>')

    @staticmethod
    def load(data, variable_manager=None, loader=None):
        raise AnsibleError("not implemented")

    def preprocess_data(self, ds):
        # role names that are simply numbers can be parsed by PyYAML
        # as integers even when quoted, so turn it into a string type
        if isinstance(ds, int):
            ds = "%s" % ds

        if not isinstance(ds, dict) and not isinstance(ds, string_types) and not isinstance(ds, AnsibleBaseYAMLObject):
            raise AnsibleAssertionError()

        if isinstance(ds, dict):
            ds = super(RoleDefinition, self).preprocess_data(ds)

        # save the original ds for use later
        self._ds = ds

        # we create a new data structure here, using the same
        # object used internally by the YAML parsing code so we
        # can preserve file:line:column information if it exists
        new_ds = AnsibleMapping()
        if isinstance(ds, AnsibleBaseYAMLObject):
            new_ds.ansible_pos = ds.ansible_pos

        # first we pull the role name out of the data structure,
        # and then use that to determine the role path (which may
        # result in a new role name, if it was a file path)
        role_name = self._load_role_name(ds)
        (role_name, role_path) = self._load_role_path(role_name)

        # next, we split the role params out from the valid role
        # attributes and update the new datastructure with that
        # result and the role name
        if isinstance(ds, dict):
            (new_role_def, role_params) = self._split_role_params(ds)
            new_ds.update(new_role_def)
            self._role_params = role_params

        # set the role name in the new ds
        new_ds['role'] = role_name

        # we store the role path internally
        self._role_path = role_path

        # and return the cleaned-up data structure
        return new_ds

    def _load_role_name(self, ds):
        '''
        Returns the role name (either the role: or name: field) from
        the role definition, or (when the role definition is a simple
        string), just that string
        '''

        if isinstance(ds, string_types):
            return ds

        role_name = ds.get('role', ds.get('name'))
        if not role_name or not isinstance(role_name, string_types):
            raise AnsibleError('role definitions must contain a role name', obj=ds)

        # if we have the required datastructures, and if the role_name
        # contains a variable, try and template it now
        if self._variable_manager:
            all_vars = self._variable_manager.get_vars(play=self._play)
            templar = Templar(loader=self._loader, variables=all_vars)
            role_name = templar.template(role_name)

        return role_name

    def _load_role_path(self, role_name):
        '''
        the 'role', as specified in the ds (or as a bare string), can either
        be a simple name or a full path. If it is a full path, we use the
        basename as the role name, otherwise we take the name as-given and
        append it to the default role path
        '''

        # create a templar class to template the dependency names, in
        # case they contain variables
        if self._variable_manager is not None:
            all_vars = self._variable_manager.get_vars(play=self._play)
        else:
            all_vars = dict()

        templar = Templar(loader=self._loader, variables=all_vars)
        finder = AnsibleRoleFinder(self._loader.get_basedir(), self._role_basedir, templar)

        result = finder.find_first(role_name, self._collection_list)
        if result:
            self._role_collection = result.collection_name
            return (result.role_name, result.role_path)

        searches = (self._collection_list or []) + finder.standard_role_search_paths
        raise AnsibleError("the role '%s' was not found in %s" % (role_name, ":".join(searches)), obj=self._ds)

    def _split_role_params(self, ds):
        '''
        Splits any random role params off from the role spec and store
        them in a dictionary of params for parsing later
        '''

        role_def = dict()
        role_params = dict()
        base_attribute_names = frozenset(self._valid_attrs.keys())
        for (key, value) in iteritems(ds):
            # use the list of FieldAttribute values to determine what is and is not
            # an extra parameter for this role (or sub-class of this role)
            # FIXME: hard-coded list of exception key names here corresponds to the
            #        connection fields in the Base class. There may need to be some
            #        other mechanism where we exclude certain kinds of field attributes,
            #        or make this list more automatic in some way so we don't have to
            #        remember to update it manually.
            if key not in base_attribute_names:
                # this key does not match a field attribute, so it must be a role param
                role_params[key] = value
            else:
                # this is a field attribute, so copy it over directly
                role_def[key] = value

        return (role_def, role_params)

    def get_role_params(self):
        return self._role_params.copy()

    def get_role_path(self):
        return self._role_path

    def get_name(self, include_role_fqcn=True):
        if include_role_fqcn:
            return '.'.join(x for x in (self._role_collection, self.role) if x)
        return self.role
