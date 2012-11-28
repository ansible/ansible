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
from ansible.utils import parse_kv, template
from ansible.inventory.host import Host
from ansible.inventory.group import Group

class ActionModule(object):
    ''' Create inventory hosts and groups in the memory inventory'''

    ### We need to be able to modify the inventory
    BYPASS_HOST_LOOP = True
    NEEDS_TMPPATH = False

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject):
        args = parse_kv(module_args)
        if not 'hostname' in args:
            raise ae("'hostname' is a required argument.")

        vv("created 'add_host' ActionModule: hostname=%s"%(args['hostname']))


        result = {'changed': True}

        new_host = Host(args['hostname'])
        inventory = self.runner.inventory
        
        # add the new host to the 'all' group
        allgroup = inventory.get_group('all')
        allgroup.add_host(new_host)
        result['changed'] = True
        
        # add it to the group if that was specified
        if 'groupname' in args:
            if not inventory.get_group(args['groupname']):
                new_group = Group(args['groupname'])
                inventory.add_group(new_group)
                
            ngobj = inventory.get_group(args['groupname'])
            ngobj.add_host(new_host)
            vv("created 'add_host' ActionModule: groupname=%s"%(args['groupname']))
            result['new_group'] = args['groupname']
            
        result['new_host'] = args['hostname']
        
        return ReturnData(conn=conn, comm_ok=True, result=result)



