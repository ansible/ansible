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
module: hcloud_server

short_description: Create and manage cloud servers on the Hetzner Cloud.

version_added: "2.8"

description:
    - Create, update and manage cloud servers on the Hetzner Cloud.

author:
    - Lukas Kaemmerling (@lkaemmerling)

options:
    id:
        description:
            - The ID of the Hetzner Cloud server to manage.
            - Only required if no server I(name) is given
        type: int
    name:
        description:
            - The Name of the Hetzner Cloud server to manage.
            - Only required if no server I(id) is given or a server does not exists.
        type: str
    server_type:
        description:
            - The Server Type of the Hetzner Cloud server to manage.
            - Required if server does not exists.
        type: str
    ssh_keys:
        description:
            - List of SSH Keys Names
        type: list
    volumes:
        description:
            - List of Volumes IDs that should be attached to the server on server creation.
        type: list
    image:
        description:
            - Image the server should be created from.
            - Required if server does not exists.
        type: str
    location:
        description:
            - Location of Server.
            - Required if no I(datacenter) is given and server does not exists.
        type: str
    datacenter:
        description:
            - Datacenter of Server.
            - Required of no I(location) is given and server does not exists.
        type: str
    backups:
        description:
            - Enable or disable Backups for the given Server.
        type: bool
        default: no
    upgrade_disk:
        description:
            - Resize the disk size, when resizing a server.
            - If you want to downgrade the server later, this value should be False.
        type: bool
        default: no
    force_upgrade:
        description:
            - Force the upgrade of the server.
            - Power off the server if it is running on upgrade.
        type: bool
        default: no
    user_data:
        description:
            - User Data to be passed to the server on creation.
            - Only used if server does not exists.
        type: str
    labels:
        description:
            - User-defined labels (key-value pairs).
        type: dict
    state:
        description:
            - State of the server.
        default: present
        choices: [ absent, present, restarted, started, stopped, rebuild ]
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Create a basic server
  hcloud_server:
    name: my-server
    server_type: cx11
    image: ubuntu-18.04
    state: present

- name: Create a basic server with ssh key
  hcloud_server:
    name: my-server
    server_type: cx11
    image: ubuntu-18.04
    location: fsn1
    ssh_keys:
      - my-ssh-key
    state: present

- name: Resize an existing server
  hcloud_server:
    name: my-server
    server_type: cx21
    keep_disk: yes
    state: present

- name: Ensure the server is absent (remove if needed)
  hcloud_server:
    name: my-server
    state: absent

- name: Ensure the server is started
  hcloud_server:
    name: my-server
    state: started

- name: Ensure the server is stopped
  hcloud_server:
    name: my-server
    state: stopped

- name: Ensure the server is restarted
  hcloud_server:
    name: my-server
    state: restarted

- name: Ensure the server is rebuild
  hcloud_server:
    name: my-server
    image: ubuntu-18.04
    state: rebuild
"""

RETURN = """
hcloud_server:
    description: The server instance
    returned: Always
    type: dict
    sample: {
        "backup_window": null,
        "datacenter": "nbg1-dc3",
        "id": 1937415,
        "image": "ubuntu-18.04",
        "ipv4_address": "116.203.104.109",
        "ipv6": "2a01:4f8:1c1c:c140::/64",
        "labels": {},
        "location": "nbg1",
        "name": "mein-server-2",
        "rescue_enabled": false,
        "server_type": "cx11",
        "status": "running"
    }
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.hcloud import Hcloud

try:
    from hcloud.volumes.domain import Volume
    from hcloud.ssh_keys.domain import SSHKey
    from hcloud.servers.domain import Server
    from hcloud import APIException
except ImportError:
    pass


