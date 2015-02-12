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

from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    ''' Create inventory hosts and groups in the memory inventory'''

    ### We need to be able to modify the inventory
    BYPASS_HOST_LOOP = True
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=dict()):

        # FIXME: is this necessary in v2?
        #if self.runner.noop_on_check(inject):
        #    return ReturnData(conn=conn, comm_ok=True, result=dict(skipped=True, msg='check mode not supported for this module'))

        # Parse out any hostname:port patterns
        new_name = self._task.args.get('name', self._task.args.get('hostname', None))
        #vv("creating host via 'add_host': hostname=%s" % new_name)

        if ":" in new_name:
            new_name, new_port = new_name.split(":")
            self._task.args['ansible_ssh_port'] = new_port

        groups = self._task.args.get('groupname', self._task.args.get('groups', self._task.args.get('group', ''))) 
        # add it to the group if that was specified
        new_groups = []
        if groups:
            for group_name in groups.split(","):
                if group_name not in new_groups:
                    new_groups.append(group_name.strip())

        # Add any variables to the new_host
        host_vars = dict()
        for k in self._task.args.keys():
            if not k in [ 'name', 'hostname', 'groupname', 'groups' ]:
                host_vars[k] = self._task.args[k] 

        return dict(changed=True, add_host=dict(host_name=new_name, groups=new_groups, host_vars=host_vars))


