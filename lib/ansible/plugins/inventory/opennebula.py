# -*- coding: utf-8 -*-
# Copyright (c) 2020, FELDSAM s.r.o. - FeldHost™ <support@feldhost.cz>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
    name: opennebula
    plugin_type: inventory
    author:
        - Kristian Feldsam
    short_description: OpenNebula inventory source
    version_added: "2.10"
    extends_documentation_fragment:
        - constructed
    description:
        - Get inventory hosts from OpenNebula cloud.
        - Uses an YAML configuration file ending with either I(opennebula.yml), I(opennebula.yaml), I(one.yml)
        - or I(one.yaml) to set parameter values.
        - Uses I(api_authfile), I(~/.one/one_auth), or C(ONE_AUTH) pointing to a OpenNebula credentials file
    options:
        plugin:
            description: Token that ensures this is a source file for the 'opennebula' plugin.
            type: string
            required: True
            choices: [ opennebula ]
        api_url:
            description:
              - URL of the OpenNebula RPC server.
              - It is recommended to use HTTPS so that the username/password are not
              - transferred over the network unencrypted.
              - If not set then the value of the C(ONE_URL) environment variable is used.
            env:
              - name: ONE_URL
            required: True
            type: string
        api_username:
            description:
              - Name of the user to login into the OpenNebula RPC server. If not set
              - then the value of the C(ONE_USERNAME) environment variable is used.
            env:
              - name: ONE_USERNAME
            required: False
            type: string
        api_password:
            description:
              - Password of the user to login into OpenNebula RPC server. If not set
              - then the value of the C(ONE_PASSWORD) environment variable is used.
            env:
              - name: ONE_PASSWORD
            required: False
            type: string
        api_authfile:
            description:
              - if both I(api_username) or I(api_password) are not set, then it will try
              - authenticate with ONE auth file. Default path is "~/.one/one_auth".
              - Set environment variable C(ONE_AUTH) to override this path.
            env:
              - name: ONE_AUTH
            required: False
            type: string
        hostname:
            description: Field to match the hostname. Note v4_first_ip corresponds to the first IPv4 found on VM.
            type: string
            default: v4_first_ip
            choices:
                - v4_first_ip
                - v6_first_ip
                - name
        filter_by_label:
            description: Only return servers filtered by this label
            type: string
'''

EXAMPLES = r'''
# inventory_one.yml file in YAML format
# Example command line: ansible-inventory --list -i inventory_one.yml

# Pass a label filter to the API
plugin: opennebula
api_url: https://opennebula:2633/RPC2
filter_by_label: Cache
'''

try:
    import pyone

    HAS_PYONE = True
except ImportError:
    HAS_PYONE = False

from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.module_utils._text import to_native

import os


def _get_connection_info(url, username, password, authfile):
    if not username:
        if not password:
            if authfile is None:
                authfile = os.path.join(os.environ.get("HOME"), ".one", "one_auth")
            try:
                with open(authfile, "r") as fp:
                    authstring = fp.read().rstrip()
                username = authstring.split(":")[0]
                password = authstring.split(":")[1]
            except (OSError, IOError):
                raise AnsibleError("Could not find or read ONE_AUTH file at '{e}'".format(e=authfile))
            except Exception:
                raise AnsibleError("Error occurs when read ONE_AUTH file at '{e}'".format(e=authfile))

    from collections import namedtuple

    auth_params = namedtuple('auth', ('url', 'username', 'password'))

    return auth_params(url=url, username=username, password=password)


def _get_vm_ipv4(vm):
    nic = vm.TEMPLATE.get('NIC')

    if isinstance(nic, dict):
        nic = [nic]

    for net in nic:
        return net['IP']

    return False


def _get_vm_ipv6(vm):
    nic = vm.TEMPLATE.get('NIC')

    if isinstance(nic, dict):
        nic = [nic]

    for net in nic:
        if net.get('IP6_GLOBAL'):
            return net['IP6_GLOBAL']

    return False


def _retrieve_servers(one_client, label_filter=None):
    # get hosts (VMs)
    try:
        vm_pool = one_client.vmpool.infoextended(-2, -1, -1, 3)
    except Exception as e:
        raise AnsibleError("Something happened durring XML-RPC call, this was original exception: {e}".format(e=to_native(e)))

    result = []

    # iterate over hosts
    for vm in vm_pool.VM:
        server = vm.USER_TEMPLATE

        labels = []
        if vm.USER_TEMPLATE.get('LABELS'):
            labels = vm.USER_TEMPLATE.get('LABELS').split(',')

        # filter by label
        if label_filter is not None:
            if label_filter not in labels:
                continue

        server['name'] = vm.NAME
        server['LABELS'] = labels
        server['v4_first_ip'] = _get_vm_ipv4(vm)
        server['v6_first_ip'] = _get_vm_ipv6(vm)

        result.append(server)

    return result


class InventoryModule(BaseInventoryPlugin, Constructable):
    NAME = 'opennebula'

    def verify_file(self, path):
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('opennebula.yaml', 'opennebula.yml', 'one.yaml', 'one.yml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path=path)

        if not HAS_PYONE:
            raise AnsibleError('OpenNebula Inventory plugin requires pyone to work!')

        auth = _get_connection_info(self.get_option('api_url'),
                                    self.get_option('api_username'),
                                    self.get_option('api_password'),
                                    self.get_option('api_authfile')
                                    )

        if not (auth.username and auth.password):
            raise AnsibleError('API Credentials missing. Check OpenNebula inventory file.')
        else:
            one_client = pyone.OneServer(auth.url, session=auth.username + ':' + auth.password)

        hostname_preference = self.get_option('hostname')

        # Add a top group 'one'
        self.inventory.add_group(group='one')

        # Filter by label is supported by the api with a query
        filter_by_label = self.get_option('filter_by_label')
        for server in _retrieve_servers(one_client, filter_by_label):

            self.inventory.add_host(host=server['name'], group='one')

            for attribute, value in server.items():
                self.inventory.set_variable(server['name'], attribute, value)

            if hostname_preference != 'name':
                self.inventory.set_variable(server['name'], 'ansible_host', server[hostname_preference])

            if server.get('SSH_PORT'):
                self.inventory.set_variable(server['name'], 'ansible_port', server['SSH_PORT'])
