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
module: hcloud_network

short_description: Create and manage cloud Networks on the Hetzner Cloud.

version_added: "2.9"

description:
    - Create, update and manage cloud Networks on the Hetzner Cloud.
    - You need at least hcloud-python 1.3.0.

author:
    - Lukas Kaemmerling (@lkaemmerling)

options:
    id:
        description:
            - The ID of the Hetzner Cloud Networks to manage.
            - Only required if no Network I(name) is given.
        type: int
    name:
        description:
            - The Name of the Hetzner Cloud Network to manage.
            - Only required if no Network I(id) is given or a Network does not exists.
        type: str
    ip_range:
        description:
            - IP range of the Network.
            - Required if Network does not exists.
        type: str
    labels:
        description:
            - User-defined labels (key-value pairs).
        type: dict
    state:
        description:
            - State of the Network.
        default: present
        choices: [ absent, present ]
        type: str

requirements:
  - hcloud-python >= 1.3.0

extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Create a basic network
  hcloud_network:
    name: my-network
    ip_range: 10.0.0.0/8
    state: present

- name: Ensure the Network is absent (remove if needed)
  hcloud_network:
    name: my-network
    state: absent
"""

RETURN = """
hcloud_network:
    description: The Network
    returned: always
    type: complex
    contains:
        id:
            description: ID of the Network
            type: int
            returned: always
            sample: 12345
        name:
            description: Name of the Network
            type: str
            returned: always
            sample: my-volume
        ip_range:
            description: IP range of the Network
            type: str
            returned: always
            sample: 10.0.0.0/8
        labels:
            description: User-defined labels (key-value pairs)
            type: dict
            returned: always
            sample:
                key: value
                mylabel: 123
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.hcloud import Hcloud

try:
    from hcloud import APIException
except ImportError:
    APIException = None


class AnsibleHcloudNetwork(Hcloud):
    def __init__(self, module):
        super(AnsibleHcloudNetwork, self).__init__(module, "hcloud_network")
        self.hcloud_network = None

    def _prepare_result(self):
        return {
            "id": to_native(self.hcloud_network.id),
            "name": to_native(self.hcloud_network.name),
            "ip_range": to_native(self.hcloud_network.ip_range),
            "labels": self.hcloud_network.labels,
        }

    def _get_network(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_network = self.client.networks.get_by_id(
                    self.module.params.get("id")
                )
            else:
                self.hcloud_network = self.client.networks.get_by_name(
                    self.module.params.get("name")
                )
        except APIException as e:
            self.module.fail_json(msg=e.message)

    def _create_network(self):

        self.module.fail_on_missing_params(
            required_params=["name", "ip_range"]
        )
        params = {
            "name": self.module.params.get("name"),
            "ip_range": self.module.params.get("ip_range"),
            "labels": self.module.params.get("labels"),
        }

        if not self.module.check_mode:
            self.client.networks.create(**params)

        self._mark_as_changed()
        self._get_network()

    def _update_network(self):

        labels = self.module.params.get("labels")
        if labels is not None and labels != self.hcloud_network.labels:
            if not self.module.check_mode:
                self.hcloud_network.update(labels=labels)
            self._mark_as_changed()

        ip_range = self.module.params.get("ip_range")
        if ip_range is not None and ip_range != self.hcloud_network.ip_range:
            if not self.module.check_mode:
                self.hcloud_network.change_ip_range(ip_range=ip_range).wait_until_finished()
            self._mark_as_changed()

        self._get_network()

    def present_network(self):
        self._get_network()
        if self.hcloud_network is None:
            self._create_network()
        else:
            self._update_network()

    def delete_network(self):
        self._get_network()
        if self.hcloud_network is not None:
            if not self.module.check_mode:
                self.client.networks.delete(self.hcloud_network)
            self._mark_as_changed()
        self.hcloud_network = None

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                name={"type": "str"},
                ip_range={"type": "str"},
                labels={"type": "dict"},
                state={
                    "choices": ["absent", "present"],
                    "default": "present",
                },
                **Hcloud.base_module_arguments()
            ),
            required_one_of=[['id', 'name']],
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudNetwork.define_module()

    hcloud = AnsibleHcloudNetwork(module)
    state = module.params["state"]
    if state == "absent":
        hcloud.delete_network()
    elif state == "present":
        hcloud.present_network()

    module.exit_json(**hcloud.get_result())


if __name__ == "__main__":
    main()
