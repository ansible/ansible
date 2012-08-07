# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import subprocess
import ansible.constants as C
from ansible.inventory.ini import InventoryParser
from ansible.inventory.script import InventoryScript
from ansible.inventory.group import Group
from ansible.inventory.host import Host
from ansible import errors
from ansible import utils

class Inventory(object):
    """
    Host inventory for ansible.
    """

    __slots__ = [ 'host_list', 'groups', '_restriction', '_is_script',
                  'parser', '_vars_per_host', '_vars_per_group', '_hosts_cache' ]

    def __init__(self, host_list=C.DEFAULT_HOST_LIST):

        # the host file file, or script path, or list of hosts
        # if a list, inventory data will NOT be loaded
        self.host_list = host_list

        # caching to avoid repeated calculations, particularly with
        # external inventory scripts.

        self._vars_per_host  = {}
        self._vars_per_group = {}
        self._hosts_cache    = {}

        # the inventory object holds a list of groups
        self.groups = []

        # a list of host(names) to contain current inquiries to
        self._restriction = None

        # whether the inventory file is a script
        self._is_script = False

        if type(host_list) in [ str, unicode ]:
            if host_list.find(",") != -1:
                host_list = host_list.split(",")
                host_list = [ h for h in host_list if h and h.strip() ]

        if type(host_list) == list:
            all = Group('all')
            self.groups = [ all ]
            for x in host_list:
                if x.find(":") != -1:
                    tokens = x.split(":",1)
                    all.add_host(Host(tokens[0], tokens[1]))
                else:
                    all.add_host(Host(x))
        elif os.access(host_list, os.X_OK):
            self._is_script = True
            self.parser = InventoryScript(filename=host_list)
            self.groups = self.parser.groups.values()
        else:
            data = file(host_list).read()
            if not data.startswith("---"):
                self.parser = InventoryParser(filename=host_list)
                self.groups = self.parser.groups.values()
            else:
                raise errors.AnsibleError("YAML inventory support is deprecated in 0.6 and removed in 0.7, see the migration script in examples/scripts in the git checkout")

    def _match(self, str, pattern_str):
        return fnmatch.fnmatch(str, pattern_str)

    # TODO: cache this logic so if called a second time the result is not recalculated
    def get_hosts(self, pattern="all"):
        """ Get all host objects matching the pattern """
        hosts = {}
        patterns = pattern.replace(";",":").split(":")

        groups = self.get_groups()
        for pat in patterns:
            if pat.startswith("!"):
                pat = pat[1:]
                inverted = True
            else:
                inverted = False
            for group in groups:
                for host in group.get_hosts():
                    if self._match(group.name, pat) or pat == 'all' or self._match(host.name, pat):
                        # must test explicitly for None because [] means no hosts allowed
                        if self._restriction==None or host.name in self._restriction:
                            if inverted:
                                if host.name in hosts:
                                    del hosts[host.name]
                            else:
                                hosts[host.name] = host
        return sorted(hosts.values(), key=lambda x: x.name)

    def get_groups(self):
        return self.groups

    def get_host(self, hostname):
        if hostname not in self._hosts_cache:
            self._hosts_cache[hostname] = self._get_host(hostname)
        return self._hosts_cache[hostname]

    def _get_host(self, hostname):
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

    def get_variables(self, hostname):
        if hostname not in self._vars_per_host:
            self._vars_per_host[hostname] = self._get_variables(hostname)
        return self._vars_per_host[hostname]

    def _get_variables(self, hostname):

        if self._is_script:
            host = self.get_host(hostname)
            cmd = subprocess.Popen(
                [self.host_list,"--host",hostname],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            (out, err) = cmd.communicate()
            results = utils.parse_json(out)

            # FIXME: this is a bit redundant with host.py and should share code
            results['inventory_hostname'] = hostname
            results['inventory_hostname_short'] = hostname.split('.')[0]
            groups = [ g.name for g in host.get_groups() if g.name != 'all' ]
            results['group_names'] = sorted(groups)

            return results

        host = self.get_host(hostname)
        if host is None:
            raise Exception("host not found: %s" % hostname)
        return host.get_variables()

    def add_group(self, group):
        self.groups.append(group)

    def list_hosts(self, pattern="all"):
        return [ h.name for h in self.get_hosts(pattern) ]

    def list_groups(self):
        return [ g.name for g in self.groups ]

    def get_restriction(self):
        return self._restriction

    def restrict_to(self, restriction, append_missing=False):
        """ Restrict list operations to the hosts given in restriction """
        if type(restriction) != list:
            restriction = [ restriction ]
        self._restriction = restriction

    def lift_restriction(self):
        """ Do not restrict list operations """

        self._restriction = None

    def is_file(self):
        """ did inventory come from a file? """
        if not isinstance(self.host_list, basestring):
            return False
        return os.path.exists(self.host_list)

    def basedir(self):
        """ if inventory came from a file, what's the directory? """
        if not self.is_file():
            return None
        return os.path.dirname(self.host_list)
