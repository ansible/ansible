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

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.inventory.group import Group
from ansible.inventory.host import Host
from ansible.module_utils.six import string_types
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars
from ansible.utils.path import basedir

display = Display()


class InventoryData(object):
    """
    Holds inventory data (host and group objects).
    Using it's methods should guarantee expected relationships and data.
    """

    def __init__(self):

        self.groups = {}
        self.hosts = {}

        # provides 'groups' magic var, host object has group_names
        self._groups_dict_cache = {}

        # current localhost, implicit or explicit
        self.localhost = None

        self.current_source = None
        self.processed_sources = []

        # Always create the 'all' and 'ungrouped' groups,
        for group in ('all', 'ungrouped'):
            self.add_group(group)
        self.add_child('all', 'ungrouped')

    def serialize(self):
        self._groups_dict_cache = None
        data = {
            'groups': self.groups,
            'hosts': self.hosts,
            'local': self.localhost,
            'source': self.current_source,
            'processed_sources': self.processed_sources
        }
        return data

    def deserialize(self, data):
        self._groups_dict_cache = {}
        self.hosts = data.get('hosts')
        self.groups = data.get('groups')
        self.localhost = data.get('local')
        self.current_source = data.get('source')
        self.processed_sources = data.get('processed_sources')

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
            if group.name != 'all' and not group.get_ancestors():
                self.add_child('all', group.name)

        host_names = set()
        # get host vars from host_vars/ files and vars plugins
        for host in self.hosts.values():
            host_names.add(host.name)

            mygroups = host.get_groups()

            if self.groups['ungrouped'] in mygroups:
                # clear ungrouped of any incorrectly stored by parser
                if set(mygroups).difference(set([self.groups['all'], self.groups['ungrouped']])):
                    self.groups['ungrouped'].remove_host(host)

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

    def remove_group(self, group):

        if group in self.groups:
            del self.groups[group]
            display.debug("Removed group %s from inventory" % group)
            self._groups_dict_cache = {}

        for host in self.hosts:
            h = self.hosts[host]
            h.remove_group(group)

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
                g.add_host(h)
                self._groups_dict_cache = {}
                display.debug("Added host %s to group %s" % (host, group))
        else:
            raise AnsibleError("Invalid empty host name provided: %s" % host)

        return host

    def remove_host(self, host):

        if host.name in self.hosts:
            del self.hosts[host.name]

        for group in self.groups:
            g = self.groups[group]
            g.remove_host(host)

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
        added = False
        if group in self.groups:
            g = self.groups[group]
            if child in self.groups:
                added = g.add_child_group(self.groups[child])
            elif child in self.hosts:
                added = g.add_host(self.hosts[child])
            else:
                raise AnsibleError("%s is not a known host nor group" % child)
            self._groups_dict_cache = {}
            display.debug('Group %s now contains %s' % (group, child))
        else:
            raise AnsibleError("%s is not a known group" % group)
        return added

    def get_groups_dict(self):
        """
        We merge a 'magic' var 'groups' with group name keys and hostname list values into every host variable set. Cache for speed.
        """
        if not self._groups_dict_cache:
            for (group_name, group) in self.groups.items():
                self._groups_dict_cache[group_name] = [h.name for h in group.get_hosts()]

        return self._groups_dict_cache
