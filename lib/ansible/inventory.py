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

    def __init__(self, host_list=C.DEFAULT_HOST_LIST, extra_vars=None):

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
            self.host_list, self.groups = self._parse_from_script(extra_vars)
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

    def get_variables(self, host, extra_vars=None):
        """ Return the variables associated with this host. """

        if host in self._variables:
            return self._variables[host]

        if not self._is_script:
            return {}

        return self._get_variables_from_script(host, extra_vars)

    # *****************************************************

    def _parse_from_file(self):
        ''' parse a textual host file '''

        results = []
        groups = dict(ungrouped=[])
        lines = file(self.inventory_file).read().split("\n")
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

    def _parse_from_script(self, extra_vars=None):
        ''' evaluate a script that returns list of hosts by groups '''

        results = []
        groups = dict(ungrouped=[])

        cmd = [self.inventory_file, '--list']

        if extra_vars:
            cmd.extend(['--extra-vars', extra_vars])

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

    def _get_variables_from_script(self, host, extra_vars=None):
        ''' support per system variabes from external variable scripts, see web docs '''

        cmd = [self.inventory_file, '--host', host]

        if extra_vars:
            cmd.extend(['--extra-vars', extra_vars])

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
