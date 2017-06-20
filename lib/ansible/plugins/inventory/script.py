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
'''
DOCUMENTATION:
    inventory: script
    version_added: "2.4"
    short_description: Executes an inventory script that returns JSON
    description:
        - The source provided must an executable that returns Ansible inventory JSON
        - The source must accept C(--list) and C(--host <hostname>) as arguments.
          C(--host) will only be used if no C(_meta) key is present (performance optimization)
    notes:
        - It takes the place of the previously hardcoded script inventory.
        - To function it requires being whitelisted in configuration, which is true by default.
'''
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import subprocess
from collections import Mapping

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils.basic import json_dict_bytes_to_unicode
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native, to_text
from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):
    ''' Host inventory parser for ansible using external inventory scripts. '''

    NAME = 'script'

    def __init__(self):

        super(InventoryModule, self).__init__()

        self._hosts = set()

    def verify_file(self, path):
        ''' Verify if file is usable by this plugin, base does minimal accesability check '''

        valid = super(InventoryModule, self).verify_file(path)

        if valid:
            # not only accessible, file must be executable and/or have shebang
            shebang_present = False
            try:
                with open(path, 'rb') as inv_file:
                    initial_chars = inv_file.read(2)
                    if initial_chars.startswith(b'#!'):
                        shebang_present = True
            except:
                pass

            if not os.access(path, os.X_OK) and not shebang_present:
                valid = False

        return valid

    def parse(self, inventory, loader, path, cache=True):

        super(InventoryModule, self).parse(inventory, loader, path)

        # Support inventory scripts that are not prefixed with some
        # path information but happen to be in the current working
        # directory when '.' is not in PATH.
        cmd = [path, "--list"]

        try:
            cache_key = self.get_cache_prefix(path)
            if not cache or cache_key not in inventory.cache:
                try:
                    sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except OSError as e:
                    raise AnsibleParserError("problem running %s (%s)" % (' '.join(cmd), to_native(e)))
                (stdout, stderr) = sp.communicate()

                path = to_native(path)
                if stderr:
                    err = to_native(stderr) + "\n"

                if sp.returncode != 0:
                    raise AnsibleError("Inventory script (%s) had an execution error: %s " % (path, err))

                # make sure script output is unicode so that json loader will output
                # unicode strings itself
                try:
                    data = to_text(stdout, errors="strict")
                except Exception as e:
                    raise AnsibleError("Inventory {0} contained characters that cannot be interpreted as UTF-8: {1}".format(path, to_native(e)))

                try:
                    inventory.cache[cache_key] = self.loader.load(data, file_name=path)
                except Exception as e:
                    raise AnsibleError("failed to parse executable inventory script results from {0}: {1}\n{2}".format(path, to_native(e), err))

            processed = inventory.cache[cache_key]
            if not isinstance(processed, Mapping):
                raise AnsibleError("failed to parse executable inventory script results from {0}: needs to be a json dict\n{1}".format(path, err))

            group = None
            data_from_meta = None

            # A "_meta" subelement may contain a variable "hostvars" which contains a hash for each host
            # if this "hostvars" exists at all then do not call --host for each # host.
            # This is for efficiency and scripts should still return data
            # if called with --host for backwards compat with 1.2 and earlier.
            for (group, gdata) in processed.items():
                if group == '_meta':
                    if 'hostvars' in gdata:
                        data_from_meta = gdata['hostvars']
                else:
                    self._parse_group(group, gdata)

            for host in self._hosts:
                got = {}
                if data_from_meta is None:
                    got = self.get_host_variables(path, host)
                else:
                    try:
                        got = data_from_meta.get(host, {})
                    except AttributeError as e:
                        raise AnsibleError("Improperly formatted host information for %s: %s" % (host, to_native(e)))

                self.populate_host_vars([host], got)

        except Exception as e:
            raise AnsibleParserError(to_native(e))

    def _parse_group(self, group, data):

        self.inventory.add_group(group)

        if not isinstance(data, dict):
            data = {'hosts': data}
        # is not those subkeys, then simplified syntax, host with vars
        elif not any(k in data for k in ('hosts', 'vars', 'children')):
            data = {'hosts': [group], 'vars': data}

        if 'hosts' in data:
            if not isinstance(data['hosts'], list):
                raise AnsibleError("You defined a group '%s' with bad data for the host list:\n %s" % (group, data))

            for hostname in data['hosts']:
                self._hosts.add(hostname)
                self.inventory.add_host(hostname, group)

        if 'vars' in data:
            if not isinstance(data['vars'], dict):
                raise AnsibleError("You defined a group '%s' with bad data for variables:\n %s" % (group, data))

            for k, v in iteritems(data['vars']):
                self.inventory.set_variable(group, k, v)

        if group != '_meta' and isinstance(data, dict) and 'children' in data:
            for child_name in data['children']:
                self.inventory.add_group(child_name)
                self.inventory.add_child(group, child_name)

    def get_host_variables(self, path, host):
        """ Runs <script> --host <hostname>, to determine additional host variables """

        cmd = [path, "--host", host]
        try:
            sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            raise AnsibleError("problem running %s (%s)" % (' '.join(cmd), e))
        (out, err) = sp.communicate()
        if out.strip() == '':
            return {}
        try:
            return json_dict_bytes_to_unicode(self.loader.load(out, file_name=path))
        except ValueError:
            raise AnsibleError("could not parse post variable response: %s, %s" % (cmd, out))
