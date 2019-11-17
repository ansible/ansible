# (c) 2019, Red Hat, Inc.
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

from __future__ import (absolute_import, division, print_function)

from ansible.errors import AnsibleError
from ansible.utils.vars import combine_vars


def add_host(host_info, inventory):
    '''
    Helper function to add a new host to inventory based on a task result.
    '''

    if host_info:
        host_name = host_info.get('host_name')

        # Check if host in inventory, add if not
        if host_name in inventory.hosts:
            return None

        inventory.add_host(host_name, 'all')
        new_host = inventory.get_host(host_name)

        # Set/update the vars for this host
        new_host.vars = combine_vars(new_host.get_vars(), host_info.get('host_vars', dict()))

        new_groups = host_info.get('groups', [])
        for group_name in new_groups:
            if group_name not in inventory.groups:
                group_name = inventory.add_group(group_name)
            new_group = inventory.groups[group_name]
            new_group.add_host(new_host)

        # reconcile inventory, ensures inventory rules are followed
        inventory.reconcile_inventory()

        return new_host

def add_group(host_name, result_item, inventory):
    '''
    Helper function to add a group (if it does not exist), and to assign the
    specified host to that group.
    '''

    changed = False

    # the host here is from the executor side, which means it was a
    # serialized/cloned copy and we'll need to look up the proper
    # host object from the master inventory
    real_host = inventory.hosts.get(host_name)
    if real_host is None:
        if host_name == inventory.localhost.name:
            real_host = inventory.localhost
        else:
            raise AnsibleError('%s cannot be matched in inventory' % host_name)

    group_name = result_item.get('add_group')
    parent_group_names = result_item.get('parent_groups', [])

    if group_name not in inventory.groups:
        group_name = inventory.add_group(group_name)

    for name in parent_group_names:
        if name not in inventory.groups:
            # create the new group and add it to inventory
            inventory.add_group(name)
            changed = True

    group = inventory.groups[group_name]
    for parent_group_name in parent_group_names:
        parent_group = inventory.groups[parent_group_name]
        parent_group.add_child_group(group)

    if real_host.name not in group.get_hosts():
        group.add_host(real_host)
        changed = True

    if group_name not in real_host.get_groups():
        real_host.add_group(group)
        changed = True

    if changed:
        inventory.reconcile_inventory()

    return changed
