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
module: hcloud_floating_ip

short_description: Create and manage Floating IPs on the Hetzner Cloud

version_added: "2.8"

description:
    - "Create, update and manage Floating IPss on the Hetzner Cloud."

author:
    - Lukas Kaemmerling (@lkaemmerling)

options:
    id:
        description:
            - The ID of the Hetzner Cloud Floating IP to manage.
        type: int
    description:
        description:
            - The Description of the Hetzner Cloud Floating IP to manage.
        type: str
    home_location:
        description:
            - Home Location of the Hetzner Cloud Floating IP.
            - Required if no I(server) is given and Floating IP does not exists.
        type: str
    server:
        description:
            - Server Name the Floating IP should be assigned to.
            - Required if no I(home_location) is given and Floating IP does not exists.
        type: str
    labels:
        description:
            - User-defined key-value pairs.
        type: dict
    type:
        description:
            - Type of the Floating IP.
            - Required if Floating IP does not exists
        choices: [ ipv4, ipv6 ]
        type: str
    force_assign:
        description:
            - Force the assignment of the Floating IP.
        type: bool
    state:
        description:
            - State of the Floating IP.
        default: present
        choices: [ absent, present ]
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Create a basic IPv4 Floating IP
  hcloud_floating_ip:
    description: my-floating-ip
    home_location: fsn1
    type: ipv4
    state: present

- name: Create a basic IPv6 Floating IP
  hcloud_floating_ip:
    description: my-floating-ip
    home_location: fsn1
    type: ipv6
    state: present

- name: Assign a Floating IP to a server
  hcloud_floating_ip:
    description: my-floating-ip
    server: 1234
    type: ipv4
    state: present

- name: Assign a Floating IP to another server
  hcloud_floating_ip:
    description: my-floating-ip
    server: 1234
    force_assign: yes
    type: ipv4
    state: present

- name: Floating IP should be absent
  hcloud_floating_ip:
    id: 1234
    state: absent
"""

RETURN = """
hcloud_floating_ip:
    description: The Floating IP instance
    returned: Always
    type: dict
    sample: {
        "id": 1937415,
        "description": "mein-server-2",
        "ip": "116.203.104.109",
        "type": "ipv4",
        "labels": {},
        "home_location": "fsn",
        "server": "my-server"
    }
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.hcloud import Hcloud

try:
    from hcloud.servers.domain import Server
    from hcloud.locations.domain import Location
    from hcloud import APIException
except ImportError:
    pass


class AnsibleHcloudFloatingIP(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_floating_ip")
        self.hcloud_floating_ip = None

    def _prepare_result(self):

        server = None

        if self.hcloud_floating_ip.server is not None:
            server = to_native(self.hcloud_floating_ip.server.name)
        return {
            "id": to_native(self.hcloud_floating_ip.id),
            "description": to_native(self.hcloud_floating_ip.description),
            "ip": to_native(self.hcloud_floating_ip.ip),
            "type": to_native(self.hcloud_floating_ip.type),
            "home_location": to_native(self.hcloud_floating_ip.home_location.name),
            "labels": self.hcloud_floating_ip.labels,
            "server": server,
        }

    def _get_floating_ip(self):
        try:
            if self.hcloud_floating_ip is None:
                self.hcloud_floating_ip = self.client.floating_ips.get_by_id(
                    self.module.params.get("id")
                )
            else:
                self.hcloud_floating_ip = self.client.floating_ips.get_by_id(
                    self.hcloud_floating_ip.id
                )
        except APIException:
            self.hcloud_floating_ip = None

    def _create_floating_ip(self):
        params = {
            "description": self.module.params.get("description"),
            "type": self.module.params.get("type"),
        }
        if self.module.params.get("home_location") is not None:
            params["home_location"] = self.client.locations.get_by_name(
                self.module.params.get("home_location")
            )
        if self.module.params.get("server") is not None:
            params["server"] = self.client.servers.get_by_name(
                self.module.params.get("server")
            )
        if self.module.params.get("labels") is not None:
            params["labels"] = self.module.params.get("labels")

        if not self.module.check_mode:
            resp = self.client.floating_ips.create(**params)
            self.hcloud_floating_ip = resp.floating_ip
            if resp.action is not None:
                resp.action.wait_until_finished()
        self._mark_as_changed()
        self._get_floating_ip()

    def _update_floating_ip(self):
        description = self.module.params.get("description")
        if description is not None and self.hcloud_floating_ip.description != description:
            if not self.module.check_mode:
                self.hcloud_floating_ip.update(description)
            self._mark_as_changed()

        labels = self.module.params.get("labels")
        if labels is not None and labels != self.hcloud_floating_ip.labels:
            if not self.module.check_mode:
                self.hcloud_floating_ip.update(labels=labels)
            self._mark_as_changed()

        server = self.module.params.get("server")
        if server is not None:
            if not self.module.check_mode:
                if self.module.params.get("force_assign") or self.hcloud_floating_ip.server is None:
                    self.hcloud_floating_ip.assign(
                        self.client.servers.get_by_name(self.module.params.get("server"))
                    )
                else:
                    self.module.warn(
                        "Floating IP is already assigned to server %s. You need to unassign the Floating IP or use force_assign=yes."
                        % self.hcloud_floating_ip.server.name
                    )
            self._mark_as_changed()
        elif server is None and self.hcloud_floating_ip.server is not None:
            if not self.module.check_mode:
                self.hcloud_floating_ip.unassign()
            self._mark_as_changed()

        self._get_floating_ip()

    def present_floating_ip(self):
        self._get_floating_ip()
        if self.hcloud_floating_ip is None:
            self._create_floating_ip()
        else:
            self.module.fail_on_missing_params(
                required_params=["id"]
            )
            self._update_floating_ip()

    def delete_floating_ip(self):
        self._get_floating_ip()
        if self.hcloud_floating_ip is not None:
            if not self.module.check_mode:
                self.client.floating_ips.delete(self.hcloud_floating_ip)
            self._mark_as_changed()
        self.hcloud_floating_ip = None

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                description={"type": "str"},
                server={"type": "str"},
                home_location={"type": "str"},
                force_assign={"type": "bool"},
                type={"choices": ["ipv4", "ipv6"], "required": True},
                labels={"type": "dict"},
                state={"choices": ["absent", "present"], "default": "present"},
                **Hcloud.base_module_arguments()
            ),
            required_one_of=[['home_location', 'server']],
            mutually_exclusive=[['home_location', 'server']],
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudFloatingIP.define_module()

    hcloud = AnsibleHcloudFloatingIP(module)
    state = module.params.get("state")
    if state == "absent":
        module.fail_on_missing_params(
            required_params=["id"]
        )
        hcloud.delete_floating_ip()
    else:
        hcloud.present_floating_ip()

    module.exit_json(**hcloud.get_result())


if __name__ == "__main__":
    main()
