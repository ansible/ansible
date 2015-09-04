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

import ansible.constants as C
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible import errors
from ansible import utils
import os
import yaml
import sys
from six import iteritems

class InventoryParserYaml(object):
    ''' Host inventory parser for ansible '''

    def __init__(self, filename=C.DEFAULT_HOST_LIST):

        sys.stderr.write("WARNING: YAML inventory files are deprecated in 0.6 and will be removed in 0.7, to migrate" +
            " download and run https://github.com/ansible/ansible/blob/devel/examples/scripts/yaml_to_ini.py\n")

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
        # FIXME: refactor into subfunctions

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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "usage: yaml_to_ini.py /path/to/ansible/hosts"
        sys.exit(1)

    result = ""

    original = sys.argv[1]
    yamlp = InventoryParserYaml(filename=sys.argv[1])
    dirname = os.path.dirname(original)

    group_names = [ g.name for g in yamlp.groups.values() ]

    for group_name in sorted(group_names):

        record = yamlp.groups[group_name]

        if group_name == 'all':
            continue

        hosts = record.hosts
        result = result + "[%s]\n" % record.name
        for h in hosts:
            result = result + "%s\n" % h.name
        result = result + "\n"

        groupfiledir = os.path.join(dirname, "group_vars")
        if not os.path.exists(groupfiledir):
            print "* creating: %s" % groupfiledir
            os.makedirs(groupfiledir)
        groupfile = os.path.join(groupfiledir, group_name)
        print "* writing group variables for %s into %s" % (group_name, groupfile)
        groupfh = open(groupfile, 'w')
        groupfh.write(yaml.dump(record.get_variables()))
        groupfh.close()

    for (host_name, host_record) in iteritems(yamlp._hosts):
        hostfiledir = os.path.join(dirname, "host_vars")
        if not os.path.exists(hostfiledir):
            print "* creating: %s" % hostfiledir
            os.makedirs(hostfiledir)
        hostfile = os.path.join(hostfiledir, host_record.name)
        print "* writing host variables for %s into %s" % (host_record.name, hostfile)
        hostfh = open(hostfile, 'w')
        hostfh.write(yaml.dump(host_record.get_variables()))
        hostfh.close()


    # also need to keep a hash of variables per each host
    # and variables per each group
    # and write those to disk

    newfilepath = os.path.join(dirname, "hosts.new")
    fdh = open(newfilepath, 'w')
    fdh.write(result)
    fdh.close()

    print "* COMPLETE: review your new inventory file and replace your original when ready"
    print "*           new inventory file saved as %s" % newfilepath
    print "*           edit group specific variables in %s/group_vars/" % dirname
    print "*           edit host specific variables in %s/host_vars/" % dirname

    # now need to write this to disk as (oldname).new
    # and inform the user
