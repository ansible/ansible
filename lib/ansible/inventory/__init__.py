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

import fnmatch
import os
import sys
import re
import subprocess

import ansible.constants as C
from ansible.inventory.ini import InventoryParser
from ansible.inventory.script import InventoryScript
from ansible.inventory.dir import InventoryDirectory
from ansible.inventory.group import Group
from ansible.inventory.host import Host
from ansible import errors
from ansible import utils

class Inventory(object):
    """
    Host inventory for ansible.
    """

    __slots__ = [ 'host_list', 'groups', '_restriction', '_also_restriction', '_subset', 
                  'parser', '_vars_per_host', '_vars_per_group', '_hosts_cache', '_groups_list',
                  '_pattern_cache', '_vars_plugins', '_playbook_basedir']

    def __init__(self, host_list=C.DEFAULT_HOST_LIST):

        # the host file file, or script path, or list of hosts
        # if a list, inventory data will NOT be loaded
        self.host_list = host_list

        # caching to avoid repeated calculations, particularly with
        # external inventory scripts.

        self._vars_per_host  = {}
        self._vars_per_group = {}
        self._hosts_cache    = {}
        self._groups_list    = {} 
        self._pattern_cache  = {}

        # to be set by calling set_playbook_basedir by ansible-playbook
        self._playbook_basedir = None

        # the inventory object holds a list of groups
        self.groups = []

        # a list of host(names) to contain current inquiries to
        self._restriction = None
        self._also_restriction = None
        self._subset = None

        if isinstance(host_list, basestring):
            if "," in host_list:
                host_list = host_list.split(",")
                host_list = [ h for h in host_list if h and h.strip() ]

        if host_list is None:
            self.parser = None
        elif isinstance(host_list, list):
            self.parser = None
            all = Group('all')
            self.groups = [ all ]
            ipv6_re = re.compile('\[([a-f:A-F0-9]*[%[0-z]+]?)\](?::(\d+))?')
            for x in host_list:
                m = ipv6_re.match(x)
                if m:
                    all.add_host(Host(m.groups()[0], m.groups()[1]))
                else:
                    if ":" in x:
                        tokens = x.rsplit(":", 1)
                        # if there is ':' in the address, then this is a ipv6
                        if ':' in tokens[0]:
                            all.add_host(Host(x))
                        else:
                            all.add_host(Host(tokens[0], tokens[1]))
                    else:
                        all.add_host(Host(x))
        elif os.path.exists(host_list):
            if os.path.isdir(host_list):
                # Ensure basedir is inside the directory
                self.host_list = os.path.join(self.host_list, "")
                self.parser = InventoryDirectory(filename=host_list)
                self.groups = self.parser.groups.values()
            else:
                # check to see if the specified file starts with a
                # shebang (#!/), so if an error is raised by the parser
                # class we can show a more apropos error
                shebang_present = False
                try:
                    inv_file = open(host_list)
                    first_line = inv_file.readlines()[0]
                    inv_file.close()
                    if first_line.startswith('#!'):
                        shebang_present = True
                except:
                    pass

                if utils.is_executable(host_list):
                    try:
                        self.parser = InventoryScript(filename=host_list)
                        self.groups = self.parser.groups.values()
                    except:
                        if not shebang_present:
                            raise errors.AnsibleError("The file %s is marked as executable, but failed to execute correctly. " % host_list + \
                                                      "If this is not supposed to be an executable script, correct this with `chmod -x %s`." % host_list)
                        else:
                            raise
                else:
                    try:
                        self.parser = InventoryParser(filename=host_list)
                        self.groups = self.parser.groups.values()
                    except:
                        if shebang_present:
                            raise errors.AnsibleError("The file %s looks like it should be an executable inventory script, but is not marked executable. " % host_list + \
                                                      "Perhaps you want to correct this with `chmod +x %s`?" % host_list)
                        else:
                            raise

            utils.plugins.vars_loader.add_directory(self.basedir(), with_subdir=True)
        else:
            raise errors.AnsibleError("Unable to find an inventory file, specify one with -i ?")

        self._vars_plugins = [ x for x in utils.plugins.vars_loader.all(self) ]


    def _match(self, str, pattern_str):
        if pattern_str.startswith('~'):
            return re.search(pattern_str[1:], str)
        else:
            return fnmatch.fnmatch(str, pattern_str)

    def get_hosts(self, pattern="all"):
        """ 
        find all host names matching a pattern string, taking into account any inventory restrictions or
        applied subsets.
        """

        # process patterns
        if isinstance(pattern, list):
            pattern = ';'.join(pattern)
        patterns = pattern.replace(";",":").split(":")
        hosts = self._get_hosts(patterns)

        # exclude hosts not in a subset, if defined
        if self._subset:
            subset = self._get_hosts(self._subset)
            hosts = [ h for h in hosts if h in subset ]

        # exclude hosts mentioned in any restriction (ex: failed hosts)
        if self._restriction is not None:
            hosts = [ h for h in hosts if h.name in self._restriction ]
        if self._also_restriction is not None:
            hosts = [ h for h in hosts if h.name in self._also_restriction ]

        return hosts

    def _get_hosts(self, patterns):
        """
        finds hosts that match a list of patterns. Handles negative
        matches as well as intersection matches.
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
            else:
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
            that = self.__get_hosts(p)
            if p.startswith("!"):
                hosts = [ h for h in hosts if h not in that ]
            elif p.startswith("&"):
                hosts = [ h for h in hosts if h in that ]
            else:
                to_append = [ h for h in that if h.name not in [ y.name for y in hosts ] ]
                hosts.extend(to_append)
        
        return hosts

    def __get_hosts(self, pattern):
        """ 
        finds hosts that postively match a particular pattern.  Does not
        take into account negative matches.
        """

        if pattern in self._pattern_cache:
            return self._pattern_cache[pattern]

        (name, enumeration_details) = self._enumeration_info(pattern)
        hpat = self._hosts_in_unenumerated_pattern(name)
        result = self._apply_ranges(pattern, hpat)
        self._pattern_cache[pattern] = result
        return result

    def _enumeration_info(self, pattern):
        """
        returns (pattern, limits) taking a regular pattern and finding out
        which parts of it correspond to start/stop offsets.  limits is
        a tuple of (start, stop) or None
        """

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

    def _create_implicit_localhost(self, pattern):
        new_host = Host(pattern)
        new_host.set_variable("ansible_python_interpreter", sys.executable)
        new_host.set_variable("ansible_connection", "local")
        ungrouped = self.get_group("ungrouped")
        if ungrouped is None:
            self.add_group(Group('ungrouped'))
            ungrouped = self.get_group('ungrouped')
        ungrouped.add_host(new_host)
        return new_host

    def _hosts_in_unenumerated_pattern(self, pattern):
        """ Get all host names matching the pattern """

        hosts = []
        hostnames = set()

        # ignore any negative checks here, this is handled elsewhere
        pattern = pattern.replace("!","").replace("&", "")

        results = []
        groups = self.get_groups()
        for group in groups:
            for host in group.get_hosts():
                if pattern == 'all' or self._match(group.name, pattern) or self._match(host.name, pattern):
                    if host not in results and host.name not in hostnames:
                        results.append(host)
                        hostnames.add(host.name)

        if pattern in ["localhost", "127.0.0.1"] and len(results) == 0:
            new_host = self._create_implicit_localhost(pattern)
            results.append(new_host)
        return results

    def clear_pattern_cache(self):
        ''' called exclusively by the add_host plugin to allow patterns to be recalculated '''
        self._pattern_cache = {}

    def groups_for_host(self, host):
        results = []
        groups = self.get_groups()
        for group in groups:
            for hostn in group.get_hosts():
                if host == hostn.name:
                    results.append(group)
                    continue
        return results

    def groups_list(self):
        if not self._groups_list:
            groups = {}
            for g in self.groups:
                groups[g.name] = [h.name for h in g.get_hosts()]
                ancestors = g.get_ancestors()
                for a in ancestors:
                    if a.name not in groups:
                        groups[a.name] = [h.name for h in a.get_hosts()]
            self._groups_list = groups
        return self._groups_list

    def get_groups(self):
        return self.groups

    def get_host(self, hostname):
        if hostname not in self._hosts_cache:
            self._hosts_cache[hostname] = self._get_host(hostname)
        return self._hosts_cache[hostname]

    def _get_host(self, hostname):
        if hostname in ['localhost','127.0.0.1']:
            for host in self.get_group('all').get_hosts():
                if host.name in ['localhost', '127.0.0.1']:
                    return host
            return self._create_implicit_localhost(hostname)
        else:
            for group in self.groups:
                for host in group.get_hosts():
                    if hostname == host.name:
                        return host
        return None

    def get_group(self, groupname):
        for group in self.groups:
            if group.name == groupname:
                return group
        return None

    def get_group_variables(self, groupname):
        if groupname not in self._vars_per_group:
            self._vars_per_group[groupname] = self._get_group_variables(groupname)
        return self._vars_per_group[groupname]

    def _get_group_variables(self, groupname):
        group = self.get_group(groupname)
        if group is None:
            raise Exception("group not found: %s" % groupname)
        return group.get_variables()

    def get_variables(self, hostname, vault_password=None):
        if hostname not in self._vars_per_host:
            self._vars_per_host[hostname] = self._get_variables(hostname, vault_password=vault_password)
        return self._vars_per_host[hostname]

    def _get_variables(self, hostname, vault_password=None):

        host = self.get_host(hostname)
        if host is None:
            raise errors.AnsibleError("host not found: %s" % hostname)

        vars = {}
        vars_results = [ plugin.run(host, vault_password=vault_password) for plugin in self._vars_plugins ] 
        for updated in vars_results:
            if updated is not None:
                vars = utils.combine_vars(vars, updated)

        vars = utils.combine_vars(vars, host.get_variables())
        if self.parser is not None:
            vars = utils.combine_vars(vars, self.parser.get_host_variables(host))
        return vars

    def add_group(self, group):
        self.groups.append(group)
        self._groups_list = None  # invalidate internal cache 

    def list_hosts(self, pattern="all"):

        """ return a list of hostnames for a pattern """

        result = [ h.name for h in self.get_hosts(pattern) ]
        if len(result) == 0 and pattern in ["localhost", "127.0.0.1"]:
            result = [pattern]
        return result

    def list_groups(self):
        return sorted([ g.name for g in self.groups ], key=lambda x: x)

    # TODO: remove this function
    def get_restriction(self):
        return self._restriction

    def restrict_to(self, restriction):
        """ 
        Restrict list operations to the hosts given in restriction.  This is used
        to exclude failed hosts in main playbook code, don't use this for other
        reasons.
        """
        if not isinstance(restriction, list):
            restriction = [ restriction ]
        self._restriction = restriction

    def also_restrict_to(self, restriction):
        """
        Works like restict_to but offers an additional restriction.  Playbooks use this
        to implement serial behavior.
        """
        if not isinstance(restriction, list):
            restriction = [ restriction ]
        self._also_restriction = restriction
    
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
            subset_pattern = subset_pattern.replace(',',':')
            subset_pattern = subset_pattern.replace(";",":").split(":")
            results = []
            # allow Unix style @filename data
            for x in subset_pattern:
                if x.startswith("@"):
                    fd = open(x[1:])
                    results.extend(fd.read().split("\n"))
                    fd.close()
                else:
                    results.append(x)
            self._subset = results

    def lift_restriction(self):
        """ Do not restrict list operations """
        self._restriction = None
    
    def lift_also_restriction(self):
        """ Clears the also restriction """
        self._also_restriction = None

    def is_file(self):
        """ did inventory come from a file? """
        if not isinstance(self.host_list, basestring):
            return False
        return os.path.exists(self.host_list)

    def basedir(self):
        """ if inventory came from a file, what's the directory? """
        if not self.is_file():
            return None
        dname = os.path.dirname(self.host_list)
        if dname is None or dname == '' or dname == '.':
            cwd = os.getcwd()
            return os.path.abspath(cwd) 
        return os.path.abspath(dname)

    def src(self):
        """ if inventory came from a file, what's the directory and file name? """
        if not self.is_file():
            return None
        return self.host_list

    def playbook_basedir(self):
        """ returns the directory of the current playbook """
        return self._playbook_basedir

    def set_playbook_basedir(self, dir):
        """ 
        sets the base directory of the playbook so inventory plugins can use it to find
        variable files and other things. 
        """
        self._playbook_basedir = dir


