# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

#############################################
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

from itertools import chain

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.inventory.group import Group
from ansible.inventory.host import Host
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems, string_types
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars
from ansible.utils.path import basedir

display = Display()


class InventoryHostManager(object):
    """
    Manager for inventory host relatives
    """
    def host_populate_ancestors(self, host_name, additions=None):
        """
        :type host_name: str
        :type additions: list[str]
        """
        host = self.hosts[host_name]
        if additions is None:
            for group_name in host.groups:
                for ancestor_name in self.group_get_ancestors(group_name):
                    if ancestor_name not in host.groups:
                        host.groups.append(ancestor_name)
        else:
            for group_name in additions:
                if group_name not in host.groups:
                    host.groups.append(group_name)

    def host_add_group(self, host_name, group_name):
        """
        :type host_name: str
        :type group_name: str
        """
        self.host_populate_ancestors(host_name)
        if group_name not in self.hosts[host_name].groups:
            self.hosts[host_name].groups.append(group_name)

    def host_remove_group(self, host_name, group_name):
        """
        :type host_name: str
        :type group_name: str
        """
        # Remove references to a group and its ancestors from a host
        host = self.hosts[host_name]

        if group_name in host.groups:
            host.groups.remove(group_name)

        # Update ancestry
        for old_group in self.group_get_ancestors(group_name):
            if old_group.name != 'all':
                for child_group_name in host.groups:
                    if old_group in self.group_get_ancestors(child_group_name):
                        break
                    else:
                        self.host_remove_group(host_name, old_group.name)


