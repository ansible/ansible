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
module: hcloud_subnetwork

short_description: Manage cloud subnetworks on the Hetzner Cloud.

version_added: "2.9"

description:
    - Create, update and delete cloud subnetworks on the Hetzner Cloud.

author:
    - Lukas Kaemmerling (@lkaemmerling)

options:
    network:
        description:
            - The ID or Name  of the Hetzner Cloud Networks.

        type: str
        required: true
    ip_range:
        description:
            - IP range of the subnetwork.
        type: str
        required: true
    type:
        description:
            - Type of subnetwork.
        type: str
        required: true
    network_zone:
        description:
            - Name of network zone.
        type: str
        required: true
    state:
        description:
            - State of the subnetwork.
        default: present
        choices: [ absent, present ]
        type: str

requirements:
  - hcloud-python >= 1.3.0

extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Create a basic subnetwork
  hcloud_subnetwork:
    network: my-network
    ip_range: 10.0.0.0/16
    network_zone: eu-central
    type: server
    state: present

- name: Ensure the subnetwork is absent (remove if needed)
  hcloud_subnetwork:
    network: my-network
    ip_range: 10.0.0.0/8
    network_zone: eu-central
    type: server
    state: absent
"""

RETURN = """
hcloud_subnetwork:
    description: One Subnet of a Network
    returned: always
    type: complex
    contains:
        network:
            description: Name of the Network
            type: str
            returned: always
            sample: my-network
        ip_range:
            description: IP range of the Network
            type: str
            returned: always
            sample: 10.0.0.0/8
        type:
            description: Type of subnetwork
            type: str
            returned: always
            sample: server
        network_zone:
            description: Name of network zone
            type: str
            returned: always
            sample: eu-central
        gateway:
            description: Gateway of the subnetwork
            type: str
            returned: always
            sample: 10.0.0.1
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.hcloud import Hcloud

try:
    from hcloud import APIException
    from hcloud.networks.domain import NetworkSubnet
except ImportError:
    APIException = None
    NetworkSubnet = None


class AnsibleHcloudSubnetwork(Hcloud):
    def __init__(self, module):
        super(AnsibleHcloudSubnetwork, self).__init__(module, "hcloud_subnetwork")
        self.hcloud_network = None
        self.hcloud_subnetwork = None

    def _prepare_result(self):
        return {
            "network": to_native(self.hcloud_network.name),
            "ip_range": to_native(self.hcloud_subnetwork.ip_range),
            "type": to_native(self.hcloud_subnetwork.type),
            "network_zone": to_native(self.hcloud_subnetwork.network_zone),
            "gateway": self.hcloud_subnetwork.gateway,
        }

    def _get_network(self):
        try:
            self.hcloud_network = self.client.networks.get_by_name(self.module.params.get("network"))
            self.hcloud_subnetwork = None
        except APIException as e:
            self.module.fail_json(msg=e.message)

    def _get_subnetwork(self):
        subnet_ip_range = self.module.params.get("ip_range")
        for subnetwork in self.hcloud_network.subnets:
            if subnetwork.ip_range == subnet_ip_range:
                self.hcloud_subnetwork = subnetwork

    def _create_subnetwork(self):
        subnet = NetworkSubnet(
            ip_range=self.module.params.get("ip_range"),
            type=self.module.params.get('type'),
            network_zone=self.module.params.get('network_zone')
        )

        if not self.module.check_mode:
            try:
                self.hcloud_network.add_subnet(subnet=subnet).wait_until_finished()
            except APIException as e:
                self.module.fail_json(msg=e.message)

        self._mark_as_changed()
        self._get_network()
        self._get_subnetwork()

    def present_subnetwork(self):
        self._get_network()
        self._get_subnetwork()
        if self.hcloud_subnetwork is None:
            self._create_subnetwork()

    def delete_subnetwork(self):
        self._get_network()
        self._get_subnetwork()
        if self.hcloud_subnetwork is not None and self.hcloud_network is not None:
            if not self.module.check_mode:
                self.hcloud_network.delete_subnet(self.hcloud_subnetwork).wait_until_finished()
            self._mark_as_changed()
        self.hcloud_subnetwork = None

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                network={"type": "str", "required": True},
                network_zone={"type": "str", "required": True},
                type={"type": "str", "required": True},
                ip_range={"type": "str", "required": True},
                state={
                    "choices": ["absent", "present"],
                    "default": "present",
                },
                **Hcloud.base_module_arguments()
            ),
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudSubnetwork.define_module()

    hcloud = AnsibleHcloudSubnetwork(module)
    state = module.params["state"]
    if state == "absent":
        hcloud.delete_subnetwork()
    elif state == "present":
        hcloud.present_subnetwork()

    module.exit_json(**hcloud.get_result())


if __name__ == "__main__":
    main()
