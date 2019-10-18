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

short_description: Create and manage cloud Floating IPs on the Hetzner Cloud.

version_added: "2.10"

description:
    - Create, update and manage cloud Floating IPs on the Hetzner Cloud.

author:
    - Lukas Kaemmerling (@lkaemmerling)

options:
    id:
        description:
            - The ID of the Hetzner Cloud Floating IPs to manage.
            - Only required if no Floating IP I(name) is given.
        type: int
    name:
        description:
            - The Name of the Hetzner Cloud Floating IPs to manage.
            - Only required if no Floating IP I(id) is given or a Floating IP does not exists.
        type: str
    description:
        description:
            - The Description of the Hetzner Cloud Floating IPs.
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
    type:
        description:
            - Type of the Floating IP.
            - Required if Floating IP does not exists
        choices: [ ipv4, ipv6 ]
        type: str
    force:
        description:
            - Force the assignment or deletion of the Floating IP.
        type: bool
    delete_protection:
        description:
            - Protect the Floating IP for deletion.
        type: bool
        version_added: "2.10"
    labels:
        description:
            - User-defined labels (key-value pairs).
        type: dict
    state:
        description:
            - State of the Floating IP.
        default: present
        choices: [ absent, present ]
        type: str

requirements:
  - hcloud-python >= 1.6.0

extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Create a basic IPv4 Floating IP
  hcloud_floating_ip:
    name: my-floating-ip
    home_location: fsn1
    type: ipv4
    state: present
- name: Create a basic IPv6 Floating IP
  hcloud_floating_ip:
    name: my-floating-ip
    home_location: fsn1
    type: ipv6
    state: present
- name: Assign a Floating IP to a server
  hcloud_floating_ip:
    name: my-floating-ip
    server: 1234
    state: present
- name: Assign a Floating IP to another server
  hcloud_floating_ip:
    name: my-floating-ip
    server: 1234
    force: yes
    state: present
- name: Floating IP should be absent
  hcloud_floating_ip:
    name: my-floating-ip
    state: absent
"""

RETURN = """
hcloud_floating_ip:
    description: The Floating IP instance
    returned: Always
    type: complex
    contains:
        id:
            description: ID of the Floating IP
            type: int
            returned: Always
            sample: 12345
        name:
            description: Name of the Floating IP
            type: str
            returned: Always
            sample: my-floating-ip
        description:
            description: Description of the Floating IP
            type: str
            returned: Always
            sample: my-floating-ip
        ip:
            description: IP Address of the Floating IP
            type: str
            returned: Always
            sample: 116.203.104.109
        type:
            description: Type of the Floating IP
            type: str
            returned: Always
            sample: ipv4
        home_location:
            description: Name of the home location of the Floating IP
            type: str
            returned: Always
            sample: fsn1
        server:
            description: Name of the server the Floating IP is assigned to.
            type: str
            returned: Always
            sample: "my-server"
        delete_protection:
            description: True if Floating IP is protected for deletion
            type: bool
            returned: always
            sample: false
            version_added: "2.10"
        labels:
            description: User-defined labels (key-value pairs)
            type: dict
            returned: Always
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


