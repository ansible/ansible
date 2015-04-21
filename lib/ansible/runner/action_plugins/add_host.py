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
from ansible.utils import parse_kv, combine_vars
from ansible.inventory.host import Host
from ansible.inventory.group import Group

class ActionModule(object):
    ''' Create inventory hosts and groups in the memory inventory'''

    ### We need to be able to modify the inventory
    BYPASS_HOST_LOOP = True
    TRANSFERS_FILES = False

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):

        if self.runner.noop_on_check(inject):
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

        # redefine inventory and get group "all"
        inventory = self.runner.inventory
        allgroup = inventory.get_group('all')

        # check if host in cache, add if not
        if new_name in inventory._hosts_cache:
            new_host = inventory._hosts_cache[new_name]
        else:
            new_host = Host(new_name)
            # only groups can be added directly to inventory
            inventory._hosts_cache[new_name] = new_host
            allgroup.add_host(new_host)

        groupnames = args.get('groupname', args.get('groups', args.get('group', '')))
        # add it to the group if that was specified
        if groupnames:
            for group_name in groupnames.split(","):
                group_name = group_name.strip()
                if not inventory.get_group(group_name):
                    new_group = Group(group_name)
                    inventory.add_group(new_group)
                    new_group.vars = inventory.get_group_variables(group_name, vault_password=inventory._vault_password)
                grp = inventory.get_group(group_name)
                grp.add_host(new_host)

                # add this host to the group cache
                if inventory._groups_list is not None:
                    if group_name in inventory._groups_list:
                        if new_host.name not in inventory._groups_list[group_name]:
                            inventory._groups_list[group_name].append(new_host.name)

                vv("added host to group via add_host module: %s" % group_name)
            result['new_groups'] = groupnames.split(",")


        # actually load host vars
        new_host.vars = combine_vars(new_host.vars, inventory.get_host_variables(new_name, update_cached=True, vault_password=inventory._vault_password))

        # Add any passed variables to the new_host
        for k in args.keys():
            if not k in [ 'name', 'hostname', 'groupname', 'groups' ]:
                new_host.set_variable(k, args[k])

        result['new_host'] = new_name

        # clear pattern caching completely since it's unpredictable what
        # patterns may have referenced the group
        inventory.clear_pattern_cache()

        return ReturnData(conn=conn, comm_ok=True, result=result)



