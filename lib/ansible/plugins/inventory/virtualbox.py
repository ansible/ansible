# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: virtualbox
    plugin_type: inventory
    short_description: virtualbox inventory source
    description:
        - Get inventory hosts from the local virtualbox installation.
        - Uses a <name>.vbox.yaml (or .vbox.yml) YAML configuration file.
        - The inventory_hostname is always the 'Name' of the virtualbox instance.
    extends_documentation_fragment:
      - constructed
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
'''

EXAMPLES = '''
# file must be named vbox.yaml or vbox.yml
simple_config_file:
    plugin: virtualbox
    settings_password_file: /etc/virtulbox/secrets
    query:
      logged_in_users: /VirtualBox/GuestInfo/OS/LoggedInUsersList
    compose:
      ansible_connection: ('indows' in vbox_Guest_OS)|ternary('winrm', 'ssh')
'''

import os

from collections import MutableMapping
from subprocess import Popen, PIPE

from ansible.errors import AnsibleParserError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    ''' Host inventory parser for ansible using local virtualbox. '''

    NAME = 'virtualbox'
    VBOX = b"VBoxManage"

    def _query_vbox_data(self, host, property_path):
        ret = None
        try:
            cmd = [self.VBOX, b'guestproperty', b'get', to_bytes(host, errors='surrogate_or_strict'), to_bytes(property_path, errors='surrogate_or_strict')]
            x = Popen(cmd, stdout=PIPE)
            ipinfo = to_text(x.stdout.read(), errors='surrogate_or_strict')
            if 'Value' in ipinfo:
                a, ip = ipinfo.split(':', 1)
                ret = ip.strip()
        except:
            pass
        return ret

    def _set_variables(self, hostvars):

        # set vars in inventory from hostvars
        for host in hostvars:

            query = self.get_option('query')
            # create vars from vbox properties
            if query and isinstance(query, MutableMapping):
                for varname in query:
                    hostvars[host][varname] = self._query_vbox_data(host, query[varname])

            # create composite vars
            self._set_composite_vars(self.get_option('compose'), hostvars, host)

            # actually update inventory
            for key in hostvars[host]:
                self.inventory.set_variable(host, key, hostvars[host][key])

            # constructed groups based on conditionals
            self._add_host_to_composed_groups(self.get_option('groups'), hostvars, host)

    def _populate_from_source(self, source_data):
        hostvars = {}
        prevkey = pref_k = ''
        current_host = None

        # needed to possibly set ansible_host
        netinfo = self.get_option('network_info_path')

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

        self._set_variables(hostvars)

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('.vbox.yaml', '.vbox.yml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):

        super(InventoryModule, self).parse(inventory, loader, path)

        cache_key = self._get_cache_prefix(path)

        config_data = self._read_config_data(path)

        # set _options from config data
        self._consume_options(config_data)

        source_data = None
        if cache and cache_key in self._cache:
            try:
                source_data = self._cache[cache_key]
            except KeyError:
                pass

        if not source_data:
            b_pwfile = to_bytes(self.get_option('settings_password_file'), errors='surrogate_or_strict')
            running = self.get_option('running_only')

            # start getting data
            cmd = [self.VBOX, b'list', b'-l']
            if running:
                cmd.append(b'runningvms')
            else:
                cmd.append(b'vms')

            if b_pwfile and os.path.exists(b_pwfile):
                cmd.append(b'--settingspwfile')
                cmd.append(b_pwfile)

            try:
                p = Popen(cmd, stdout=PIPE)
            except Exception as e:
                AnsibleParserError(to_native(e))

            source_data = p.stdout.read()
            self._cache[cache_key] = to_text(source_data, errors='surrogate_or_strict')

        self._populate_from_source(source_data.splitlines())
