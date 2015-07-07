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

from ansible.callbacks import vv
from ansible.errors import AnsibleError as ae
from ansible.runner.return_data import ReturnData
from ansible.utils import parse_kv, check_conditional
import ansible.utils.template as template

class ActionModule(object):
    ''' Create inventory groups based on variables '''

    ### We need to be able to modify the inventory
    BYPASS_HOST_LOOP = True
    TRANSFERS_FILES = False

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):

        # the group_by module does not need to pay attention to check mode.
        # it always runs.

        # module_args and complex_args have already been templated for the first host.
        # Use them here only to check that a key argument is provided.
        args = {}
        if complex_args:
            args.update(complex_args)
        args.update(parse_kv(module_args))
        if not 'key' in args:
            raise ae("'key' is a required argument.")

        vv("created 'group_by' ActionModule: key=%s"%(args['key']))

        inventory = self.runner.inventory

        result = {'changed': False}

        ### find all groups
        groups = {}

        for host in self.runner.host_set:
            data = {}
            data.update(inject)
            data.update(inject['hostvars'][host])
            conds = self.runner.conditional
            if type(conds) != list:
                conds = [ conds ]
            next_host = False
            for cond in conds:
                if not check_conditional(cond, self.runner.basedir, data, fail_on_undefined=self.runner.error_on_undefined_vars):
                    next_host = True
                    break
            if next_host:
                continue

            # Template original module_args and complex_args from runner for each host.
            host_module_args = template.template(self.runner.basedir, self.runner.module_args, data)
            host_complex_args = template.template(self.runner.basedir, self.runner.complex_args, data)
            host_args  = {}
            if host_complex_args:
                host_args.update(host_complex_args)
            host_args.update(parse_kv(host_module_args))

            group_name = host_args['key']
            group_name = group_name.replace(' ','-')
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(host)

        result['groups'] = groups

        ### add to inventory
        for group, hosts in groups.items():
            inv_group = inventory.get_group(group)
            if not inv_group:
                inv_group = ansible.inventory.Group(name=group)
                inventory.add_group(inv_group)
                inventory.get_group('all').add_child_group(inv_group)
                inv_group.vars = inventory.get_group_variables(group, update_cached=False, vault_password=inventory._vault_password)
            for host in hosts:
                if host in self.runner.inventory._vars_per_host:
                    del self.runner.inventory._vars_per_host[host]
                inv_host = inventory.get_host(host)
                if not inv_host:
                    inv_host = ansible.inventory.Host(name=host)
                if inv_group not in inv_host.get_groups():
                    result['changed'] = True
                    inv_group.add_host(inv_host)

        return ReturnData(conn=conn, comm_ok=True, result=result)
