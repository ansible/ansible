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

import os
import subprocess
import ansible.constants as C
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.module_utils.basic import json_dict_bytes_to_unicode
from ansible import utils
from ansible import errors
import sys


class InventoryScript(object):
    ''' Host inventory parser for ansible using external inventory scripts. '''

    def __init__(self, filename=C.DEFAULT_HOST_LIST):

        # Support inventory scripts that are not prefixed with some
        # path information but happen to be in the current working
        # directory when '.' is not in PATH.
        self.filename = os.path.abspath(filename)
        cmd = [ self.filename, "--list" ]
        try:
            sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError, e:
            raise errors.AnsibleError("problem running %s (%s)" % (' '.join(cmd), e))
        (stdout, stderr) = sp.communicate()

        if sp.returncode != 0:
            raise errors.AnsibleError("Inventory script (%s) had an execution error: %s " % (filename,stderr))

        self.data = stdout
        # see comment about _meta below
        self.host_vars_from_top = None
        self.groups = self._parse(stderr)


    def _parse(self, err):

        all_hosts = {}

        # not passing from_remote because data from CMDB is trusted
        self.raw  = utils.parse_json(self.data)
        self.raw  = json_dict_bytes_to_unicode(self.raw)

        all       = Group('all')
        groups    = dict(all=all)
        group     = None


        if 'failed' in self.raw:
            sys.stderr.write(err + "\n")
            raise errors.AnsibleError("failed to parse executable inventory script results: %s" % self.raw)

        for (group_name, data) in self.raw.items():

            # in Ansible 1.3 and later, a "_meta" subelement may contain
            # a variable "hostvars" which contains a hash for each host
            # if this "hostvars" exists at all then do not call --host for each
            # host.  This is for efficiency and scripts should still return data
            # if called with --host for backwards compat with 1.2 and earlier.

            if group_name == '_meta':
                if 'hostvars' in data:
                    self.host_vars_from_top = data['hostvars']
                    continue

            if group_name != all.name:
                group = groups[group_name] = Group(group_name)
            else:
                group = all
            host = None

            if not isinstance(data, dict):
                data = {'hosts': data}
            # is not those subkeys, then simplified syntax, host with vars
            elif not any(k in data for k in ('hosts','vars','children')):
                data = {'hosts': [group_name], 'vars': data}

            if 'hosts' in data:
                if not isinstance(data['hosts'], list):
                    raise errors.AnsibleError("You defined a group \"%s\" with bad "
                        "data for the host list:\n %s" % (group_name, data))

                for hostname in data['hosts']:
                    if not hostname in all_hosts:
                        all_hosts[hostname] = Host(hostname)
                    host = all_hosts[hostname]
                    group.add_host(host)

            if 'vars' in data:
                if not isinstance(data['vars'], dict):
                    raise errors.AnsibleError("You defined a group \"%s\" with bad "
                        "data for variables:\n %s" % (group_name, data))

                for k, v in data['vars'].iteritems():
                    if group.name == all.name:
                        all.set_variable(k, v)
                    else:
                        group.set_variable(k, v)

        # Separate loop to ensure all groups are defined
        for (group_name, data) in self.raw.items():
            if group_name == '_meta':
                continue
            if isinstance(data, dict) and 'children' in data:
                for child_name in data['children']:
                    if child_name in groups:
                        groups[group_name].add_child_group(groups[child_name])

        for group in groups.values():
            if group.depth == 0 and group.name != 'all':
                all.add_child_group(group)

        return groups

    def get_host_variables(self, host):
        """ Runs <script> --host <hostname> to determine additional host variables """
        if self.host_vars_from_top is not None:
            got = self.host_vars_from_top.get(host.name, {})
            return got


        cmd = [self.filename, "--host", host.name]
        try:
            sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError, e:
            raise errors.AnsibleError("problem running %s (%s)" % (' '.join(cmd), e))
        (out, err) = sp.communicate()
        if out.strip() == '':
            return dict()
        try:
            return json_dict_bytes_to_unicode(utils.parse_json(out))
        except ValueError:
            raise errors.AnsibleError("could not parse post variable response: %s, %s" % (cmd, out))

