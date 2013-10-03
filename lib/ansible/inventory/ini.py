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

import ansible.constants as C
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.inventory.expand_hosts import detect_range
from ansible.inventory.expand_hosts import expand_hostname_range
from ansible import errors
import shlex
import re
import ast

class InventoryParser(object):
    """
    Host inventory for ansible.
    """

    def __init__(self, filename=C.DEFAULT_HOST_LIST):

        with open(filename) as fh:
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
        # FIXME: refactor

        ungrouped = Group(name='ungrouped')
        all = Group(name='all')
        all.add_child_group(ungrouped)

        self.groups = dict(all=all, ungrouped=ungrouped)
        active_group_name = 'ungrouped'

        for line in self.lines:
            line = line.split("#")[0].strip()
            if line.startswith("[") and line.endswith("]"):
                active_group_name = line.replace("[","").replace("]","")
                if line.find(":vars") != -1 or line.find(":children") != -1:
                    active_group_name = active_group_name.rsplit(":", 1)[0]
                    if active_group_name not in self.groups:
                        new_group = self.groups[active_group_name] = Group(name=active_group_name)
                        all.add_child_group(new_group)
                    active_group_name = None
                elif active_group_name not in self.groups:
                    new_group = self.groups[active_group_name] = Group(name=active_group_name)
                    all.add_child_group(new_group)
            elif line.startswith(";") or line == '':
                pass
            elif active_group_name:
                tokens = shlex.split(line)
                if len(tokens) == 0:
                    continue
                hostname = tokens[0]
                port = C.DEFAULT_REMOTE_PORT
                # Three cases to check:
                # 0. A hostname that contains a range pesudo-code and a port
                # 1. A hostname that contains just a port
                if hostname.count(":") > 1:
                    # probably an IPv6 addresss, so check for the format
                    # XXX:XXX::XXX.port, otherwise we'll just assume no
                    # port is set 
                    if hostname.find(".") != -1:
                        (hostname, port) = hostname.rsplit(".", 1)
                elif (hostname.find("[") != -1 and
                    hostname.find("]") != -1 and
                    hostname.find(":") != -1 and
                    (hostname.rindex("]") < hostname.rindex(":")) or
                    (hostname.find("]") == -1 and hostname.find(":") != -1)):
                        (hostname, port) = hostname.rsplit(":", 1)

                hostnames = []
                if detect_range(hostname):
                    hostnames = expand_hostname_range(hostname)
                else:
                    hostnames = [hostname]

                for hn in hostnames:
                    host = None
                    if hn in self.hosts:
                        host = self.hosts[hn]
                    else:
                        host = Host(name=hn, port=port)
                        self.hosts[hn] = host
                    if len(tokens) > 1:
                        for t in tokens[1:]:
                            if t.startswith('#'):
                                break
                            try:
                                (k,v) = t.split("=")
                            except ValueError, e:
                                raise errors.AnsibleError("Invalid ini entry: %s - %s" % (t, str(e)))
                            try:
                                host.set_variable(k,ast.literal_eval(v))
                            except:
                                # most likely a string that literal_eval
                                # doesn't like, so just set it
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
            elif line.startswith("#") or line.startswith(";"):
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
            elif line.startswith("#") or line.startswith(";"):
                pass
            elif line.startswith("["):
                group = None
            elif line == '':
                pass
            elif group:
                if line.find("=") == -1:
                    raise errors.AnsibleError("variables assigned to group must be in key=value form")
                else:
                    (k, v) = [e.strip() for e in line.split("=", 1)]
                    # When the value is a single-quoted or double-quoted string
                    if re.match(r"^(['\"]).*\1$", v):
                        # Unquote the string
                        group.set_variable(k, re.sub(r"^['\"]|['\"]$", '', v))
                    else:
                        group.set_variable(k, v)

    def get_host_variables(self, host):
        return {}
