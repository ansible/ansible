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
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible import errors
from ansible import utils

class InventoryParser(object):
    """ 
    Host inventory for ansible.
    """

    def __init__(self, filename=C.DEFAULT_HOST_LIST):

        fh = open(filename)
        self.lines = fh.readlines()
        self.groups = {}
        self.hosts = {}
        self._parse()
 
    def _parse(self):

        self._parse_base_groups()
        self._parse_group_children()
        self._parse_group_variables()
        return self.groups

    # [webservers]
    # alpha
    # beta:2345
    # gamma sudo=True user=root
    # delta asdf=jkl favcolor=red 

    def _parse_base_groups(self):

        ungrouped = Group(name='ungrouped')
        all = Group(name='all')
        all.add_child_group(ungrouped)

        self.groups = dict(all=all, ungrouped=ungrouped)
        active_group_name = 'ungrouped'

        for line in self.lines:
            if line.startswith("["):
                active_group_name = line.replace("[","").replace("]","").strip()
                if line.find(":vars") != -1 or line.find(":children") != -1:
                    active_group_name = None
                else:
                    new_group = self.groups[active_group_name] = Group(name=active_group_name)
                    all.add_child_group(new_group)
            elif line.startswith("#") or line == '':
                pass
            elif active_group_name:
                tokens = line.split()
                if len(tokens) == 0:
                    continue
                hostname = tokens[0]
                port = C.DEFAULT_REMOTE_PORT
                if hostname.find(":") != -1:
                   tokens2  = hostname.split(":")
                   hostname = tokens2[0]
                   port     = tokens2[1]
                host = None
                if hostname in self.hosts:
                    host = self.hosts[hostname]
                else:
                    host = Host(name=hostname, port=port)
                    self.hosts[hostname] = host
                if len(tokens) > 1:
                   for t in tokens[1:]:
                      (k,v) = t.split("=")
                      host.set_variable(k,v)
                self.groups[active_group_name].add_host(host)

    # [southeast:children]
    # atlanta
    # raleigh

    def _parse_group_children(self):
        group = None

        for line in self.lines:
            line = line.strip()
            if line is None or line == '':
                continue
            if line.startswith("[") and line.find(":children]") != -1:
                line = line.replace("[","").replace(":children]","")
                group = self.groups.get(line, None)
                if group is None:
                    group = self.groups[line] = Group(name=line)
            elif line.startswith("#"):
                pass
            elif line.startswith("["):
                group = None
            elif group:
                kid_group = self.groups.get(line, None)
                if kid_group is None:
                    raise errors.AnsibleError("child group is not defined: (%s)" % line)
                else:
                    group.add_child_group(kid_group)


    # [webservers:vars]
    # http_port=1234
    # maxRequestsPerChild=200

    def _parse_group_variables(self):
        group = None
        for line in self.lines:
            line = line.strip()
            if line.startswith("[") and line.find(":vars]") != -1:
                line = line.replace("[","").replace(":vars]","")
                group = self.groups.get(line, None)
                if group is None:
                   raise errors.AnsibleError("can't add vars to undefined group: %s" % line)
            elif line.startswith("#"):
                pass
            elif line.startswith("["):
                group = None
            elif line == '':
                pass
            elif group:
                if line.find("=") == -1:
                    raise errors.AnsibleError("variables assigned to group must be in key=value form")
                else:
                    (k,v) = line.split("=")
                    group.set_variable(k,v)


