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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import sys
from ansible import constants as C
from ansible.inventory.group import Group
from .host import Host
from ansible.plugins.inventory.aggregate import InventoryAggregateParser
from ansible import errors

class Inventory:
    '''
    Create hosts and groups from inventory

    Retrieve the hosts and groups that ansible knows about from this class.

    Retrieve raw variables (non-expanded) from the Group and Host classes
    returned from here.
    '''

    def __init__(self, inventory_list=C.DEFAULT_HOST_LIST):
        '''
        :kwarg inventory_list: A list of inventory sources.  This may be file
            names which will be parsed as ini-like files, executable scripts
            which return inventory data as json, directories of both of the above,
            or hostnames.  Files and directories are 
        :kwarg vault_password: Password to use if any of the inventory sources
            are in an ansible vault
        '''

        self._restricted_to  = None
        self._filter_pattern = None

        parser = InventoryAggregateParser(inventory_list)
        parser.parse()

        self._basedir = parser.basedir
        self._hosts   = parser.hosts
        self._groups  = parser.groups

    def get_hosts(self):
        '''
        Return the list of hosts, after filtering based on any set pattern
        and restricting the results based on the set host restrictions.
        '''

        if self._filter_pattern:
            hosts = self._filter_hosts()
        else:
            hosts = self._hosts[:]

        if self._restricted_to is not None:
            # this will preserve the order of hosts after intersecting them
            res_set = set(hosts).intersection(self._restricted_to)
            return [h for h in hosts if h in res_set]
        else:
            return hosts[:]

    def get_groups(self):
        '''
        Retrieve the Group objects known to the Inventory
        '''

        return self._groups[:]

    def get_host(self, hostname):
        '''
        Retrieve the Host object for a hostname
        '''

        for host in self._hosts:
            if host.name == hostname:
                return host

        return None

    def get_group(self, groupname):
        '''
        Retrieve the Group object for a groupname
        '''

        for group in self._groups:
            if group.name == groupname:
                return group

        return None

    def add_group(self, group):
        '''
        Add a new group to the inventory
        '''

        if group not in self._groups:
            self._groups.append(group)

    def set_filter_pattern(self, pattern='all'):
        '''
        Sets a pattern upon which hosts/groups will be filtered.
        This pattern can contain logical groupings such as unions,
        intersections and negations using special syntax.
        '''

        self._filter_pattern = pattern

    def set_host_restriction(self, restriction):
        '''
        Restrict operations to hosts in the given list
        '''

        assert isinstance(restriction, list)
        self._restricted_to = restriction[:]

    def remove_host_restriction(self):
        '''
        Remove the restriction on hosts, if any.
        '''

        self._restricted_to = None

    def _filter_hosts(self):
        """
        Limits inventory results to a subset of inventory that matches a given
        list of patterns, such as to select a subset of a hosts selection that also
        belongs to a certain geographic group or numeric slice.

        Corresponds to --limit parameter to ansible-playbook

        :arg patterns: The pattern to limit with.  If this is None it
            clears the subset.  Multiple patterns may be specified as a comma,
            semicolon, or colon separated string.
        """

        hosts = []

        pattern_regular = []
        pattern_intersection = []
        pattern_exclude = []

        patterns = self._pattern.replace(";",":").split(":")
        for p in patterns:
            if p.startswith("!"):
                pattern_exclude.append(p)
            elif p.startswith("&"):
                pattern_intersection.append(p)
            elif p:
                pattern_regular.append(p)

        # if no regular pattern was given, hence only exclude and/or intersection
        # make that magically work
        if pattern_regular == []:
            pattern_regular = ['all']

        # when applying the host selectors, run those without the "&" or "!"
        # first, then the &s, then the !s.
        patterns = pattern_regular + pattern_intersection + pattern_exclude

        for p in patterns:
            intersect = False
            negate    = False
            if p.startswith('&'):
                intersect = True
            elif p.startswith('!'):
                p = p[1:]
                negate = True

            target = self._resolve_pattern(p)
            if isinstance(target, Host):
                if negate and target in hosts:
                    # remove it
                    hosts.remove(target)
                elif target not in hosts:
                    # for both union and intersections, we just append it
                    hosts.append(target)
            else:
                if intersect:
                    hosts = [ h for h in hosts if h not in target ]
                elif negate:
                    hosts = [ h for h in hosts if h in target ]
                else:
                    to_append = [ h for h in target if h.name not in [ y.name for y in hosts ] ]
                    hosts.extend(to_append)

        return hosts

    def _resolve_pattern(self, pattern):
        target = self.get_host(pattern)
        if target:
            return target
        else:
            (name, enumeration_details) = self._enumeration_info(pattern)
            hpat = self._hosts_in_unenumerated_pattern(name)
            result = self._apply_ranges(pattern, hpat)
            return result

    def _enumeration_info(self, pattern):
        """
        returns (pattern, limits) taking a regular pattern and finding out
        which parts of it correspond to start/stop offsets.  limits is
        a tuple of (start, stop) or None
        """

        # Do not parse regexes for enumeration info
        if pattern.startswith('~'):
            return (pattern, None)

        # The regex used to match on the range, which can be [x] or [x-y].
        pattern_re = re.compile("^(.*)\[([-]?[0-9]+)(?:(?:-)([0-9]+))?\](.*)$")
        m = pattern_re.match(pattern)
        if m:
            (target, first, last, rest) = m.groups()
            first = int(first)
            if last:
                if first < 0:
                    raise errors.AnsibleError("invalid range: negative indices cannot be used as the first item in a range")
                last = int(last)
            else:
                last = first
            return (target, (first, last))
        else:
            return (pattern, None)

    def _apply_ranges(self, pat, hosts):
        """
        given a pattern like foo, that matches hosts, return all of hosts
        given a pattern like foo[0:5], where foo matches hosts, return the first 6 hosts
        """ 

        # If there are no hosts to select from, just return the
        # empty set. This prevents trying to do selections on an empty set.
        # issue#6258
        if not hosts:
            return hosts

        (loose_pattern, limits) = self._enumeration_info(pat)
        if not limits:
            return hosts

        (left, right) = limits

        if left == '':
            left = 0
        if right == '':
            right = 0
        left=int(left)
        right=int(right)
        try:
            if left != right:
                return hosts[left:right]
            else:
                return [ hosts[left] ]
        except IndexError:
            raise errors.AnsibleError("no hosts matching the pattern '%s' were found" % pat)

    def _hosts_in_unenumerated_pattern(self, pattern):
        """ Get all host names matching the pattern """

        results = []
        hosts = []
        hostnames = set()

        # ignore any negative checks here, this is handled elsewhere
        pattern = pattern.replace("!","").replace("&", "")

        def __append_host_to_results(host):
            if host not in results and host.name not in hostnames:
                hostnames.add(host.name)
                results.append(host)

        groups = self.get_groups()
        for group in groups:
            if pattern == 'all':
                for host in group.get_hosts():
                    __append_host_to_results(host)
            else:
                if self._match(group.name, pattern):
                    for host in group.get_hosts():
                        __append_host_to_results(host)
                else:
                    matching_hosts = self._match_list(group.get_hosts(), 'name', pattern)
                    for host in matching_hosts:
                        __append_host_to_results(host)

        if pattern in ["localhost", "127.0.0.1"] and len(results) == 0:
            new_host = self._create_implicit_localhost(pattern)
            results.append(new_host)
        return results

    def _create_implicit_localhost(self, pattern):
        new_host = Host(pattern)
        new_host._connection = 'local'
        new_host.set_variable("ansible_python_interpreter", sys.executable)
        ungrouped = self.get_group("ungrouped")
        if ungrouped is None:
            self.add_group(Group('ungrouped'))
            ungrouped = self.get_group('ungrouped')
            self.get_group('all').add_child_group(ungrouped)
        ungrouped.add_host(new_host)
        return new_host

    def is_file(self):
        '''
        Did inventory come from a file?

        :returns: True if the inventory is file based, False otherwise
        '''
        pass

    def src(self):
        '''
        What's the complete path to the inventory file?

        :returns: Complete path to the inventory file.  None if inventory is
            not file-based
        '''
        pass

    def basedir(self):
        '''
        What directory from which the inventory was read.
        '''

        return self._basedir