class InventoryGroupManager(object):
    """
    Manager for inventory group relatives
    """

    def group_walk_relationship(self, group, rel, include_self=False, preserve_ordering=False):
        '''
        :type group: str
        :type rel: str
        :rtype: list[str] | set(str)

        Given `rel` that is an iterable property of Group,
        consitituting a directed acyclic graph among all groups,
        Returns a set of all groups in full tree
        A   B    C
        |  / |  /
        | /  | /
        D -> E
        |  /    vertical connections
        | /     are directed upward
        F
        Called with group F, returns set of (A, B, C, D, E)
        '''
        seen = set([])
        unprocessed = set(getattr(self.groups[group], rel))
        if include_self:
            unprocessed.add(group)
        if preserve_ordering:
            ordered = [group] if include_self else []
            ordered.extend(getattr(self.groups[group], rel))

        while unprocessed:
            seen.update(unprocessed)
            new_unprocessed = set([])

            for new_item in chain.from_iterable(getattr(self.groups[g], rel) for g in unprocessed):
                new_unprocessed.add(new_item)
                if preserve_ordering:
                    if new_item not in seen:
                        ordered.append(new_item)

            new_unprocessed.difference_update(seen)
            unprocessed = new_unprocessed

        if preserve_ordering:
            return ordered
        return seen

    def group_remove_host(self, group_name, host_name):
        """
        :type group_name: str
        :type host_name: str
        """
        group = self.groups[group_name]
        if host_name in group.host_names:
            group.hosts.remove(host_name)
            group._hosts.remove(host_name)
            self.group_clear_hosts_cache(group_name)

    def group_add_host(self, group_name, host_name):
        """
        :type group_name: str
        :type host_name: str
        """
        group = self.groups[group_name]
        if host_name not in group.host_names:
            group.hosts.append(host_name)
            group._hosts.add(host_name)
            self.group_clear_hosts_cache(group_name)

    def group_get_ancestors(self, group_name):
        """
        :type group_name: str
        :rtype: set(str)
        """
        return self.group_walk_relationship(group_name, 'parent_groups')

    def group_get_descendants(self, group_name, **kwargs):
        """
        :type group_name: str
        :rtype: list[str] | set(str)
        """
        return self.group_walk_relationship(group_name, 'child_groups', **kwargs)

    def group_add_child_group(self, group, parent):
        """
        :type group: str
        :type parent: str
        """

        if parent == group:
            raise Exception("can't add group to itself")

        # don't add if it's already there
        if group not in self.groups[parent].child_groups:
            # prepare list of group's new ancestors this edge creates
            start_ancestors = self.group_get_ancestors(group)
            new_ancestors = self.group_get_ancestors(parent)
            if group in new_ancestors:
                raise AnsibleError("Adding group '%s' as child to '%s' creates a recursive dependency loop." % (to_native(group), to_native(parent)))
            new_ancestors.add(parent)
            new_ancestors.difference_update(start_ancestors)
            self.groups[parent].child_groups.append(group)

            # update the depth of the child
            self.groups[group].depth = max([self.groups[parent].depth + 1, self.groups[group].depth])

            # update the depth of the grandchildren
            self.group_check_children_depth(group)

            # now add group to child's parent_groups list, but only if there
            # isn't already a group with the same name
            if parent not in self.groups[group].parent_groups:
                self.groups[group].parent_groups.append(parent)
                for h in self.group_get_hosts(group):
                    self.host_populate_ancestors(h, additions=new_ancestors)

            self.group_clear_hosts_cache(parent)

    def group_check_children_depth(self, group_name):
        """
        :type group_name: str
        """
        group = self.groups[group_name]
        depth = group.depth
        start_depth = group.depth  # group.depth could change over loop
        seen = set([])
        unprocessed = set(group.child_groups)

        while unprocessed:
            seen.update(unprocessed)
            depth += 1
            to_process = unprocessed.copy()
            unprocessed = set([])
            for i in to_process:
                g = self.groups[i]
                if g.depth < depth:
                    g.depth = depth
                    unprocessed.update(g.child_groups)
            if depth - start_depth > len(seen):
                raise AnsibleError("The group named '%s' has a recursive dependency loop." % to_native(group.name))

    def group_clear_hosts_cache(self, group_name):
        """
        :type group_name: str
        """
        self.groups[group_name]._hosts_cache = None
        for ancestor_name in self.group_get_ancestors(group_name):
            self.groups[ancestor_name]._hosts_cache = None

    def group_get_hosts(self, group_name):
        """
        :type group_name: str
        :rtype: list[str]
        Returns the cache of hosts associated with the group and any of its descenants
        """
        if self.groups[group_name]._hosts_cache is None:
            self.groups[group_name]._hosts_cache = self._group_get_hosts(group_name)
        return self.groups[group_name]._hosts_cache

    def _group_get_hosts(self, group_name):
        """
        :type group_name: str
        :rtype: list[str]
        Returns all of the hosts from the group's descendants
        """
        hosts = []
        seen = set()
        for child in self.group_get_descendants(group_name, include_self=True, preserve_ordering=True):
            for host_name in self.groups[child].hosts:
                if host_name not in seen:
                    seen.add(host_name)
                    if group_name == 'all' and self.hosts[host_name].implicit:
                        continue
                    hosts.append(host_name)
        return hosts


