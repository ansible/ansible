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
from ansible import errors
from ansible import utils

class InventoryParserYaml(object):
    """ 
    Host inventory for ansible.
    """

    def __init__(self, filename=C.DEFAULT_HOST_LIST):

        fh = open(filename)
        data = fh.read()
        fh.close()
        self._hosts = {}
        self._parse(data)

    def _make_host(self, hostname):
        if hostname in self._hosts:
            return self._hosts[hostname]
        else:
            host = Host(hostname)
            self._hosts[hostname] = host
            return host 

    # see file 'test/yaml_hosts' for syntax

    def _parse(self, data):

        all = Group('all')
        ungrouped = Group('ungrouped')
        all.add_child_group(ungrouped)

        self.groups = dict(all=all, ungrouped=ungrouped)
        grouped_hosts = []

        yaml = utils.parse_yaml(data)

        # first add all groups
        for item in yaml:
            if type(item) == dict and 'group' in item:
                group = Group(item['group'])

                for subresult in item.get('hosts',[]):

                    if type(subresult) in [ str, unicode ]:
                        host = self._make_host(subresult)
                        group.add_host(host)
                        grouped_hosts.append(host)
                    elif type(subresult) == dict:
                        host = self._make_host(subresult['host'])
                        vars = subresult.get('vars',{})
                        if type(vars) == list:
                            for subitem in vars:
                                for (k,v) in subitem.items():
                                    host.set_variable(k,v) 
                        elif type(vars) == dict:
                            for (k,v) in subresult.get('vars',{}).items():
                                host.set_variable(k,v)
                        else:
                            raise errors.AnsibleError("unexpected type for variable")
                        group.add_host(host)
                        grouped_hosts.append(host)

                vars = item.get('vars',{})
                if type(vars) == dict:
                    for (k,v) in item.get('vars',{}).items():
                        group.set_variable(k,v) 
                elif type(vars) == list:
                    for subitem in vars:
                        if type(subitem) != dict:
                            raise errors.AnsibleError("expected a dictionary")
                        for (k,v) in subitem.items():
                            group.set_variable(k,v)

                self.groups[group.name] = group
                all.add_child_group(group)

        # add host definitions
        for item in yaml:
            if type(item) in [ str, unicode ]:
                host = self._make_host(item)
                if host not in grouped_hosts:
                    ungrouped.add_host(host)

            elif type(item) == dict and 'host' in item:
                host = self._make_host(item['host'])

                vars = item.get('vars', {})
                if type(vars)==list:
                    varlist, vars = vars, {}
                    for subitem in varlist:
                        vars.update(subitem)
                for (k,v) in vars.items():
                    host.set_variable(k,v)

                groups = item.get('groups', {})
                if type(groups) in [ str, unicode ]:
                    groups = [ groups ]
                if type(groups)==list:
                    for subitem in groups:
                        if subitem in self.groups:
                            group = self.groups[subitem]
                        else:
                            group = Group(subitem)
                            self.groups[group.name] = group
                            all.add_child_group(group)
                        group.add_host(host)
                        grouped_hosts.append(host)

                if host not in grouped_hosts:
                    ungrouped.add_host(host)

        # make sure ungrouped.hosts is the complement of grouped_hosts
        ungrouped_hosts = [host for host in ungrouped.hosts if host not in grouped_hosts]