class AnsibleHcloudServer(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_server")
        self.hcloud_server = None

    def _prepare_result(self):
        return {
            "id": to_native(self.hcloud_server.id),
            "name": to_native(self.hcloud_server.name),
            "ipv4_address": to_native(self.hcloud_server.public_net.ipv4.ip),
            "ipv6": to_native(self.hcloud_server.public_net.ipv6.ip),
            "image": to_native(self.hcloud_server.image.name),
            "server_type": to_native(self.hcloud_server.server_type.name),
            "datacenter": to_native(self.hcloud_server.datacenter.name),
            "location": to_native(self.hcloud_server.datacenter.location.name),
            "rescue_enabled": self.hcloud_server.rescue_enabled,
            "backup_window": to_native(self.hcloud_server.backup_window),
            "labels": self.hcloud_server.labels,
            "status": to_native(self.hcloud_server.status),
        }

    def _get_server(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_server = self.client.servers.get_by_id(
                    self.module.params.get("id")
                )
            else:
                self.hcloud_server = self.client.servers.get_by_name(
                    self.module.params.get("name")
                )
        except APIException as e:
            self.module.fail_json(msg=e.message)

    def _create_server(self):

        self.module.fail_on_missing_params(
            required_params=["name", "server_type", "image"]
        )
        params = {
            "name": self.module.params.get("name"),
            "server_type": self.client.server_types.get_by_name(
                self.module.params.get("server_type")
            ),
            "image": self.client.images.get_by_name(self.module.params.get("image")),
            "user_data": self.module.params.get("user_data"),
            "labels": self.module.params.get("labels"),
        }

        if self.module.params.get("ssh_keys") is not None:
            params["ssh_keys"] = [
                SSHKey(name=ssh_key_name)
                for ssh_key_name in self.module.params.get("ssh_keys")
            ]

        if self.module.params.get("volumes") is not None:
            params["volumes"] = [
                Volume(id=volume_id) for volume_id in self.module.params.get("volumes")
            ]

        if self.module.params.get("location") is None and self.module.params.get("datacenter") is None:
            # When not given, the API will choose the location.
            params["location"] = None
            params["datacenter"] = None
        elif self.module.params.get("location") is not None and self.module.params.get("datacenter") is None:
            params["location"] = self.client.locations.get_by_name(
                self.module.params.get("location")
            )
        elif self.module.params.get("location") is None and self.module.params.get("datacenter") is not None:
            params["datacenter"] = self.client.datacenters.get_by_name(
                self.module.params.get("datacenter")
            )

        if not self.module.check_mode:
            resp = self.client.servers.create(**params)
            self.result["root_password"] = resp.root_password
            resp.action.wait_until_finished()
            [action.wait_until_finished() for action in resp.next_actions]
        self._mark_as_changed()
        self._get_server()

    def _update_server(self):
        if self.module.params.get("backups") and self.hcloud_server.backup_window is None:
            if not self.module.check_mode:
                self.hcloud_server.enable_backup().wait_until_finished()
            self._mark_as_changed()
        elif not self.module.params.get("backups") and self.hcloud_server.backup_window is not None:
            if not self.module.check_mode:
                self.hcloud_server.disable_backup().wait_until_finished()
            self._mark_as_changed()

        labels = self.module.params.get("labels")
        if labels is not None and labels != self.hcloud_server.labels:
            if not self.module.check_mode:
                self.hcloud_server.update(labels=labels)
            self._mark_as_changed()

        server_type = self.module.params.get("server_type")
        if server_type is not None and self.hcloud_server.server_type.name != server_type:
            previous_server_status = self.hcloud_server.status
            state = self.module.params.get("state")
            if previous_server_status == Server.STATUS_RUNNING:
                if not self.module.check_mode:
                    if self.module.params.get("force_upgrade") or state == "stopped":
                        self.stop_server()  # Only stopped server can be upgraded
                    else:
                        self.module.warn(
                            "You can not upgrade a running instance %s. You need to stop the instance or use force_upgrade=yes."
                            % self.hcloud_server.name
                        )
            timeout = 100
            if self.module.params.get("upgrade_disk"):
                timeout = (
                    1000
                )  # When we upgrade the disk too the resize progress takes some more time.
            if not self.module.check_mode:
                self.hcloud_server.change_type(
                    server_type=self.client.server_types.get_by_name(server_type),
                    upgrade_disk=self.module.params.get("upgrade_disk"),
                ).wait_until_finished(timeout)
                if state == "present" and previous_server_status == Server.STATUS_RUNNING or state == "started":
                    self.start_server()

            self._mark_as_changed()
        self._get_server()

    def start_server(self):
        if self.hcloud_server.status != Server.STATUS_RUNNING:
            if not self.module.check_mode:
                self.client.servers.power_on(self.hcloud_server).wait_until_finished()
            self._mark_as_changed()
        self._get_server()

    def stop_server(self):
        if self.hcloud_server.status != Server.STATUS_OFF:
            if not self.module.check_mode:
                self.client.servers.power_off(self.hcloud_server).wait_until_finished()
            self._mark_as_changed()
        self._get_server()

    def rebuild_server(self):
        self.module.fail_on_missing_params(
            required_params=["image"]
        )
        if not self.module.check_mode:
            self.client.servers.rebuild(self.hcloud_server, self.client.images.get_by_name(self.module.params.get("image"))).wait_until_finished()
        self._mark_as_changed()

        self._get_server()

    def present_server(self):
        self._get_server()
        if self.hcloud_server is None:
            self._create_server()
        else:
            self._update_server()

    def delete_server(self):
        self._get_server()
        if self.hcloud_server is not None:
            if not self.module.check_mode:
                self.client.servers.delete(self.hcloud_server).wait_until_finished()
            self._mark_as_changed()
        self.hcloud_server = None

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                name={"type": "str"},
                image={"type": "str"},
                server_type={"type": "str"},
                location={"type": "str"},
                datacenter={"type": "str"},
                user_data={"type": "str"},
                ssh_keys={"type": "list"},
                volumes={"type": "list"},
                labels={"type": "dict"},
                backups={"type": "bool", "default": False},
                upgrade_disk={"type": "bool", "default": False},
                force_upgrade={"type": "bool", "default": False},
                state={
                    "choices": ["absent", "present", "restarted", "started", "stopped", "rebuild"],
                    "default": "present",
                },
                **Hcloud.base_module_arguments()
            ),
            required_one_of=[['id', 'name']],
            mutually_exclusive=[["location", "datacenter"]],
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudServer.define_module()

    hcloud = AnsibleHcloudServer(module)
    state = module.params.get("state")
    if state == "absent":
        hcloud.delete_server()
    elif state == "present":
        hcloud.present_server()
    elif state == "started":
        hcloud.present_server()
        hcloud.start_server()
    elif state == "stopped":
        hcloud.present_server()
        hcloud.stop_server()
    elif state == "restarted":
        hcloud.present_server()
        hcloud.stop_server()
        hcloud.start_server()
    elif state == "rebuild":
        hcloud.present_server()
        hcloud.rebuild_server()

    module.exit_json(**hcloud.get_result())


if __name__ == "__main__":
    main()
