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

from six import iteritems, string_types

import os

from ansible.errors import AnsibleError
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleMapping
from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.playbook.base import Base


__all__ = ['RoleDefinition']


class RoleDefinition(Base):

    _role = FieldAttribute(isa='string')

    def __init__(self):
        self._role_path   = None
        self._role_params = dict()
        super(RoleDefinition, self).__init__()

    def __repr__(self):
        return 'ROLEDEF: ' + self._attributes.get('role', '<no name set>')

    @staticmethod
    def load(data, loader=None):
        raise AnsibleError("not implemented")

    def munge(self, ds):

        assert isinstance(ds, dict) or isinstance(ds, string_types)

        # we create a new data structure here, using the same
        # object used internally by the YAML parsing code so we
        # can preserve file:line:column information if it exists
        new_ds = AnsibleMapping()
        if isinstance(ds, AnsibleBaseYAMLObject):
            new_ds.copy_position_info(ds)

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

        # save the original ds for use later
        self._ds = ds

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
        if not role_name:
            raise AnsibleError('role definitions must contain a role name', obj=ds)

        return role_name

    def _load_role_path(self, role_name):
        '''
        the 'role', as specified in the ds (or as a bare string), can either
        be a simple name or a full path. If it is a full path, we use the
        basename as the role name, otherwise we take the name as-given and
        append it to the default role path
        '''

        # FIXME: this should use unfrackpath once the utils code has been sorted out
        role_path = os.path.normpath(role_name)
        if self._loader.path_exists(role_path):
            role_name = os.path.basename(role_name)
            return (role_name, role_path)
        else:
            # FIXME: this should search in the configured roles path
            for path in ('./roles', '/etc/ansible/roles'):
                role_path = os.path.join(path, role_name)
                if self._loader.path_exists(role_path):
                    return (role_name, role_path)

        # FIXME: make the parser smart about list/string entries
        #        in the yaml so the error line/file can be reported
        #        here
        raise AnsibleError("the role '%s' was not found" % role_name)

    def _split_role_params(self, ds):
        '''
        Splits any random role params off from the role spec and store
        them in a dictionary of params for parsing later
        '''

        role_def = dict()
        role_params = dict()
        for (key, value) in iteritems(ds):
            # use the list of FieldAttribute values to determine what is and is not
            # an extra parameter for this role (or sub-class of this role)
            if key not in [attr_name for (attr_name, attr_value) in self._get_base_attributes().iteritems()]:
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
