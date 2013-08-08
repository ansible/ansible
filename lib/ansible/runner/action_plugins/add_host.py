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

import ansible

from ansible.callbacks import vv
from ansible.errors import AnsibleError as ae
from ansible.runner.return_data import ReturnData
from ansible.utils import parse_kv
from ansible.inventory.host import Host
from ansible.inventory.group import Group

class ActionModule(object):
    ''' Create inventory hosts and groups in the memory inventory'''

    ### We need to be able to modify the inventory
    BYPASS_HOST_LOOP = True
    NEEDS_TMPPATH = False

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):

        if self.runner.check:
            return ReturnData(conn=conn, comm_ok=True, result=dict(skipped=True, msg='check mode not supported for this module'))

        args = {}
        if complex_args:
            args.update(complex_args)
        args.update(parse_kv(module_args))
        if not 'hostname' in args and not 'name' in args:
            raise ae("'name' is a required argument.")

        result = {}

        # Parse out any hostname:port patterns
        new_name = args.get('name', args.get('hostname', None))
        vv("creating host via 'add_host': hostname=%s" % new_name)

        if ":" in new_name:
            new_name, new_port = new_name.split(":")
            args['ansible_ssh_port'] = new_port
        
        # create host and get inventory    
        new_host = Host(new_name)
        inventory = self.runner.inventory
        
        # Add any variables to the new_host
        for k in args.keys():
            if not k in [ 'name', 'hostname', 'groupname', 'groups' ]:
                new_host.set_variable(k, args[k]) 
                
        
        # add the new host to the 'all' group
        allgroup = inventory.get_group('all')
        allgroup.add_host(new_host)
       
        groupnames = args.get('groupname', args.get('groups', '')) 
        # add it to the group if that was specified
        if groupnames != '':
            for group_name in groupnames.split(","):
                if not inventory.get_group(group_name):
                    new_group = Group(group_name)
                    inventory.add_group(new_group)
                grp = inventory.get_group(group_name)
                grp.add_host(new_host)
                vv("added host to group via add_host module: %s" % group_name)
            result['new_groups'] = groupnames.split(",")
            
        result['new_host'] = new_name
        
        return ReturnData(conn=conn, comm_ok=True, result=result)



