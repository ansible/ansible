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

import fnmatch
import os
import sys
import re
import stat

from ansible import constants as C
from ansible.errors import AnsibleError

from ansible.inventory.dir import InventoryDirectory, get_file_parser
from ansible.inventory.group import Group
from ansible.inventory.host import Host
from ansible.plugins import vars_loader
from ansible.utils.vars import combine_vars
from ansible.parsing.utils.addresses import parse_address

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class Inventory(object):
    """
    Host inventory for ansible.
    """

    def __init__(self, loader, variable_manager, host_list=C.DEFAULT_HOST_LIST):

        # the host file file, or script path, or list of hosts
        # if a list, inventory data will NOT be loaded
        self.host_list = host_list
        self._loader = loader
        self._variable_manager = variable_manager

        # caching to avoid repeated calculations, particularly with
        # external inventory scripts.

        self._vars_per_host  = {}
        self._vars_per_group = {}
        self._hosts_cache    = {}
        self._pattern_cache  = {}
        self._vars_plugins   = []

        # to be set by calling set_playbook_basedir by playbook code
        self._playbook_basedir = None

        # the inventory object holds a list of groups
        self.groups = {}

        # a list of host(names) to contain current inquiries to
        self._restriction = None
        self._subset = None

        self.parse_inventory(host_list)

    def parse_inventory(self, host_list):

        if isinstance(host_list, basestring):
            if "," in host_list:
                host_list = host_list.split(",")
                host_list = [ h for h in host_list if h and h.strip() ]

        self.parser = None

        # Always create the 'all' and 'ungrouped' groups, even if host_list is
        # empty: in this case we will subsequently an the implicit 'localhost' to it.

        ungrouped = Group(name='ungrouped')
        all = Group('all')
        all.add_child_group(ungrouped)

        self.groups = dict(all=all, ungrouped=ungrouped)

        if host_list is None:
            pass
        elif isinstance(host_list, list):
            for h in host_list:
                (host, port) = parse_address(h, allow_ranges=False)
                all.add_host(Host(host, port))
        elif self._loader.path_exists(host_list):
            #TODO: switch this to a plugin loader and a 'condition' per plugin on which it should be tried, restoring 'inventory pllugins'
            if self._loader.is_directory(host_list):
                # Ensure basedir is inside the directory
                host_list = os.path.join(self.host_list, "")
                self.parser = InventoryDirectory(loader=self._loader, groups=self.groups, filename=host_list)
            else:
                self.parser = get_file_parser(host_list, self.groups, self._loader)
                vars_loader.add_directory(self.basedir(), with_subdir=True)

            if not self.parser:
                # should never happen, but JIC
                raise AnsibleError("Unable to parse %s as an inventory source" % host_list)

        self._vars_plugins = [ x for x in vars_loader.all(self) ]

        # FIXME: shouldn't be required, since the group/host vars file
        #        management will be done in VariableManager
        # get group vars from group_vars/ files and vars plugins
        for group in self.groups.values():
            group.vars = combine_vars(group.vars, self.get_group_variables(group.name))

        # get host vars from host_vars/ files and vars plugins
        for host in self.get_hosts():
            host.vars = combine_vars(host.vars, self.get_host_variables(host.name))

    def _match(self, str, pattern_str):
        try:
            if pattern_str.startswith('~'):
                return re.search(pattern_str[1:], str)
            else:
                return fnmatch.fnmatch(str, pattern_str)
        except Exception as e:
            raise AnsibleError('invalid host pattern: %s' % pattern_str)

    def _match_list(self, items, item_attr, pattern_str):
        results = []
        try:
            if not pattern_str.startswith('~'):
                pattern = re.compile(fnmatch.translate(pattern_str))
            else:
                pattern = re.compile(pattern_str[1:])
        except Exception as e:
            raise AnsibleError('invalid host pattern: %s' % pattern_str)

        for item in items:
            if pattern.match(getattr(item, item_attr)):
                results.append(item)
        return results

    def _split_pattern(self, pattern):
        """
        takes e.g. "webservers[0:5]:dbservers:others"
        and returns ["webservers[0:5]", "dbservers", "others"]
        """

        term = re.compile(
            r'''(?:             # We want to match something comprising:
                    [^:\[\]]    # (anything other than ':', '[', or ']'
                    |           # ...or...
                    \[[^\]]*\]  # a single complete bracketed expression)
                )*              # repeated as many times as possible
            ''', re.X
        )

        return [x for x in term.findall(pattern) if x]

    def get_hosts(self, pattern="all", ignore_limits_and_restrictions=False):
        """ 
        Takes a pattern or list of patterns and returns a list of matching
        inventory host names, taking into account any active restrictions
        or applied subsets
        """

        # Enumerate all hosts matching the given pattern (which may be
        # either a list of patterns or a string like 'pat1:pat2').
        if isinstance(pattern, list):
            pattern = ':'.join(pattern)

        if ';' in pattern or ',' in pattern:
            display.deprecated("Use ':' instead of ',' or ';' to separate host patterns", version=2.0, removed=True)

        patterns = self._split_pattern(pattern)
        hosts = self._evaluate_patterns(patterns)

        # mainly useful for hostvars[host] access
        if not ignore_limits_and_restrictions:
            # exclude hosts not in a subset, if defined
            if self._subset:
                subset = self._evaluate_patterns(self._subset)
                hosts = [ h for h in hosts if h in subset ]

            # exclude hosts mentioned in any restriction (ex: failed hosts)
            if self._restriction is not None:
                hosts = [ h for h in hosts if h in self._restriction ]

        return hosts

    def _evaluate_patterns(self, patterns):
        """
        Takes a list of patterns and returns a list of matching host names,
        taking into account any negative and intersection patterns.
        """

        # Host specifiers should be sorted to ensure consistent behavior
        pattern_regular = []
        pattern_intersection = []
        pattern_exclude = []
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

        hosts = []

        for p in patterns:
            # avoid resolving a pattern that is a plain host
            if p in self._hosts_cache:
                hosts.append(self.get_host(p))
            else:
                that = self._match_one_pattern(p)
                if p.startswith("!"):
                    hosts = [ h for h in hosts if h not in that ]
                elif p.startswith("&"):
                    hosts = [ h for h in hosts if h in that ]
                else:
                    to_append = [ h for h in that if h.name not in [ y.name for y in hosts ] ]
                    hosts.extend(to_append)
        return hosts

    def _match_one_pattern(self, pattern):
        """ 
        Takes a single pattern and returns a list of matching host names.
        Ignores intersection (&) and exclusion (!) specifiers.

        The pattern may be:

            1. A regex starting with ~, e.g. '~[abc]*'
            2. A shell glob pattern with ?/*/[chars]/[!chars], e.g. 'foo'
            3. An ordinary word that matches itself only, e.g. 'foo'

        The pattern is matched using the following rules:

            1. If it's 'all', it matches all hosts in all groups.
            2. Otherwise, for each known group name:
                (a) if it matches the group name, the results include all hosts
                    in the group or any of its children.
                (b) otherwise, if it matches any hosts in the group, the results
                    include the matching hosts.

        This means that 'foo*' may match one or more groups (thus including all
        hosts therein) but also hosts in other groups.

        The built-in groups 'all' and 'ungrouped' are special. No pattern can
        match these group names (though 'all' behaves as though it matches, as
        described above). The word 'ungrouped' can match a host of that name,
        and patterns like 'ungr*' and 'al*' can match either hosts or groups
        other than all and ungrouped.

        If the pattern matches one or more group names according to these rules,
        it may have an optional range suffix to select a subset of the results.
        This is allowed only if the pattern is not a regex, i.e. '~foo[1]' does
        not work (the [1] is interpreted as part of the regex), but 'foo*[1]'
        would work if 'foo*' matched the name of one or more groups.

        Duplicate matches are always eliminated from the results.
        """

        if pattern.startswith("&") or pattern.startswith("!"):
            pattern = pattern[1:]

        if pattern not in self._pattern_cache:
            (expr, slice) = self._split_subscript(pattern)
            hosts = self._enumerate_matches(expr)
            try:
                hosts = self._apply_subscript(hosts, slice)
            except IndexError:
                raise AnsibleError("No hosts matched the subscripted pattern '%s'" % pattern)
            self._pattern_cache[pattern] = hosts

        return self._pattern_cache[pattern]

    def _split_subscript(self, pattern):
        """
        Takes a pattern, checks if it has a subscript, and returns the pattern
        without the subscript and a (start,end) tuple representing the given
        subscript (or None if there is no subscript).

        Validates that the subscript is in the right syntax, but doesn't make
        sure the actual indices make sense in context.
        """

        # Do not parse regexes for enumeration info
        if pattern.startswith('~'):
            return (pattern, None)

        # We want a pattern followed by an integer or range subscript.
        # (We can't be more restrictive about the expression because the
        # fnmatch semantics permit [\[:\]] to occur.)

        pattern_with_subscript = re.compile(
            r'''^
                (.+)                    # A pattern expression ending with...
                \[(?:                   # A [subscript] expression comprising:
                    (-?[0-9]+)          # A single positive or negative number
                    |                   # Or a numeric range
                    ([0-9]+)([:-])([0-9]+)
                )\]
                $
            ''', re.X
        )

        subscript = None
        m = pattern_with_subscript.match(pattern)
        if m:
            (pattern, idx, start, sep, end) = m.groups()
            if idx:
                subscript = (int(idx), None)
            else:
                subscript = (int(start), int(end))
                if sep == '-':
                    display.deprecated("Use [x:y] inclusive subscripts instead of [x-y]", version=2.0, removed=True)

        return (pattern, subscript)

    def _apply_subscript(self, hosts, subscript):
        """
        Takes a list of hosts and a (start,end) tuple and returns the subset of
        hosts based on the subscript (which may be None to return all hosts).
        """ 

        if not hosts or not subscript:
            return hosts

        (start, end) = subscript

        if end:
            return hosts[start:end+1]
        else:
            return [ hosts[start] ]

    def _enumerate_matches(self, pattern):
        """
        Returns a list of host names matching the given pattern according to the
        rules explained above in _match_one_pattern.
        """

        results = []
        hosts = []
        hostnames = set()

        def __append_host_to_results(host):
            if host.name not in hostnames:
                hostnames.add(host.name)
                results.append(host)

        groups = self.get_groups()
        for group in groups.values():
            if pattern == 'all':
                for host in group.get_hosts():
                    __append_host_to_results(host)
            else:
                if self._match(group.name, pattern) and group.name not in ('all', 'ungrouped'):
                    for host in group.get_hosts():
                        __append_host_to_results(host)
                else:
                    matching_hosts = self._match_list(group.get_hosts(), 'name', pattern)
                    for host in matching_hosts:
                        __append_host_to_results(host)

        if pattern in C.LOCALHOST and len(results) == 0:
            new_host = self._create_implicit_localhost(pattern)
            results.append(new_host)
        return results

    def _create_implicit_localhost(self, pattern):
        new_host = Host(pattern)
        new_host.set_variable("ansible_python_interpreter", sys.executable)
        new_host.set_variable("ansible_connection", "local")
        new_host.ipv4_address = '127.0.0.1'
        self.get_group("ungrouped").add_host(new_host)
        return new_host

    def clear_pattern_cache(self):
        ''' called exclusively by the add_host plugin to allow patterns to be recalculated '''
        self._pattern_cache = {}

    def groups_for_host(self, host):
        if host in self._hosts_cache:
            return self._hosts_cache[host].get_groups()
        else:
            return []

    def get_groups(self):
        return self.groups

    def get_host(self, hostname):
        if hostname not in self._hosts_cache:
            self._hosts_cache[hostname] = self._get_host(hostname)
            if hostname in C.LOCALHOST:
                for host in C.LOCALHOST.difference((hostname,)):
                    self._hosts_cache[host] = self._hosts_cache[hostname]
        return self._hosts_cache[hostname]

    def _get_host(self, hostname):
        if hostname in C.LOCALHOST:
            for host in self.get_group('all').get_hosts():
                if host.name in C.LOCALHOST:
                    return host
            return self._create_implicit_localhost(hostname)
        matching_host = None
        for group in self.groups.values():
            for host in group.get_hosts():
                if hostname == host.name:
                    matching_host = host
                self._hosts_cache[host.name] = host
        return matching_host

    def get_group(self, groupname):
        return self.groups[groupname]

    def get_group_variables(self, groupname, update_cached=False, vault_password=None):
        if groupname not in self._vars_per_group or update_cached:
            self._vars_per_group[groupname] = self._get_group_variables(groupname, vault_password=vault_password)
        return self._vars_per_group[groupname]

    def _get_group_variables(self, groupname, vault_password=None):

        group = self.get_group(groupname)
        if group is None:
            raise Exception("group not found: %s" % groupname)

        vars = {}

        # plugin.get_group_vars retrieves just vars for specific group
        vars_results = [ plugin.get_group_vars(group, vault_password=vault_password) for plugin in self._vars_plugins if hasattr(plugin, 'get_group_vars')]
        for updated in vars_results:
            if updated is not None:
                vars = combine_vars(vars, updated)

        # Read group_vars/ files
        vars = combine_vars(vars, self.get_group_vars(group))

        return vars

    def get_vars(self, hostname, update_cached=False, vault_password=None):

        host = self.get_host(hostname)
        if not host:
            raise AnsibleError("no vars as host is not in inventory: %s" % hostname)
        return host.get_vars()

    def get_host_variables(self, hostname, update_cached=False, vault_password=None):

        if hostname not in self._vars_per_host or update_cached:
            self._vars_per_host[hostname] = self._get_host_variables(hostname, vault_password=vault_password)
        return self._vars_per_host[hostname]

    def _get_host_variables(self, hostname, vault_password=None):

        host = self.get_host(hostname)
        if host is None:
            raise AnsibleError("no host vars as host is not in inventory: %s" % hostname)

        vars = {}

        # plugin.run retrieves all vars (also from groups) for host
        vars_results = [ plugin.run(host, vault_password=vault_password) for plugin in self._vars_plugins if hasattr(plugin, 'run')]
        for updated in vars_results:
            if updated is not None:
                vars = combine_vars(vars, updated)

        # plugin.get_host_vars retrieves just vars for specific host
        vars_results = [ plugin.get_host_vars(host, vault_password=vault_password) for plugin in self._vars_plugins if hasattr(plugin, 'get_host_vars')]
        for updated in vars_results:
            if updated is not None:
                vars = combine_vars(vars, updated)

        # still need to check InventoryParser per host vars
        # which actually means InventoryScript per host,
        # which is not performant
        if self.parser is not None:
            vars = combine_vars(vars, self.parser.get_host_variables(host))

        # Read host_vars/ files
        vars = combine_vars(vars, self.get_host_vars(host))

        return vars

    def add_group(self, group):
        if group.name not in self.groups:
            self.groups[group.name] = group
        else:
            raise AnsibleError("group already in inventory: %s" % group.name)

    def list_hosts(self, pattern="all"):

        """ return a list of hostnames for a pattern """

        result = [ h for h in self.get_hosts(pattern) ]
        if len(result) == 0 and pattern in C.LOCALHOST:
            result = [pattern]
        return result

    def list_groups(self):
        return sorted(self.groups.keys(), key=lambda x: x)

    def restrict_to_hosts(self, restriction):
        """ 
        Restrict list operations to the hosts given in restriction.  This is used
        to batch serial operations in main playbook code, don't use this for other
        reasons.
        """
        if restriction is None:
            return
        elif not isinstance(restriction, list):
            restriction = [ restriction ]
        self._restriction = restriction

    def subset(self, subset_pattern):
        """ 
        Limits inventory results to a subset of inventory that matches a given
        pattern, such as to select a given geographic of numeric slice amongst
        a previous 'hosts' selection that only select roles, or vice versa.  
        Corresponds to --limit parameter to ansible-playbook
        """        
        if subset_pattern is None:
            self._subset = None
        else:
            if ';' in subset_pattern or ',' in subset_pattern:
                display.deprecated("Use ':' instead of ',' or ';' to separate host patterns", version=2.0, removed=True)

            subset_patterns = self._split_pattern(subset_pattern)
            results = []
            # allow Unix style @filename data
            for x in subset_patterns:
                if x.startswith("@"):
                    fd = open(x[1:])
                    results.extend(fd.read().split("\n"))
                    fd.close()
                else:
                    results.append(x)
            self._subset = results

    def remove_restriction(self):
        """ Do not restrict list operations """
        self._restriction = None

    def is_file(self):
        """ did inventory come from a file? """
        if not isinstance(self.host_list, basestring):
            return False
        return self._loader.path_exists(self.host_list)

    def basedir(self):
        """ if inventory came from a file, what's the directory? """
        dname = self.host_list
        if not self.is_file():
            dname = None
        elif self._loader.is_directory(self.host_list):
            dname = self.host_list
        else:
            dname = os.path.dirname(self.host_list)
            if dname is None or dname == '' or dname == '.':
                cwd = os.getcwd()
                dname = cwd
        if dname:
            dname = os.path.abspath(dname)
        return dname

    def src(self):
        """ if inventory came from a file, what's the directory and file name? """
        if not self.is_file():
            return None
        return self.host_list

    def playbook_basedir(self):
        """ returns the directory of the current playbook """
        return self._playbook_basedir

    def set_playbook_basedir(self, dir_name):
        """
        sets the base directory of the playbook so inventory can use it as a
        basedir for host_ and group_vars, and other things.
        """
        # Only update things if dir is a different playbook basedir
        if dir_name != self._playbook_basedir:
            self._playbook_basedir = dir_name
            # get group vars from group_vars/ files
            # FIXME: excluding the new_pb_basedir directory may result in group_vars
            #        files loading more than they should, however with the file caching
            #        we do this shouldn't be too much of an issue. Still, this should
            #        be fixed at some point to allow a "first load" to touch all of the
            #        directories, then later runs only touch the new basedir specified
            for group in self.groups:
                #group.vars = combine_vars(group.vars, self.get_group_vars(group, new_pb_basedir=True))
                group.vars = combine_vars(group.vars, self.get_group_vars(group))
            # get host vars from host_vars/ files
            for host in self.get_hosts():
                #host.vars = combine_vars(host.vars, self.get_host_vars(host, new_pb_basedir=True))
                host.vars = combine_vars(host.vars, self.get_host_vars(host))
            # invalidate cache
            self._vars_per_host = {}
            self._vars_per_group = {}

    def get_host_vars(self, host, new_pb_basedir=False):
        """ Read host_vars/ files """
        return self._get_hostgroup_vars(host=host, group=None, new_pb_basedir=new_pb_basedir)

    def get_group_vars(self, group, new_pb_basedir=False):
        """ Read group_vars/ files """
        return self._get_hostgroup_vars(host=None, group=group, new_pb_basedir=new_pb_basedir)

    def _get_hostgroup_vars(self, host=None, group=None, new_pb_basedir=False):
        """
        Loads variables from group_vars/<groupname> and host_vars/<hostname> in directories parallel
        to the inventory base directory or in the same directory as the playbook.  Variables in the playbook
        dir will win over the inventory dir if files are in both.
        """

        results = {}
        scan_pass = 0
        _basedir = self.basedir()

        # look in both the inventory base directory and the playbook base directory
        # unless we do an update for a new playbook base dir
        if not new_pb_basedir:
            basedirs = [_basedir, self._playbook_basedir]
        else:
            basedirs = [self._playbook_basedir]

        for basedir in basedirs:
            display.debug('getting vars from %s' % basedir)

            # this can happen from particular API usages, particularly if not run
            # from /usr/bin/ansible-playbook
            if basedir is None:
                basedir = './'

            scan_pass = scan_pass + 1

            # it's not an eror if the directory does not exist, keep moving
            if not os.path.exists(basedir):
                continue

            # save work of second scan if the directories are the same
            if _basedir == self._playbook_basedir and scan_pass != 1:
                continue

            # FIXME: these should go to VariableManager
            if group and host is None:
                # load vars in dir/group_vars/name_of_group
                base_path = os.path.realpath(os.path.join(basedir, "group_vars/%s" % group.name))
                results = self._variable_manager.add_group_vars_file(base_path, self._loader)
            elif host and group is None:
                # same for hostvars in dir/host_vars/name_of_host
                base_path = os.path.realpath(os.path.join(basedir, "host_vars/%s" % host.name))
                results = self._variable_manager.add_host_vars_file(base_path, self._loader)

        # all done, results is a dictionary of variables for this particular host.
        return results

    def refresh_inventory(self):

        self.clear_pattern_cache()

        self._hosts_cache    = {}
        self._vars_per_host  = {}
        self._vars_per_group = {}
        self.groups          = {}

        self.parse_inventory(self.host_list)
