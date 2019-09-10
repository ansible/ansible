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
module: hcloud_server_network

short_description: Manage the relationship between Hetzner Cloud Networks and servers

version_added: "2.9"

description:
    - Create and delete the relationship Hetzner Cloud Networks and servers

author:
    - Lukas Kaemmerling (@lkaemmerling)

options:
    network:
        description:
            - The name of the Hetzner Cloud Networks.

        type: str
        required: true
    server:
        description:
            - The name of the Hetzner Cloud server.
        type: str
        required: true
    ip:
        description:
            - The IP the server should have.
        type: str
    alias_ips:
        description:
            - Alias IPs the server has.
        type: list
    state:
        description:
            - State of the server_network.
        default: present
        choices: [ absent, present ]
        type: str

requirements:
  - hcloud-python >= 1.3.0

extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Create a basic server network
  hcloud_server_network:
    network: my-network
    server: my-server
    state: present

- name: Create a server network and specify the ip address
  hcloud_server_network:
    network: my-network
    server: my-server
    ip: 10.0.0.1
    state: present

- name: Create a server network and add alias ips
  hcloud_server_network:
    network: my-network
    server: my-server
    ip: 10.0.0.1
    alias_ips:
       - 10.1.0.1
       - 10.2.0.1
    state: present

- name: Ensure the server network is absent (remove if needed)
  hcloud_server_network:
    network: my-network
    server: my-server
    state: absent
"""

RETURN = """
hcloud_server_network:
    description: The relationship between a server and a network
    returned: always
    type: complex
    contains:
        network:
            description: Name of the Network
            type: str
            returned: always
            sample: my-network
        server:
            description: Name of the server
            type: str
            returned: always
            sample: my-server
        ip:
            description: IP of the server within the Network ip range
            type: str
            returned: always
            sample: 10.0.0.8
        alias_ips:
            description: Alias IPs of the server within the Network ip range
            type: str
            returned: always
            sample: [10.1.0.1, ...]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.hcloud import Hcloud

try:
    from hcloud import APIException
except ImportError:
    APIException = None
    NetworkSubnet = None


class AnsibleHcloudServerNetwork(Hcloud):
    def __init__(self, module):
        super(AnsibleHcloudServerNetwork, self).__init__(module, "hcloud_server_network")
        self.hcloud_network = None
        self.hcloud_server = None
        self.hcloud_server_network = None

    def _prepare_result(self):
        return {
            "network": to_native(self.hcloud_network.name),
            "server": to_native(self.hcloud_server.name),
            "ip": to_native(self.hcloud_server_network.ip),
            "alias_ips": self.hcloud_server_network.alias_ips,
        }

    def _get_server_and_network(self):
        try:
            self.hcloud_network = self.client.networks.get_by_name(self.module.params.get("network"))
            self.hcloud_server = self.client.servers.get_by_name(self.module.params.get("server"))
            self.hcloud_server_network = None
        except APIException as e:
            self.module.fail_json(msg=e.message)

    def _get_server_network(self):
        for privateNet in self.hcloud_server.private_net:
            if privateNet.network.id == self.hcloud_network.id:
                self.hcloud_server_network = privateNet

    def _create_server_network(self):
        params = {
            "network": self.hcloud_network
        }

        if self.module.params.get("ip") is not None:
            params["ip"] = self.module.params.get("ip")
        if self.module.params.get("alias_ips") is not None:
            params["alias_ips"] = self.module.params.get("alias_ips")

        if not self.module.check_mode:
            try:
                self.hcloud_server.attach_to_network(**params).wait_until_finished()
            except APIException as e:
                self.module.fail_json(msg=e.message)

        self._mark_as_changed()
        self._get_server_and_network()
        self._get_server_network()

    def present_server_network(self):
        self._get_server_and_network()
        self._get_server_network()
        if self.hcloud_server_network is None:
            self._create_server_network()

    def delete_server_network(self):
        self._get_server_and_network()
        self._get_server_network()
        if self.hcloud_server_network is not None and self.hcloud_server is not None:
            if not self.module.check_mode:
                self.hcloud_server.detach_from_network(self.hcloud_server_network.network).wait_until_finished()
            self._mark_as_changed()
        self.hcloud_server_network = None

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                network={"type": "str", "required": True},
                server={"type": "str", "required": True},
                ip={"type": "str"},
                alias_ips={"type": "list"},
                state={
                    "choices": ["absent", "present"],
                    "default": "present",
                },
                **Hcloud.base_module_arguments()
            ),
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudServerNetwork.define_module()

    hcloud = AnsibleHcloudServerNetwork(module)
    state = module.params["state"]
    if state == "absent":
        hcloud.delete_server_network()
    elif state == "present":
        hcloud.present_server_network()

    module.exit_json(**hcloud.get_result())


if __name__ == "__main__":
    main()
