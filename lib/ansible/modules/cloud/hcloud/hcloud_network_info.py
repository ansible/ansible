#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Hetzner Cloud GmbH <info@hetzner-cloud.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: hcloud_network_info

short_description: Gather info about your Hetzner Cloud networks.

version_added: "2.9"

description:
    - Gather info about your Hetzner Cloud networks.

author:
    - Christopher Schmitt (@cschmitt-hcloud)

options:
    id:
        description:
            - The ID of the network you want to get.
        type: int
    name:
        description:
            - The name of the network you want to get.
        type: str
    label_selector:
        description:
            - The label selector for the network you want to get.
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Gather hcloud network info
  local_action:
    module: hcloud_network_info

- name: Print the gathered info
  debug:
    var: hcloud_network_info
"""

RETURN = """
hcloud_network_info:
    description: The network info as list
    returned: always
    type: complex
    contains:
        id:
            description: Numeric identifier of the network
            returned: always
            type: int
            sample: 1937415
        name:
            description: Name of the network
            returned: always
            type: str
            sample: awsome-network
        ip_range:
            description: IP range of the network
            returned: always
            type: str
            sample: 10.0.0.0/16
        subnetworks:
            description: Subnetworks belonging to the network
            returned: always
            type: complex
        routes:
            description: Routes belonging to the network
            returned: always
            type: complex
        servers:
            description: Servers attached to the network
            returned: always
            type: complex
        labels:
            description: Labels of the network
            returned: always
            type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.hcloud import Hcloud

try:
    from hcloud import APIException
except ImportError:
    pass


class AnsibleHcloudNetworkInfo(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_network_info")
        self.hcloud_network_info = None

    def _prepare_result(self):
        tmp = []

        for network in self.hcloud_network_info:
            if network is not None:
                subnets = []
                for subnet in network.subnets:
                    prepared_subnet = {
                        "type": subnet.type,
                        "ip_range": subnet.ip_range,
                        "network_zone": subnet.network_zone,
                        "gateway": subnet.gateway,
                    }
                    subnets.append(prepared_subnet)
                routes = []
                for route in network.routes:
                    prepared_route = {
                        "destination": route.destination,
                        "gateway": route.gateway
                    }
                    routes.append(prepared_route)

                servers = []
                for server in network.servers:
                    prepared_server = {
                        "id": to_native(server.id),
                        "name": to_native(server.name),
                        "ipv4_address": to_native(server.public_net.ipv4.ip),
                        "ipv6": to_native(server.public_net.ipv6.ip),
                        "image": to_native(server.image.name),
                        "server_type": to_native(server.server_type.name),
                        "datacenter": to_native(server.datacenter.name),
                        "location": to_native(server.datacenter.location.name),
                        "rescue_enabled": server.rescue_enabled,
                        "backup_window": to_native(server.backup_window),
                        "labels": server.labels,
                        "status": to_native(server.status),
                    }
                    servers.append(prepared_server)

                tmp.append({
                    "id": to_native(network.id),
                    "name": to_native(network.name),
                    "ip_range": to_native(network.ip_range),
                    "subnetworks": subnets,
                    "routes": routes,
                    "servers": servers,
                    "labels": network.labels,
                })
        return tmp

    def get_networks(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_network_info = [self.client.networks.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("name") is not None:
                self.hcloud_network_info = [self.client.networks.get_by_name(
                    self.module.params.get("name")
                )]
            elif self.module.params.get("label_selector") is not None:
                self.hcloud_network_info = self.client.networks.get_all(
                    label_selector=self.module.params.get("label_selector"))
            else:
                self.hcloud_network_info = self.client.networks.get_all()

        except APIException as e:
            self.module.fail_json(msg=e.message)

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                name={"type": "str"},
                label_selector={"type": "str"},
                **Hcloud.base_module_arguments()
            ),
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudNetworkInfo.define_module()

    hcloud = AnsibleHcloudNetworkInfo(module)
    hcloud.get_networks()
    result = hcloud.get_result()
    info = {
        'hcloud_network_info': result['hcloud_network_info']
    }
    module.exit_json(**info)


if __name__ == "__main__":
    main()
