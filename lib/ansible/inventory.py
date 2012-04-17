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

import constants as C
from ansible import errors
from ansible import utils

class Inventory(object):
    """ Host inventory for ansible.

    The inventory is either a simple text file with systems and [groups] of 
    systems, or a script that will be called with --list or --host.
    """

    def __init__(self, host_list=C.DEFAULT_HOST_LIST):

        self._restriction = None
        self._variables = {}

        if type(host_list) == list:
            self.host_list = host_list
            self.groups = dict(ungrouped=host_list)
            self._is_script = False
            return

        inventory_file = os.path.expanduser(host_list)
        if not os.path.exists(inventory_file):
            raise errors.AnsibleFileNotFound("inventory file not found: %s" % host_list)

        self.inventory_file = os.path.abspath(inventory_file)

        if os.access(self.inventory_file, os.X_OK):
            self.host_list, self.groups = self._parse_from_script()
            self._is_script = True
        else:
            self.host_list, self.groups = self._parse_from_file()
            self._is_script = False

    # *****************************************************
    # Public API

    def list_hosts(self, pattern="all"):
        """ Return a list of hosts [matching the pattern] """
        if self._restriction is None:
            host_list = self.host_list
        else:
            host_list = [ h for h in self.host_list if h in self._restriction ]
        return [ h for h in host_list if self._matches(h, pattern) ]

    def restrict_to(self, restriction):
        """ Restrict list operations to the hosts given in restriction """
        if type(restriction)!=list:
            restriction = [ restriction ]

        self._restriction = restriction

    def lift_restriction(self):
        """ Do not restrict list operations """
        self._restriction = None

    def get_variables(self, host):
        """ Return the variables associated with this host. """

        if host in self._variables:
            return self._variables[host].copy()

        if not self._is_script:
            return {}

        return self._get_variables_from_script(host)

    # *****************************************************

    def _parse_from_file(self):
        ''' parse a textual host file '''

        results = []
        groups = dict(ungrouped=[])
        lines = file(self.inventory_file).read().split("\n")
        if "---" in lines:
            return self._parse_yaml()
        group_name = 'ungrouped'
        for item in lines:
            item = item.lstrip().rstrip()
            if item.startswith("#"):
                # ignore commented out lines
                pass
            elif item.startswith("["):
                # looks like a group
                group_name = item.replace("[","").replace("]","").lstrip().rstrip()
                groups[group_name] = []
            elif item != "":
                # looks like a regular host
                if ":" in item:
                    # a port was specified
                    item, port = item.split(":")
                    try:
                        port = int(port)
                    except ValueError:
                        raise errors.AnsibleError("SSH port for %s in inventory (%s) should be numerical."%(item, port))
                    self._set_variable(item, "ansible_ssh_port", port)
                groups[group_name].append(item)
                if not item in results:
                    results.append(item)
        return (results, groups)

    # *****************************************************

    def _parse_from_script(self):
        ''' evaluate a script that returns list of hosts by groups '''

        results = []
        groups = dict(ungrouped=[])

        cmd = [self.inventory_file, '--list']

        cmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        out, err = cmd.communicate()
        rc = cmd.returncode
        if rc:
            raise errors.AnsibleError("%s: %s" % self.inventory_file, err)

        try:
            groups = utils.json_loads(out)
        except:
            raise errors.AnsibleError("invalid JSON response from script: %s" % self.inventory_file)

        for (groupname, hostlist) in groups.iteritems():
            for host in hostlist:
                if host not in results:
                    results.append(host)
        return (results, groups)

    # *****************************************************

    def _parse_yaml(self):
        """ Load the inventory from a yaml file.

        returns hosts and groups"""
        data = utils.parse_yaml_from_file(self.inventory_file)

        if type(data) != list:
            raise errors.AnsibleError("YAML inventory should be a list.")

        hosts = []
        groups = {}

        ungrouped = []

        for item in data:
            if type(item) == dict:
                if "group" in item:
                    group_name = item["group"]

                    group_vars = []
                    if "vars" in item:
                        group_vars = item["vars"]

                    group_hosts = []
                    if "hosts" in item:
                        for host in item["hosts"]:
                            host_name = self._parse_yaml_host(host, group_vars)
                            group_hosts.append(host_name)

                    groups[group_name] = group_hosts
                    hosts.extend(group_hosts)

                elif "host" in item:
                    host_name = self._parse_yaml_host(item)
                    hosts.append(host_name)
                    ungrouped.append(host_name)
            else:
                host_name = self._parse_yaml_host(item)
                hosts.append(host_name)
                ungrouped.append(host_name)

        # filter duplicate hosts
        output_hosts = []
        for host in hosts:
            if host not in output_hosts:
                output_hosts.append(host)

        if len(ungrouped) > 0 :
            # hosts can be defined top-level, but also in a group
            really_ungrouped = []
            for host in ungrouped:
                already_grouped = False
                for name, group_hosts in groups.items():
                    if host in group_hosts:
                        already_grouped = True
                if not already_grouped:
                    really_ungrouped.append(host)
            groups["ungrouped"] = really_ungrouped

        return output_hosts, groups

    def _parse_yaml_host(self, item, variables=[]):
        def set_variables(host, variables):
            for variable in variables:
                if len(variable) != 1:
                    raise AnsibleError("Only one item expected in %s"%(variable))
                k, v = variable.items()[0]
                self._set_variable(host, k, v)

        if type(item) in [str, unicode]:
            set_variables(item, variables)
            return item
        elif type(item) == dict:
            if "host" in item:
                host_name = item["host"]
                set_variables(host_name, variables)

                if "vars" in item:
                    set_variables(host_name, item["vars"])

                return host_name
        else:
            raise AnsibleError("Unknown item in inventory: %s"%(item))


    def _get_variables_from_script(self, host):
        ''' support per system variabes from external variable scripts, see web docs '''

        cmd = [self.inventory_file, '--host', host]

        cmd = subprocess.Popen(cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )
        out, err = cmd.communicate()

        variables = {}
        try:
            variables = utils.json_loads(out)
        except:
            raise errors.AnsibleError("%s returned invalid result when called with hostname %s" % (
                self.inventory_file,
                host
            ))
        return variables

    def _set_variable(self, host, key, value):
        if not host in self._variables:
            self._variables[host] = {}
        self._variables[host][key] = value

    def _matches(self, host_name, pattern):
        ''' returns if a hostname is matched by the pattern '''

        # a pattern is in fnmatch format but more than one pattern
        # can be strung together with semicolons. ex:
        #   atlanta-web*.example.com;dc-web*.example.com

        if host_name == '':
            return False
        pattern = pattern.replace(";",":")
        subpatterns = pattern.split(":")
        for subpattern in subpatterns:
            if subpattern == 'all':
                return True
            if fnmatch.fnmatch(host_name, subpattern):
                return True
            elif subpattern in self.groups:
                if host_name in self.groups[subpattern]:
                    return True
        return False