class InventoryData(InventoryHostManager, InventoryGroupManager):
    """
    Holds inventory data (host and group objects).
    Using it's methods should guarantee expected relationships and data.
    """

    def __init__(self):

        # the inventory object holds a list of groups
        self.groups = {}
        self.hosts = {}

        # provides 'groups' magic var, host object has group_names
        self._groups_dict_cache = {}

        # current localhost, implicit or explicit
        self.localhost = None

        self.current_source = None

        # Always create the 'all' and 'ungrouped' groups,
        for group in ('all', 'ungrouped'):
            self.add_group(group)
        self.add_child('all', 'ungrouped')

    def __eq__(self, inventory):
        return not self.__ne__(inventory)

    def __ne__(self, inventory):
        if not isinstance(inventory, InventoryData):
            return True

        current_inventory = self.serialize()
        comparison_inventory = inventory.serialize()

        # Compare top level of inventory
        if current_inventory['local'] != comparison_inventory['local']:
            return True
        if sorted(current_inventory['hosts'].keys()) != sorted(comparison_inventory['hosts'].keys()):
            return True
        if sorted(current_inventory['groups'].keys()) != sorted(comparison_inventory['groups'].keys()):
            return True

        # Compare inventory entity relationships and variables
        for host in current_inventory['hosts']:
            if current_inventory['hosts'][host].serialize() != comparison_inventory['hosts'][host].serialize():
                return True
        for group in current_inventory['groups']:
            if current_inventory['groups'][group].serialize() != comparison_inventory['groups'][group].serialize():
                return True

        # Inventories are identical
        return False

    def serialize(self):
        self._groups_dict_cache = None
        data = {
            'groups': self.groups,
            'hosts': self.hosts,
            'local': self.localhost,
            'source': self.current_source,
        }
        return data

    def deserialize(self, data):
        self._groups_dict_cache = {}
        self.hosts = data.get('hosts')
        self.groups = data.get('groups')
        self.localhost = data.get('local')
        self.current_source = data.get('source')

    def _create_implicit_localhost(self, pattern):

        if self.localhost:
            new_host = self.localhost
        else:
            new_host = Host(pattern)

            new_host.address = "127.0.0.1"
            new_host.implicit = True

            # set localhost defaults
            py_interp = sys.executable
            if not py_interp:
                # sys.executable is not set in some cornercases. see issue #13585
                py_interp = '/usr/bin/python'
                display.warning('Unable to determine python interpreter from sys.executable. Using /usr/bin/python default. '
                                'You can correct this by setting ansible_python_interpreter for localhost')
            new_host.set_variable("ansible_python_interpreter", py_interp)
            new_host.set_variable("ansible_connection", 'local')

            self.localhost = new_host

        return new_host

    def reconcile_inventory(self):
        ''' Ensure inventory basic rules, run after updates '''

        display.debug('Reconcile groups and hosts in inventory.')
        self.current_source = None

        group_names = set()
        # set group vars from group_vars/ files and vars plugins
        for g in self.groups:
            group = self.groups[g]
            group_names.add(group.name)

            # ensure all groups inherit from 'all'
            if group.name != 'all' and not self.group_get_ancestors(group.name):
                self.add_child('all', group.name)

        host_names = set()
        # get host vars from host_vars/ files and vars plugins
        for host in self.hosts.values():
            host_names.add(host.name)

            mygroups = host.get_groups()

            if self.groups['ungrouped'] in mygroups:
                # clear ungrouped of any incorrectly stored by parser
                if set(mygroups).difference(set([self.groups['all'], self.groups['ungrouped']])):
                    self.group_remove_host('ungrouped', host.name)

            elif not host.implicit:
                # add ungrouped hosts to ungrouped, except implicit
                length = len(mygroups)
                if length == 0 or (length == 1 and self.groups['all'] in mygroups):
                    self.add_child('ungrouped', host.name)

            # special case for implicit hosts
            if host.implicit:
                host.vars = combine_vars(self.groups['all'].get_vars(), host.vars)

        # warn if overloading identifier as both group and host
        for conflict in group_names.intersection(host_names):
            display.warning("Found both group and host with same name: %s" % conflict)

        self._groups_dict_cache = {}

    def get_host(self, hostname):
        ''' fetch host object using name deal with implicit localhost '''

        matching_host = self.hosts.get(hostname, None)

        # if host is not in hosts dict
        if matching_host is None and hostname in C.LOCALHOST:
            # might need to create implicit localhost
            matching_host = self._create_implicit_localhost(hostname)

        return matching_host

    def add_group(self, group):
        ''' adds a group to inventory if not there already, returns named actually used '''

        if group:
            if not isinstance(group, string_types):
                raise AnsibleError("Invalid group name supplied, expected a string but got %s for %s" % (type(group), group))
            if group not in self.groups:
                g = Group(group)
                if g.name not in self.groups:
                    self.groups[g.name] = g
                    self._groups_dict_cache = {}
                    display.debug("Added group %s to inventory" % group)
                group = g.name
            else:
                display.debug("group %s already in inventory" % group)
        else:
            raise AnsibleError("Invalid empty/false group name provided: %s" % group)

        return group

    def remove_group(self, group_name):
        # Remove references to the group from any hosts first
        # If the only group object is deleted before doing so the ancestors for the host could be inaccurate
        for host_name in self.hosts:
            self.host_remove_group(host_name, group_name)

        if group_name in self.groups:
            del self.groups[group_name]
            display.debug("Removed group %s from inventory" % group_name)
            self._groups_dict_cache = {}

    def add_host(self, host, group=None, port=None):
        ''' adds a host to inventory and possibly a group if not there already '''

        if host:
            if not isinstance(host, string_types):
                raise AnsibleError("Invalid host name supplied, expected a string but got %s for %s" % (type(host), host))

            # TODO: add to_safe_host_name
            g = None
            if group:
                if group in self.groups:
                    g = self.groups[group]
                else:
                    raise AnsibleError("Could not find group %s in inventory" % group)

            if host not in self.hosts:
                h = Host(host, port)
                self.hosts[host] = h
                if self.current_source:  # set to 'first source' in which host was encountered
                    self.set_variable(host, 'inventory_file', self.current_source)
                    self.set_variable(host, 'inventory_dir', basedir(self.current_source))
                else:
                    self.set_variable(host, 'inventory_file', None)
                    self.set_variable(host, 'inventory_dir', None)
                display.debug("Added host %s to inventory" % (host))

                # set default localhost from inventory to avoid creating an implicit one. Last localhost defined 'wins'.
                if host in C.LOCALHOST:
                    if self.localhost is None:
                        self.localhost = self.hosts[host]
                        display.vvvv("Set default localhost to %s" % h)
                    else:
                        display.warning("A duplicate localhost-like entry was found (%s). First found localhost was %s" % (h, self.localhost.name))
            else:
                h = self.hosts[host]

            if g:
                self.group_add_host(group, host)
                self.host_add_group(h.name, g.name)
                self._groups_dict_cache = {}
                display.debug("Added host %s to group %s" % (host, group))
        else:
            raise AnsibleError("Invalid empty host name provided: %s" % host)

        return host

    def remove_host(self, host):

        if host.name in self.hosts:
            del self.hosts[host.name]

        for group in self.groups:
            self.group_remove_host(group, host)

    def set_variable(self, entity, varname, value):
        ''' sets a variable for an inventory object '''

        if entity in self.groups:
            inv_object = self.groups[entity]
        elif entity in self.hosts:
            inv_object = self.hosts[entity]
        else:
            raise AnsibleError("Could not identify group or host named %s" % entity)

        inv_object.set_variable(varname, value)
        display.debug('set %s for %s' % (varname, entity))

    def add_child(self, group, child):
        ''' Add host or group to group '''

        if group in self.groups:
            g = self.groups[group]
            if child in self.groups:
                self.group_add_child_group(child, group)
            elif child in self.hosts:
                self.group_add_host(group, child)
                self.host_add_group(child, group)
            else:
                raise AnsibleError("%s is not a known host nor group" % child)
            self._groups_dict_cache = {}
            display.debug('Group %s now contains %s' % (group, child))
        else:
            raise AnsibleError("%s is not a known group" % group)

    def get_groups_dict(self):
        """
        We merge a 'magic' var 'groups' with group name keys and hostname list values into every host variable set. Cache for speed.
        """
        if not self._groups_dict_cache:
            for (group_name, group) in iteritems(self.groups):
                self._groups_dict_cache[group_name] = self.group_get_hosts(group_name)

        return self._groups_dict_cache
