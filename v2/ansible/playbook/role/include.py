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

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.playbook.attribute import Attribute, FieldAttribute
from ansible.playbook.role.definition import RoleDefinition


__all__ = ['RoleInclude']


class RoleInclude(RoleDefinition):

    """
    FIXME: docstring
    """

    def __init__(self, role_basedir=None):
        super(RoleInclude, self).__init__(role_basedir=role_basedir)

    @staticmethod
    def load(data, current_role_path=None, parent_role=None, variable_manager=None, loader=None):
        assert isinstance(data, string_types) or isinstance(data, dict)

        ri = RoleInclude(role_basedir=current_role_path)
        return ri.load_data(data, variable_manager=variable_manager, loader=loader)

