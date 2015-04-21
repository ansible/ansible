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

import ansible.constants as C
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.inventory.expand_hosts import detect_range
from ansible.inventory.expand_hosts import expand_hostname_range
from ansible import errors
from ansible import utils
import shlex
import re
import ast

class InventoryParser(object):
    """
    Host inventory for ansible.
    """

    def __init__(self, filename=C.DEFAULT_HOST_LIST):

        with open(filename) as fh:
            self.filename = filename
            self.lines = fh.readlines()
            self.groups = {}
            self.hosts = {}
            self._parse()

    def _parse(self):

        self._parse_base_groups()
        self._parse_group_children()
        self._add_allgroup_children()
        self._parse_group_variables()
        return self.groups

    @staticmethod
    def _parse_value(v):
        if "#" not in v:
            try:
                ret = ast.literal_eval(v)
                if not isinstance(ret, float):
                    # Do not trim floats. Eg: "1.20" to 1.2
                    return ret
            # Using explicit exceptions.
            # Likely a string that literal_eval does not like. We wil then just set it.
            except ValueError:
                # For some reason this was thought to be malformed.
                pass
            except SyntaxError:
                # Is this a hash with an equals at the end?
                pass
        return v

    # [webservers]
    # alpha
    # beta:2345
    # gamma sudo=True user=root
    # delta asdf=jkl favcolor=red

    def _add_allgroup_children(self):

        for group in self.groups.values():
            if group.depth == 0 and group.name != 'all':
                self.groups['all'].add_child_group(group)


    def _parse_base_groups(self):
        # FIXME: refactor

        ungrouped = Group(name='ungrouped')
        all = Group(name='all')
        all.add_child_group(ungrouped)

        self.groups = dict(all=all, ungrouped=ungrouped)
        active_group_name = 'ungrouped'

        for lineno in range(len(self.lines)):
            line = utils.before_comment(self.lines[lineno]).strip()
            if line.startswith("[") and line.endswith("]"):
                active_group_name = line.replace("[","").replace("]","")
                if ":vars" in line or ":children" in line:
                    active_group_name = active_group_name.rsplit(":", 1)[0]
                    if active_group_name not in self.groups:
                        new_group = self.groups[active_group_name] = Group(name=active_group_name)
                    active_group_name = None
                elif active_group_name not in self.groups:
                    new_group = self.groups[active_group_name] = Group(name=active_group_name)
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
                    # Possible an IPv6 address, or maybe a host line with multiple ranges
                    # IPv6 with Port  XXX:XXX::XXX.port
                    # FQDN            foo.example.com
                    if hostname.count(".") == 1:
                        (hostname, port) = hostname.rsplit(".", 1)
                elif ("[" in hostname and
                    "]" in hostname and
                    ":" in hostname and
                    (hostname.rindex("]") < hostname.rindex(":")) or
                    ("]" not in hostname and ":" in hostname)):
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
                                (k,v) = t.split("=", 1)
                            except ValueError, e:
                                raise errors.AnsibleError("%s:%s: Invalid ini entry: %s - %s" % (self.filename, lineno + 1, t, str(e)))
                            host.set_variable(k, self._parse_value(v))
                    self.groups[active_group_name].add_host(host)

    # [southeast:children]
    # atlanta
    # raleigh

    def _parse_group_children(self):
        group = None

        for lineno in range(len(self.lines)):
            line = self.lines[lineno].strip()
            if line is None or line == '':
                continue
            if line.startswith("[") and ":children]" in line:
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
                    raise errors.AnsibleError("%s:%d: child group is not defined: (%s)" % (self.filename, lineno + 1, line))
                else:
                    group.add_child_group(kid_group)


    # [webservers:vars]
    # http_port=1234
    # maxRequestsPerChild=200

    def _parse_group_variables(self):
        group = None
        for lineno in range(len(self.lines)):
            line = self.lines[lineno].strip()
            if line.startswith("[") and ":vars]" in line:
                line = line.replace("[","").replace(":vars]","")
                group = self.groups.get(line, None)
                if group is None:
                    raise errors.AnsibleError("%s:%d: can't add vars to undefined group: %s" % (self.filename, lineno + 1, line))
            elif line.startswith("#") or line.startswith(";"):
                pass
            elif line.startswith("["):
                group = None
            elif line == '':
                pass
            elif group:
                if "=" not in line:
                    raise errors.AnsibleError("%s:%d: variables assigned to group must be in key=value form" % (self.filename, lineno + 1))
                else:
                    (k, v) = [e.strip() for e in line.split("=", 1)]
                    group.set_variable(k, self._parse_value(v))

    def get_host_variables(self, host):
        return {}
