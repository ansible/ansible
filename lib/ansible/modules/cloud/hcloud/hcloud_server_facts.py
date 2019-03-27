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
module: hcloud_server_facts

short_description: Gather facts about your Hetzner Cloud servers.

version_added: "2.8"

description:
    - Gather facts about your Hetzner Cloud servers.

author:
    - Lukas Kaemmerling (@lkaemmerling)

options:
    id:
        description:
            - The ID of the server you want to get.
        type: int
    name:
        description:
            - The name of the server you want to get.
        type: str
    label_selector:
        description:
            - The label selector for the servery you want to get.
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Gather hcloud server facts
  local_action:
    module: hcloud_server_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.hcloud_server_facts
"""

RETURN = """
hcloud_server_facts:
    description: The server facts as list
    returned: always
    type: complex
    contains:
        id:
            description: Numeric identifier of the server
            returned: always
            type: int
            sample: 1937415
        name:
            description: Name of the server
            returned: always
            type: str
            sample: my-server
        status:
            description: Status of the server
            returned: always
            type: str
            sample: running
        server_type:
            description: Name of the server type of the server
            returned: always
            type: str
            sample: cx11
        ipv4_address:
            description: Public IPv4 address of the server
            returned: always
            type: str
            sample: 116.203.104.109
        ipv6:
            description: IPv6 network of the server
            returned: always
            type: str
            sample: 2a01:4f8:1c1c:c140::/64
        location:
            description: Name of the location of the server
            returned: always
            type: str
            sample: fsn1
        datacenter:
            description: Name of the datacenter of the server
            returned: always
            type: str
            sample: fsn1-dc14
        rescue_enabled:
            description: True if rescue mode is enabled, Server will then boot into rescue system on next reboot
            returned: always
            type: bool
            sample: false
        backup_window:
            description: Time window (UTC) in which the backup will run, or null if the backups are not enabled
            returned: always
            type: bool
            sample: 22-02
        labels:
            description: User-defined labels (key-value pairs)
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


class AnsibleHcloudServerFacts(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_server_facts")
        self.hcloud_server_facts = None

    def _prepare_result(self):
        tmp = []

        for server in self.hcloud_server_facts:
            if server is not None:
                tmp.append({
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
                })
        return tmp

    def get_servers(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_server_facts = [self.client.servers.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("name") is not None:
                self.hcloud_server_facts = [self.client.servers.get_by_name(
                    self.module.params.get("name")
                )]
            elif self.module.params.get("label_selector") is not None:
                self.hcloud_server_facts = self.client.servers.get_all(
                    label_selector=self.module.params.get("label_selector"))
            else:
                self.hcloud_server_facts = self.client.servers.get_all()

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
    module = AnsibleHcloudServerFacts.define_module()

    hcloud = AnsibleHcloudServerFacts(module)
    hcloud.get_servers()
    result = hcloud.get_result()
    ansible_facts = {
        'hcloud_server_facts': result['hcloud_server_facts']
    }
    module.exit_json(ansible_facts=ansible_facts)


if __name__ == "__main__":
    main()
