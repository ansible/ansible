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

from __future__ import annotations

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils.six import string_types
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject
from ansible.playbook.delegatable import Delegatable
from ansible.playbook.role.definition import RoleDefinition
from ansible.module_utils.common.text.converters import to_native


__all__ = ['RoleInclude']


class RoleInclude(RoleDefinition, Delegatable):

    """
    A derivative of RoleDefinition, used by playbook code when a role
    is included for execution in a play.
    """

    def __init__(self, play=None, role_basedir=None, variable_manager=None, loader=None, collection_list=None, extra_spec=None):
        super(RoleInclude, self).__init__(play=play, role_basedir=role_basedir, variable_manager=variable_manager,
                                          loader=loader, collection_list=collection_list, extra_spec=extra_spec)

    @staticmethod
    def load(data, play, current_role_path=None, parent_role=None, variable_manager=None, loader=None, collection_list=None, extra_spec=None):

        if not (isinstance(data, string_types) or isinstance(data, dict) or isinstance(data, AnsibleBaseYAMLObject)):
            raise AnsibleParserError("Invalid role definition: %s" % to_native(data))

        if isinstance(data, string_types) and ',' in data:
            raise AnsibleError("Invalid old style role requirement: %s" % data)

        ri = RoleInclude(
            play=play, role_basedir=current_role_path, variable_manager=variable_manager, loader=loader, collection_list=collection_list, extra_spec=extra_spec
        )
        return ri.load_data(data, variable_manager=variable_manager, loader=loader)
