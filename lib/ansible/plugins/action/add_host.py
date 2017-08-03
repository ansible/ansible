# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright 2012, Seth Vidal <skvidal@fedoraproject.org>
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

from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.plugins.action import ActionBase
from ansible.parsing.utils.addresses import parse_address

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):
    ''' Create inventory hosts and groups in the memory inventory'''

    # We need to be able to modify the inventory
    BYPASS_HOST_LOOP = True
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):

        self._supports_check_mode = True

        result = super(ActionModule, self).run(tmp, task_vars)

        # Parse out any hostname:port patterns
        new_name = self._task.args.get('name', self._task.args.get('hostname', self._task.args.get('host', None)))
        display.vv("creating host via 'add_host': hostname=%s" % new_name)

        try:
            name, port = parse_address(new_name, allow_ranges=False)
        except:
            # not a parsable hostname, but might still be usable
            name = new_name
            port = None

        if port:
            self._task.args['ansible_ssh_port'] = port

        groups = self._task.args.get('groupname', self._task.args.get('groups', self._task.args.get('group', '')))
        # add it to the group if that was specified
        new_groups = []
        if groups:
            if isinstance(groups, list):
                group_list = groups
            elif isinstance(groups, string_types):
                group_list = groups.split(",")
            else:
                raise AnsibleError("Groups must be specified as a list.", obj=self._task)

            for group_name in group_list:
                if group_name not in new_groups:
                    new_groups.append(group_name.strip())

        # Add any variables to the new_host
        host_vars = dict()
        special_args = frozenset(('name', 'hostname', 'groupname', 'groups'))
        for k in self._task.args.keys():
            if k not in special_args:
                host_vars[k] = self._task.args[k]

        result['changed'] = True
        result['add_host'] = dict(host_name=name, groups=new_groups, host_vars=host_vars)
        return result
