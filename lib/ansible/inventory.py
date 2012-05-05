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

import constants as C
from ansible.inventory_parser import InventoryParser
from ansible.group import Group
from ansible.host import Host
from ansible import errors
from ansible import utils

class Inventory(object):
    """ 
    Host inventory for ansible.
    """

    def __init__(self, host_list=C.DEFAULT_HOST_LIST):

        # FIXME: re-support YAML inventory format
        # FIXME: re-support external inventory script (?)

        self.groups = []
        self._restriction = None
        if host_list:
            if type(host_list) == list:
                self.groups = self._groups_from_override_hosts(host_list)
            else:
                self.parser = InventoryParser(filename=host_list)
                self.groups = self.parser.groups.values()
                
    def _groups_from_override_hosts(self, list):
        # support for playbook's --override-hosts only
        all = Group(name='all') 
        for h in list:
            all.add_host(Host(name=h))
        return dict(all=all) 

    def _match(self, str, pattern_str):
        return fnmatch.fnmatch(str, pattern_str)

    def get_hosts(self, pattern="all"):
        """ Get all host objects matching the pattern """
        hosts = {}
        patterns = pattern.replace(";",":").split(":")

        for group in self.get_groups():
             for host in group.get_hosts():
                 for pat in patterns:
                     if group.name == pat or pat == 'all' or self._match(host.name, pat):
                         if not self._restriction:
                             hosts[host.name] = host
                         if self._restriction and host.name in self._restriction:
                             hosts[host.name] = host
        return sorted(hosts.values(), key=lambda x: x.name)

    def get_groups(self):
        return self.groups

    def get_host(self, hostname):
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
        group = self.get_group(groupname)
        if group is None:
            raise Exception("group not found: %s" % groupname)
        return group.get_variables()

    def get_variables(self, hostname):
        host = self.get_host(hostname)
        if host is None:
            raise Exception("host not found: %s" % hostname)
        return host.get_variables()

    def add_group(self, group):
        self.groups.append(group)

    def list_hosts(self, pattern="all"):
        """ DEPRECATED: Get all host names matching the pattern """
        return [ h.name for h in self.get_hosts(pattern) ]

    def list_groups(self):
        return [ g.name for g in self.groups ] 

    def restrict_to(self, restriction):
        """ Restrict list operations to the hosts given in restriction """
        if type(restriction) != list:
            restriction = [ restriction ]
        self._restriction = restriction

    def lift_restriction(self):
        """ Do not restrict list operations """
        self._restriction = None

