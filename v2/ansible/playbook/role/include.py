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

    _tags = FieldAttribute(isa='list', default=[])
    _when = FieldAttribute(isa='list', default=[])

    def __init__(self):
        super(RoleInclude, self).__init__()

    @staticmethod
    def load(data, parent_role=None, loader=None):
        assert isinstance(data, string_types) or isinstance(data, dict)

        ri = RoleInclude()
        return ri.load_data(data, loader=loader)

