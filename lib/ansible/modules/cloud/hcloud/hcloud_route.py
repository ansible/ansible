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
module: hcloud_route

short_description: Create and delete cloud routes on the Hetzner Cloud.

version_added: "2.9"

description:
    - Create, update and delete cloud routes on the Hetzner Cloud.

author:
    - Lukas Kaemmerling (@lkaemmerling)

options:
    network:
        description:
            - The name of the Hetzner Cloud Network.
        type: str
        required: true
    destination:
        description:
            - Destination network or host of this route.
        type: str
        required: true
    gateway:
        description:
            - Gateway for the route.
        type: str
        required: true
    state:
        description:
            - State of the route.
        default: present
        choices: [ absent, present ]
        type: str

requirements:
  - hcloud-python >= 1.3.0

extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Create a basic route
  hcloud_route:
    network: my-network
    destination: 10.100.1.0/24
    gateway: 10.0.1.1
    state: present

- name: Ensure the route is absent
  hcloud_route:
    network: my-network
    destination: 10.100.1.0/24
    gateway: 10.0.1.1
    state: absent
"""

RETURN = """
hcloud_route:
    description: One Route of a Network
    returned: always
    type: complex
    contains:
        network:
            description: Name of the Network
            type: str
            returned: always
            sample: my-network
        destination:
            description: Destination network or host of this route
            type: str
            returned: always
            sample: 10.0.0.0/8
        gateway:
            description: Gateway of the route
            type: str
            returned: always
            sample: 10.0.0.1
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.hcloud import Hcloud

try:
    from hcloud import APIException
    from hcloud.networks.domain import NetworkRoute
except ImportError:
    APIException = None
    NetworkSubnet = None


class AnsibleHcloudRoute(Hcloud):
    def __init__(self, module):
        super(AnsibleHcloudRoute, self).__init__(module, "hcloud_route")
        self.hcloud_network = None
        self.hcloud_route = None

    def _prepare_result(self):
        return {
            "network": to_native(self.hcloud_network.name),
            "destination": to_native(self.hcloud_route.destination),
            "gateway": self.hcloud_route.gateway,
        }

    def _get_network(self):
        try:
            self.hcloud_network = self.client.networks.get_by_name(self.module.params.get("network"))
            self.hcloud_route = None
        except APIException as e:
            self.module.fail_json(msg=e.message)

    def _get_route(self):
        destination = self.module.params.get("destination")
        gateway = self.module.params.get("gateway")
        for route in self.hcloud_network.routes:
            if route.destination == destination and route.gateway == gateway:
                self.hcloud_route = route

    def _create_route(self):
        route = NetworkRoute(
            destination=self.module.params.get("destination"),
            gateway=self.module.params.get('gateway')
        )

        if not self.module.check_mode:
            try:
                self.hcloud_network.add_route(route=route).wait_until_finished()
            except APIException as e:
                self.module.fail_json(msg=e.message)

        self._mark_as_changed()
        self._get_network()
        self._get_route()

    def present_route(self):
        self._get_network()
        self._get_route()
        if self.hcloud_route is None:
            self._create_route()

    def delete_route(self):
        self._get_network()
        self._get_route()
        if self.hcloud_route is not None and self.hcloud_network is not None:
            if not self.module.check_mode:
                self.hcloud_network.delete_route(self.hcloud_route).wait_until_finished()
            self._mark_as_changed()
        self.hcloud_route = None

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                network={"type": "str", "required": True},
                destination={"type": "str", "required": True},
                gateway={"type": "str", "required": True},
                state={
                    "choices": ["absent", "present"],
                    "default": "present",
                },
                **Hcloud.base_module_arguments()
            ),
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudRoute.define_module()

    hcloud = AnsibleHcloudRoute(module)
    state = module.params["state"]
    if state == "absent":
        hcloud.delete_route()
    elif state == "present":
        hcloud.present_route()

    module.exit_json(**hcloud.get_result())


if __name__ == "__main__":
    main()
