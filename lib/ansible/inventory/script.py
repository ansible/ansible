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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import subprocess
import sys
from collections import Mapping

from ansible.compat.six import iteritems

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.module_utils.basic import json_dict_bytes_to_unicode
from ansible.utils.unicode import to_str, to_unicode


class InventoryScript:
    ''' Host inventory parser for ansible using external inventory scripts. '''

    def __init__(self, loader, groups=None, filename=C.DEFAULT_HOST_LIST):
        if groups is None:
            groups = dict()

        self._loader = loader
        self.groups = groups

        # Support inventory scripts that are not prefixed with some
        # path information but happen to be in the current working
        # directory when '.' is not in PATH.
        self.filename = os.path.abspath(filename)
        cmd = [ self.filename, "--list" ]
        try:
            sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            raise AnsibleError("problem running %s (%s)" % (' '.join(cmd), e))
        (stdout, stderr) = sp.communicate()

        if sp.returncode != 0:
            raise AnsibleError("Inventory script (%s) had an execution error: %s " % (filename,stderr))

        # make sure script output is unicode so that json loader will output
        # unicode strings itself
        try:
            self.data = to_unicode(stdout, errors="strict")
        except Exception as e:
            raise AnsibleError("inventory data from {0} contained characters that cannot be interpreted as UTF-8: {1}".format(to_str(self.filename), to_str(e)))

        # see comment about _meta below
        self.host_vars_from_top = None
        self._parse(stderr)

    def _parse(self, err):

        all_hosts = {}

        # not passing from_remote because data from CMDB is trusted
        try:
            self.raw = self._loader.load(self.data)
        except Exception as e:
            sys.stderr.write(err + "\n")
            raise AnsibleError("failed to parse executable inventory script results from {0}: {1}".format(to_str(self.filename), to_str(e)))

        if not isinstance(self.raw, Mapping):
            sys.stderr.write(err + "\n")
            raise AnsibleError("failed to parse executable inventory script results from {0}: data needs to be formatted as a json dict".format(to_str(self.filename)))

        group = None
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

            if group_name not in self.groups:
                group = self.groups[group_name] = Group(group_name)

            group = self.groups[group_name]
            host = None

            if not isinstance(data, dict):
                data = {'hosts': data}
            # is not those subkeys, then simplified syntax, host with vars
            elif not any(k in data for k in ('hosts','vars','children')):
                data = {'hosts': [group_name], 'vars': data}

            if 'hosts' in data:
                if not isinstance(data['hosts'], list):
                    raise AnsibleError("You defined a group \"%s\" with bad "
                        "data for the host list:\n %s" % (group_name, data))

                for hostname in data['hosts']:
                    if hostname not in all_hosts:
                        all_hosts[hostname] = Host(hostname)
                    host = all_hosts[hostname]
                    group.add_host(host)

            if 'vars' in data:
                if not isinstance(data['vars'], dict):
                    raise AnsibleError("You defined a group \"%s\" with bad "
                        "data for variables:\n %s" % (group_name, data))

                for k, v in iteritems(data['vars']):
                    group.set_variable(k, v)

        # Separate loop to ensure all groups are defined
        for (group_name, data) in self.raw.items():
            if group_name == '_meta':
                continue
            if isinstance(data, dict) and 'children' in data:
                for child_name in data['children']:
                    if child_name in self.groups:
                        self.groups[group_name].add_child_group(self.groups[child_name])

        # Finally, add all top-level groups as children of 'all'.
        # We exclude ungrouped here because it was already added as a child of
        # 'all' at the time it was created.

        for group in self.groups.values():
            if group.depth == 0 and group.name not in ('all', 'ungrouped'):
                self.groups['all'].add_child_group(group)

    def get_host_variables(self, host):
        """ Runs <script> --host <hostname> to determine additional host variables """
        if self.host_vars_from_top is not None:
            try:
                got = self.host_vars_from_top.get(host.name, {})
            except AttributeError as e:
                raise AnsibleError("Improperly formated host information for %s: %s" % (host.name,to_str(e)))
            return got

        cmd = [self.filename, "--host", host.name]
        try:
            sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            raise AnsibleError("problem running %s (%s)" % (' '.join(cmd), e))
        (out, err) = sp.communicate()
        if out.strip() == '':
            return dict()
        try:
            return json_dict_bytes_to_unicode(self._loader.load(out))
        except ValueError:
            raise AnsibleError("could not parse post variable response: %s, %s" % (cmd, out))
