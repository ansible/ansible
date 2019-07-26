# -*- coding: utf-8 -*-

# Copyright: (c) 2019. Chris Mills <chris@discreet-its.co.uk>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
netbox.py

A lookup function designed to return data from the Netbox application
"""

from __future__ import (absolute_import, division, print_function)

from pprint import pformat

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

import pynetbox

__metaclass__ = type

DOCUMENTATION = """
    lookup: netbox
    author: Chris Mills (@cpmills1975)
    version_added: "2.9"
    short_description: Queries and returns elements from Netbox
    description:
        - Queries Netbox via its API to return virtually any information
          capable of being held in Netbox.
        - While secrets can be queried, the plugin doesn't yet support
          decrypting them.
    options:
        _terms:
            description:
                - The Netbox object type to query
            required: True
        api_endpoint:
            description:
                - The URL to the Netbox instance to query
            required: True
        token:
            description:
                - The API token created through Netbox
            required: True
    requirements:
        - pynetbox
"""

EXAMPLES = """
tasks:
  # query a list of devices
  - name: Obtain list of devices from Netbox
    debug:
      msg: >
        "Device {{ item.value.display_name }} (ID: {{ item.key }}) was
         manufactured by {{ item.value.device_type.manufacturer.name }}"
    loop: "{{ query('netbox', 'devices',
                    api_endpoint='http://localhost/',
                    token='<redacted>') }}"
"""

RETURN = """
  _list:
    description:
      - list of composed dictonaries with key and value
    type: list
