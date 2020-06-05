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

from ansible.errors import AnsibleActionFail
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.six import string_types
from ansible.plugins.action import ActionBase
from ansible.parsing.utils.addresses import parse_address
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars

display = Display()


class ActionModule(ActionBase):
    ''' Create inventory hosts and groups in the memory inventory'''

    # We need to be able to modify the inventory
    BYPASS_HOST_LOOP = True
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):

        self._supports_check_mode = True

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        args = self._task.args
        raw = args.pop('_raw_params', {})
        if isinstance(raw, Mapping):
            # TODO: create 'conflict' detection in base class to deal with repeats and aliases and warn user
            args = combine_vars(raw, args)
        else:
            raise AnsibleActionFail('Invalid raw parameters passed, requires a dictonary/mapping got a  %s' % type(raw))

        # Parse out any hostname:port patterns
        new_name = args.get('name', args.get('hostname', args.get('host', None)))
        if new_name is None:
            raise AnsibleActionFail('name, host or hostname needs to be provided')

        display.vv("creating host via 'add_host': hostname=%s" % new_name)

        try:
            name, port = parse_address(new_name, allow_ranges=False)
        except Exception:
            # not a parsable hostname, but might still be usable
            name = new_name
            port = None

        if port:
            args['ansible_ssh_port'] = port

        groups = args.get('groupname', args.get('groups', args.get('group', '')))
        # add it to the group if that was specified
        new_groups = []
        if groups:
            if isinstance(groups, list):
                group_list = groups
            elif isinstance(groups, string_types):
                group_list = groups.split(",")
            else:
                raise AnsibleActionFail("Groups must be specified as a list.", obj=self._task)

            for group_name in group_list:
                if group_name not in new_groups:
                    new_groups.append(group_name.strip())

        # Add any variables to the new_host
        host_vars = dict()
        special_args = frozenset(('name', 'hostname', 'groupname', 'groups'))
        for k in args.keys():
            if k not in special_args:
                host_vars[k] = args[k]

        result['changed'] = False
        result['add_host'] = dict(host_name=name, groups=new_groups, host_vars=host_vars)
        return result
