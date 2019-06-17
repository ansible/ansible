# Copyright (c) 2015, Jason DeTiberus <jdetiber@redhat.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

STATES = ('undefined', 'stopped', 'running', 'paused', 'saved')
DOCUMENTATION = '''
    name: libvirt
    plugin_type: inventory
    short_description: libvirt inventory source
    version_added: '2.9'
    requirements:
      - libvirt python library
    author:
      - Jason DeTiberus (@detiber)
      - Brian Coca (@bcoca)
    description:
        - Get inventory hosts via libvirt
        - Uses a <name>.libvirt.yaml (or libvirt.yml) YAML configuration file.
    options:
      uri:
        description: URI to underlying virtualization system
        required: True
      states:
        description: list of states to filter against
        type: list
        default: ['undefined', 'stopped', 'running', 'paused', 'saved']
'''
# % ','.join(STATES)

EXAMPLES = '''
sample_config_file:
    plugin: libvirt
    url: 'qemu:///system'
'''

import xml.etree.ElementTree as ET

try:
    import libvirt
    HAS_LIBVIRT = True
except ImportError:
    HAS_LIBVIRT = False

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin

ansible_ns = {'ansible': 'https://github.com/ansible/ansible'}


class InventoryModule(BaseInventoryPlugin):
    ''' libvirt dynamic inventory '''

    NAME = 'libvirt'

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('.libvirt.yaml', '.libvirt.yml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):
        ''' Construct the inventory '''

        if not HAS_LIBVIRT:
            raise AnsibleParserError("This plugin requires 'libvirt' to operate")

        super(InventoryModule, self).parse(inventory, loader, path)

        self._config_data = self._read_config_data(path)
        self.set_options(direct=self._config_data)

        states = self.get_option('states')
        uri = self.get_option('uri')

        if not states:
            raise AnsibleParserError("At least one state must be specified")
        else:
            invalid = set(states).difference(STATES)
            if invalid:
                raise AnsibleParserError("Invalid states supplied: %s" % invalid)

        conn = libvirt.openReadOnly(uri)
        if conn is None:
            raise AnsibleParserError("Failed to open connection to %s" % uri)
        domains = conn.listAllDomains()
        if domains is None:
            raise AnsibleParserError("Failed to list domains for connection %s" % uri)

        for domain in domains:
            host = domain.name()
            state = domain.state()[0]
            if STATES[state] not in states:
                continue

            # create host and add some vars
            self.inventory.add_host(host)
            self.inventory.set_variable(host, 'libvirt_status', STATES[state])
            self.inventory.set_variable(host, 'libvirt_name', host)
            self.inventory.set_variable(host, 'libvirt_id', domain.ID())
            self.inventory.set_variable(host, 'libvirt_uuid', domain.UUIDString())

            # parse xml for tags
            root = ET.fromstring(domain.XMLDesc())
            tags = []
            for tag_elem in root.findall('./metadata/ansible:tags/ansible:tag', ansible_ns):
                tags.append(tag_elem.text)
            self.inventory.set_variable(host, 'libvirt_tags', tags)

            # Add all iface information
            ifaces = domain.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT, 0) or {}

            self.inventory_set_variable(host, 'libvirt_network', {"interfaces": ifaces})
