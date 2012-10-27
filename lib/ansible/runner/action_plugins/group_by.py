# Copyright 2012, Jeroen Hoekx <jeroen@hoekx.be>
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

import ansible

from ansible.errors import AnsibleError as ae
from ansible.runner.return_data import ReturnData
from ansible.utils import parse_kv, template

class ActionModule(object):
    ''' Create inventory groups based on variables '''

    ### We need to be able to modify the inventory
    BYPASS_HOST_LOOP = True

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject):
        args = parse_kv(template(self.runner.basedir, module_args, inject))
        if not 'var' in args:
            raise ae("'var' is a required argument.")
        variable = args['var']
        if 'prefix' in args:
            prefix = "%s-"%(args['prefix'])
        else:
            prefix = ""

        inventory = self.runner.inventory

        result = {'changed': False}

        ### find all returned groups
        groups = {}
        for _,host in self.runner.host_set:
            data = self.runner.setup_cache[host]
            if variable in data:
                group_name = "%s%s"%(prefix,data[variable].replace(' ','-'))
                if group_name not in groups:
                    groups[group_name] = []
                groups[group_name].append(host)

        result[variable] = groups

        ### add to inventory
        for group, hosts in groups.items():
            inv_group = inventory.get_group(group)
            if not inv_group:
                inv_group = ansible.inventory.Group(name=group)
                inventory.add_group(inv_group)
            for host in hosts:
                inv_host = inventory.get_host(host)
                if not inv_host:
                    inv_host = ansible.inventory.Host(name=host)
                if inv_group not in inv_host.get_groups():
                    result['changed'] = True
                    inv_group.add_host(inv_host)

        return ReturnData(conn=conn, comm_ok=True, result=result)