"""


def get_endpoint(netbox, term):
    """
    get_endpoint(netbox, term)
        netbox: a predefined pynetbox.api() pointing to a valid instance
                of Netbox
        term: the term passed to the lookup function upon which the api
              call will be identified
    """

    netbox_endpoint_map = {
        'aggregates': {
            'endpoint': netbox.ipam.aggregates},
        'circuit-terminations': {
            'endpoint': netbox.circuits.circuit_terminations},
        'circuit-types': {
            'endpoint': netbox.circuits.circuit_types},
        'circuits': {
            'endpoint': netbox.circuits.circuits},
        'circuit-providers': {
            'endpoint': netbox.circuits.providers},
        'cables': {
            'endpoint': netbox.dcim.cables},
        'cluster-groups': {
            'endpoint': netbox.virtualization.cluster_groups},
        'cluster-types': {
            'endpoint': netbox.virtualization.cluster_types},
        'clusters': {
            'endpoint': netbox.virtualization.clusters},
        'config-contexts': {
            'endpoint': netbox.extras.config_contexts},
        'console-connections': {
            'endpoint': netbox.dcim.console_connections},
        'console-ports': {
            'endpoint': netbox.dcim.console_ports},
        'console-server-port-templates': {
            'endpoint': netbox.dcim.console_server_port_templates},
        'console-server-ports': {
            'endpoint': netbox.dcim.console_server_ports},
        'device-bay-templates': {
            'endpoint': netbox.dcim.device_bay_templates},
        'device-bays': {
            'endpoint': netbox.dcim.device_bays},
        'device-roles': {
            'endpoint': netbox.dcim.device_roles},
        'device-types': {
            'endpoint': netbox.dcim.device_types},
        'devices': {
            'endpoint': netbox.dcim.devices},
        'export-templates': {
            'endpoint': netbox.dcim.export_templates},
        'front-port-templates': {
            'endpoint': netbox.dcim.front_port_templates},
        'front-ports': {
            'endpoint': netbox.dcim.front_ports},
        'graphs': {
            'endpoint': netbox.extras.graphs},
        'image-attachments': {
            'endpoint': netbox.extras.image_attachments},
        'interface-connections': {
            'endpoint': netbox.dcim.interface_connections},
        'interface-templates': {
            'endpoint': netbox.dcim.interface_templates},
        'interfaces': {
            'endpoint': netbox.dcim.interfaces},
        'inventory-items': {
            'endpoint': netbox.dcim.inventory_items},
        'ip-addresses': {
            'endpoint': netbox.ipam.ip_addresses},
        'manufacturers': {
            'endpoint': netbox.dcim.manufacturers},
        'object-changes': {
            'endpoint': netbox.extras.object_changes},
        'platforms': {
            'endpoint': netbox.dcim.platforms},
        'power-connections': {
            'endpoint': netbox.dcim.power_connections},
        'power-outlet-templates': {
            'endpoint': netbox.dcim.power_outlet_templates},
        'power-outlets': {
            'endpoint': netbox.dcim.power_outlets},
        'power-port-templates': {
            'endpoint': netbox.dcim.power_port_templates},
        'power-ports': {
            'endpoint': netbox.dcim.power_ports},
        'prefixes': {
            'endpoint': netbox.ipam.prefixes},
        'rack-groups': {
            'endpoint': netbox.dcim.rack_groups},
        'rack-reservations': {
            'endpoint': netbox.dcim.rack_reservations},
        'rack-roles': {
            'endpoint': netbox.dcim.rack_roles},
        'racks': {
            'endpoint': netbox.dcim.racks},
        'rear-port-templates': {
            'endpoint': netbox.dcim.rear_port_templates},
        'rear-ports': {
            'endpoint': netbox.dcim.rear_ports},
        'regions': {
            'endpoint': netbox.dcim.regions},
        'reports': {
            'endpoint': netbox.extras.reports},
        'rirs': {
            'endpoint': netbox.ipam.rirs},
        'roles': {
            'endpoint': netbox.ipam.roles},
        'secret-roles': {
            'endpoint': netbox.secrets.secret_roles},

        # Note: Currently unable to decrypt secrets as key wizardry needs to
        # take place first but term will return unencrypted elements of secrets
        # i.e. that they exist etc.
        'secrets': {
            'endpoint': netbox.secrets.secrets},

        'services': {
            'endpoint': netbox.ipam.services},
        'sites': {
            'endpoint': netbox.dcim.sites},
        'tags': {
            'endpoint': netbox.extras.tags},
        'tenant-groups': {
            'endpoint': netbox.tenancy.tenant_groups},
        'tenants': {
            'endpoint': netbox.tenancy.tenants},
        'topology-maps': {
            'endpoint': netbox.extras.topology_maps},
        'virtual-chassis': {
            'endpoint': netbox.dcim.virtual_chassis},
        'virtual-machines': {
            'endpoint': netbox.dcim.virtual_machines},
        'virtualization-interfaces': {
            'endpoint': netbox.virtualization.interfaces},
        'vlan-groups': {
            'endpoint': netbox.ipam.vlan_groups},
        'vlans': {
            'endpoint': netbox.ipam.vlans},
        'vrfs': {
            'endpoint': netbox.ipam.vrfs},
    }

    return netbox_endpoint_map[term]['endpoint']


class LookupModule(LookupBase):
    """
    LookupModule(LookupBase) is defined by Ansible
    """

    def run(self, terms, variables=None, **kwargs):

        netbox_api_token = kwargs.get('token')
        netbox_api_endpoint = kwargs.get('api_endpoint')
        netbox_private_key_file = kwargs.get('key_file')

        if not isinstance(terms, list):
            terms = [terms]

        netbox = pynetbox.api(netbox_api_endpoint, token=netbox_api_token,
                              private_key_file=netbox_private_key_file)

        results = []
        for term in terms:

            try:
                endpoint = get_endpoint(netbox, term)
            except KeyError:
                raise AnsibleError(
                    "Unrecognised term %s. Check documentation" % term)

            Display().vvvv(u"Netbox lookup for %s to %s using token %s" %
                           (term, netbox_api_endpoint, netbox_api_token))
            for res in endpoint.all():

                Display().vvvvv(pformat(dict(res)))

                key = dict(res)["id"]
                result = {key: dict(res)}

                results.extend(self._flatten_hash_to_list(result))

        return results
