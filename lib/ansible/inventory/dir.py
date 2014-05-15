# (c) 2013, Daniel Hokka Zakrisson <daniel@hozac.com>
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

import os
import ansible.constants as C
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.inventory.ini import InventoryParser
from ansible.inventory.script import InventoryScript
from ansible import utils
from ansible import errors

class InventoryDirectory(object):
    ''' Host inventory parser for ansible using a directory of inventories. '''

    def __init__(self, filename=C.DEFAULT_HOST_LIST):
        self.names = os.listdir(filename)
        self.names.sort()
        self.directory = filename
        self.parsers = []
        self.hosts = {}
        self.groups = {}

        for i in self.names:

            # Skip files that end with certain extensions or characters
            if any(i.endswith(ext) for ext in ("~", ".orig", ".bak", ".ini", ".retry", ".pyc", ".pyo")):
                continue
            # Skip hidden files
            if i.startswith('.') and not i.startswith('./'):
                continue
            # These are things inside of an inventory basedir
            if i in ("host_vars", "group_vars", "vars_plugins"):
                continue
            fullpath = os.path.join(self.directory, i)
            if os.path.isdir(fullpath):
                parser = InventoryDirectory(filename=fullpath)
            elif utils.is_executable(fullpath):
                parser = InventoryScript(filename=fullpath)
            else:
                parser = InventoryParser(filename=fullpath)
            self.parsers.append(parser)
            # This takes a lot of code because we can't directly use any of the objects, as they have to blend
            for name, group in parser.groups.iteritems():
                if name not in self.groups:
                    self.groups[name] = group
                else:
                    # group is already there, copy variables
                    # note: depth numbers on duplicates may be bogus
                    for k, v in group.get_variables().iteritems():
                        self.groups[name].set_variable(k, v)
                for host in group.get_hosts():
                    if host.name not in self.hosts:
                        self.hosts[host.name] = host
                    else:
                        # host is already there, copy variables
                        # note: depth numbers on duplicates may be bogus
                        for k, v in host.vars.iteritems():
                            self.hosts[host.name].set_variable(k, v)
                    self.groups[name].add_host(self.hosts[host.name])

            # This needs to be a second loop to ensure all the parent groups exist
            for name, group in parser.groups.iteritems():
                for ancestor in group.get_ancestors():
                    self.groups[ancestor.name].add_child_group(self.groups[name])

    def get_host_variables(self, host):
        """ Gets additional host variables from all inventories """
        vars = {}
        for i in self.parsers:
            vars.update(i.get_host_variables(host))
        return vars