class AnsibleHcloudFloatingIP(Hcloud):
    def __init__(self, module):
        super(AnsibleHcloudFloatingIP, self).__init__(module, "hcloud_floating_ip")
        self.hcloud_floating_ip = None

    def _prepare_result(self):
        server = None

        if self.hcloud_floating_ip.server is not None:
            server = to_native(self.hcloud_floating_ip.server.name)
        return {
            "id": to_native(self.hcloud_floating_ip.id),
            "name": to_native(self.hcloud_floating_ip.name),
            "description": to_native(self.hcloud_floating_ip.description),
            "ip": to_native(self.hcloud_floating_ip.ip),
            "type": to_native(self.hcloud_floating_ip.type),
            "home_location": to_native(self.hcloud_floating_ip.home_location.name),
            "labels": self.hcloud_floating_ip.labels,
            "server": server,
            "delete_protection": self.hcloud_floating_ip.protection["delete"],
        }

    def _get_floating_ip(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_floating_ip = self.client.floating_ips.get_by_id(
                    self.module.params.get("id")
                )
            else:
                self.hcloud_floating_ip = self.client.floating_ips.get_by_name(
                    self.module.params.get("name")
                )
        except APIException as e:
            self.module.fail_json(msg=e.message)

    def _create_floating_ip(self):
        self.module.fail_on_missing_params(
            required_params=["type"]
        )
        params = {
            "description": self.module.params.get("description"),
            "type": self.module.params.get("type"),
            "name": self.module.params.get("name"),
        }
        if self.module.params.get("home_location") is not None:
            params["home_location"] = self.client.locations.get_by_name(
                self.module.params.get("home_location")
            )
        elif self.module.params.get("server") is not None:
            params["server"] = self.client.servers.get_by_name(
                self.module.params.get("server")
            )
        else:
            self.module.fail_json(msg="one of the following is required: home_location, server")

        if self.module.params.get("labels") is not None:
            params["labels"] = self.module.params.get("labels")
        if not self.module.check_mode:
            resp = self.client.floating_ips.create(**params)
            self.hcloud_floating_ip = resp.floating_ip

        self._mark_as_changed()
        self._get_floating_ip()

    def _update_floating_ip(self):
        try:
            labels = self.module.params.get("labels")
            if labels is not None and labels != self.hcloud_floating_ip.labels:
                if not self.module.check_mode:
                    self.hcloud_floating_ip.update(labels=labels)
                self._mark_as_changed()

            description = self.module.params.get("description")
            if description is not None and description != self.hcloud_floating_ip.description:
                if not self.module.check_mode:
                    self.hcloud_floating_ip.update(description=description)
                self._mark_as_changed()

            server = self.module.params.get("server")
            if server is not None:
                if self.module.params.get("force") or self.hcloud_floating_ip.server is None:
                    if not self.module.check_mode:
                        self.hcloud_floating_ip.assign(
                            self.client.servers.get_by_name(self.module.params.get("server"))
                        )
                else:
                    self.module.warn(
                        "Floating IP is already assigned to server %s. You need to unassign the Floating IP or use force=yes."
                        % self.hcloud_floating_ip.server.name
                    )
                self._mark_as_changed()
            elif server is None and self.hcloud_floating_ip.server is not None:
                if not self.module.check_mode:
                    self.hcloud_floating_ip.unassign()
                self._mark_as_changed()

            delete_protection = self.module.params.get("delete_protection")
            if delete_protection is not None and delete_protection != self.hcloud_floating_ip.protection["delete"]:
                if not self.module.check_mode:
                    self.hcloud_floating_ip.change_protection(delete=delete_protection).wait_until_finished()
                self._mark_as_changed()

            self._get_floating_ip()
        except APIException as e:
            self.module.fail_json(msg=e.message)

    def present_floating_ip(self):
        self._get_floating_ip()
        if self.hcloud_floating_ip is None:
            self._create_floating_ip()
        else:
            self._update_floating_ip()

    def delete_floating_ip(self):
        try:
            self._get_floating_ip()
            if self.hcloud_floating_ip is not None:
                if self.module.params.get("force") or self.hcloud_floating_ip.server is None:
                    if not self.module.check_mode:
                        self.client.floating_ips.delete(self.hcloud_floating_ip)
                else:
                    self.module.warn(
                        "Floating IP is currently assigned to server %s. You need to unassign the Floating IP or use force=yes."
                        % self.hcloud_floating_ip.server.name
                    )
                self._mark_as_changed()
            self.hcloud_floating_ip = None
        except APIException as e:
            self.module.fail_json(msg=e.message)

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                name={"type": "str"},
                description={"type": "str"},
                server={"type": "str"},
                home_location={"type": "str"},
                force={"type": "bool"},
                type={"choices": ["ipv4", "ipv6"]},
                labels={"type": "dict"},
                delete_protection={"type": "bool"},
                state={
                    "choices": ["absent", "present"],
                    "default": "present",
                },
                **Hcloud.base_module_arguments()
            ),
            required_one_of=[['id', 'name']],
            mutually_exclusive=[['home_location', 'server']],
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudFloatingIP.define_module()

    hcloud = AnsibleHcloudFloatingIP(module)
    state = module.params["state"]
    if state == "absent":
        hcloud.delete_floating_ip()
    elif state == "present":
        hcloud.present_floating_ip()

    module.exit_json(**hcloud.get_result())


if __name__ == "__main__":
    main()
