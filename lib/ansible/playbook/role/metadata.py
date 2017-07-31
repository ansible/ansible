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

from ansible.errors import AnsibleParserError, AnsibleError
from ansible.module_utils.six import iteritems, string_types
from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.helpers import load_list_of_roles
from ansible.playbook.role.include import RoleInclude
from ansible.playbook.role.requirement import RoleRequirement

__all__ = ['RoleMetadata']


class RoleMetadata(Base):
    '''
    This class wraps the parsing and validation of the optional metadata
    within each Role (meta/main.yml).
    '''

    _allow_duplicates = FieldAttribute(isa='bool', default=False)
    _dependencies = FieldAttribute(isa='list', default=[])
    _galaxy_info = FieldAttribute(isa='GalaxyInfo')

    def __init__(self, owner=None):
        self._owner = owner
        super(RoleMetadata, self).__init__()

    @staticmethod
    def load(data, owner, variable_manager=None, loader=None):
        '''
        Returns a new RoleMetadata object based on the datastructure passed in.
        '''

        if not isinstance(data, dict):
            raise AnsibleParserError("the 'meta/main.yml' for role %s is not a dictionary" % owner.get_name())

        m = RoleMetadata(owner=owner).load_data(data, variable_manager=variable_manager, loader=loader)
        return m

    def _load_dependencies(self, attr, ds):
        '''
        This is a helper loading function for the dependencies list,
        which returns a list of RoleInclude objects
        '''

        roles = []
        if ds:
            if not isinstance(ds, list):
                raise AnsibleParserError("Expected role dependencies to be a list.", obj=self._ds)

            for role_def in ds:
                if isinstance(role_def, string_types) or 'role' in role_def or 'name' in role_def:
                    roles.append(role_def)
                    continue
                try:
                    # role_def is new style: { src: 'galaxy.role,version,name', other_vars: "here" }
                    def_parsed = RoleRequirement.role_yaml_parse(role_def)
                    if def_parsed.get('name'):
                        role_def['name'] = def_parsed['name']
                    roles.append(role_def)
                except AnsibleError as exc:
                    raise AnsibleParserError(str(exc), obj=role_def, orig_exc=exc)

        current_role_path = None
        if self._owner:
            current_role_path = os.path.dirname(self._owner._role_path)

        try:
            return load_list_of_roles(roles, play=self._owner._play, current_role_path=current_role_path, variable_manager=self._variable_manager,
                                      loader=self._loader)
        except AssertionError as e:
            raise AnsibleParserError("A malformed list of role dependencies was encountered.", obj=self._ds, orig_exc=e)

    def _load_galaxy_info(self, attr, ds):
        '''
        This is a helper loading function for the galaxy info entry
        in the metadata, which returns a GalaxyInfo object rather than
        a simple dictionary.
        '''

        return ds

    def serialize(self):
        return dict(
            allow_duplicates=self._allow_duplicates,
            dependencies=self._dependencies,
        )

    def deserialize(self, data):
        setattr(self, 'allow_duplicates', data.get('allow_duplicates', False))
        setattr(self, 'dependencies', data.get('dependencies', []))
