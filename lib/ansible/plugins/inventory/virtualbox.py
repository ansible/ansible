# This file is part of Ansible,
# (c) 2012-2017, Michael DeHaan <michael.dehaan@gmail.com>
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
'''
DOCUMENTATION:
    name: virtualbox
    plugin_type: inventory
    short_description: virtualbox inventory source
    description:
        - Get inventory hosts from the local virtualbox installation.
        - Uses a <name>.vbox.yaml (or .vbox.yml) YAML configuration file.
    options:
        running_only:
            description: toggles showing all vms vs only those currently running
            type: boolean
            default: False
        settings_password_file:
            description: provide a file containing the settings password (equivalent to --settingspwfile)
        network_info_path:
            description: property path to query for network information (ansible_host)
            default: "/VirtualBox/GuestInfo/Net/0/V4/IP"
        query:
            description: create vars from virtualbox properties
            type: dictionary
            default: {}
        compose:
            description: create vars from jinja2 expressions, these are created AFTER the query block
            type: dictionary
            default: {}
EXAMPLES:
# file must be named vbox.yaml or vbox.yml
simple_config_file:
    plugin: virtualbox
    settings_password_file: /etc/virtulbox/secrets
    query:
      logged_in_users: /VirtualBox/GuestInfo/OS/LoggedInUsersList
    compose:
      ansible_connection: ('indows' in vbox_Guest_OS)|ternary('winrm', 'ssh')
'''
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from subprocess import Popen, PIPE

from ansible.errors import AnsibleParserError
from ansible.module_utils._text import to_bytes
from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):
    ''' Host inventory parser for ansible using local virtualbox. '''

    NAME = 'virtualbox'
    VBOX = "VBoxManage"

    def _query_vbox_data(self, host, property_path):
        ret = None
        try:
            cmd = [self.VBOX, 'guestproperty', 'get', host, property_path]
            x = Popen(cmd, stdout=PIPE)
            ipinfo = x.stdout.read()
            if 'Value' in ipinfo:
                a, ip = ipinfo.split(':', 1)
                ret = ip.strip()
        except:
            pass
        return ret

    def _set_variables(self, hostvars, data):

        # set vars in inventory from hostvars
        for host in hostvars:

            # create vars from vbox properties
            if data.get('query') and isinstance(data['query'], dict):
                for varname in data['query']:
                    hostvars[host][varname] = self._query_vbox_data(host, data['query'][varname])

            # create composite vars
            if data.get('compose') and isinstance(data['compose'], dict):
                for varname in data['compose']:
                    hostvars[host][varname] = self._compose(data['compose'][varname], hostvars[host])

            # actually update inventory
            for key in hostvars[host]:
                self.inventory.set_variable(host, key, hostvars[host][key])

    def _populate_from_source(self, source_data, config_data):
        hostvars = {}
        prevkey = pref_k = ''
        current_host = None

        # needed to possibly set ansible_host
        netinfo = config_data.get('network_info_path', "/VirtualBox/GuestInfo/Net/0/V4/IP")

        for line in source_data:
            try:
                k, v = line.split(':', 1)
            except:
                # skip non splitable
                continue

            if k.strip() == '':
                # skip empty
                continue

            v = v.strip()
            # found host
            if k.startswith('Name') and ',' not in v:  # some setting strings appear in Name
                current_host = v
                if current_host not in hostvars:
                    hostvars[current_host] = {}
                    self.inventory.add_host(current_host)

                # try to get network info
                netdata = self._query_vbox_data(current_host, netinfo)
                if netdata:
                    self.inventory.set_variable(current_host, 'ansible_host', netdata)

            # found groups
            elif k == 'Groups':
                for group in v.split('/'):
                    if group:
                        self.inventory.add_group(group)
                        self.inventory.add_child(group, current_host)
                continue

            else:
                # found vars, accumulate in hostvars for clean inventory set
                pref_k = 'vbox_' + k.strip().replace(' ', '_')
                if k.startswith(' '):
                    if prevkey not in hostvars[current_host]:
                        hostvars[current_host][prevkey] = {}
                    hostvars[current_host][prevkey][pref_k] = v
                else:
                    if v != '':
                        hostvars[current_host][pref_k] = v

                prevkey = pref_k

        self._set_variables(hostvars, config_data)

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('.vbox.yaml', '.vbox.yml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):

        super(InventoryModule, self).parse(inventory, loader, path)

        cache_key = self.get_cache_prefix(path)

        # file is config file
        try:
            config_data = self.loader.load_from_file(path)
        except Exception as e:
            raise AnsibleParserError(e)

        if not config_data or config_data.get('plugin') != self.NAME:
            # this is not my config file
            return False

        source_data = None
        if cache and cache_key in inventory.cache:
            try:
                source_data = inventory.cache[cache_key]
            except KeyError:
                pass

        if not source_data:
            pwfile = to_bytes(config_data.get('settings_password_file'))
            running = config_data.get('running_only', False)

            # start getting data
            cmd = [self.VBOX, 'list', '-l']
            if running:
                cmd.append('runningvms')
            else:
                cmd.append('vms')

            if pwfile and os.path.exists(pwfile):
                cmd.append('--settingspwfile')
                cmd.append(pwfile)

            try:
                p = Popen(cmd, stdout=PIPE)
            except Exception as e:
                AnsibleParserError(e)

            source_data = p.stdout.readlines()
            inventory.cache[cache_key] = source_data

        self._populate_from_source(source_data, config_data)
