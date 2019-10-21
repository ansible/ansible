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
module: hcloud_ssh_key

short_description: Create and manage ssh keys on the Hetzner Cloud.

version_added: "2.8"

description:
    - Create, update and manage ssh keys on the Hetzner Cloud.

author:
    - Lukas Kaemmerling (@LKaemmerling)

options:
    id:
        description:
            - The ID of the Hetzner Cloud ssh_key to manage.
            - Only required if no ssh_key I(name) is given
        type: int
    name:
        description:
            - The Name of the Hetzner Cloud ssh_key to manage.
            - Only required if no ssh_key I(id) is given or a ssh_key does not exists.
        type: str
    fingerprint:
        description:
            - The Fingerprint of the Hetzner Cloud ssh_key to manage.
            - Only required if no ssh_key I(id) or I(name) is given.
        type: str
    labels:
        description:
            - User-defined labels (key-value pairs)
        type: dict
    public_key:
        description:
            - The Public Key to add.
            - Required if ssh_key does not exists.
        type: str
    state:
        description:
            - State of the ssh_key.
        default: present
        choices: [ absent, present ]
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Create a basic ssh_key
  hcloud_ssh_key:
    name: my-ssh_key
    public_key: "ssh-rsa AAAjjk76kgf...Xt"
    state: present

- name: Create a ssh_key with labels
  hcloud_ssh_key:
    name: my-ssh_key
    public_key: "ssh-rsa AAAjjk76kgf...Xt"
    labels:
        key: value
        mylabel: 123
    state: present

- name: Ensure the ssh_key is absent (remove if needed)
  hcloud_ssh_key:
    name: my-ssh_key
    state: absent
"""

RETURN = """
hcloud_ssh_key:
    description: The ssh_key instance
    returned: Always
    type: complex
    contains:
        id:
            description: ID of the ssh_key
            type: int
            returned: Always
            sample: 12345
        name:
            description: Name of the ssh_key
            type: str
            returned: Always
            sample: my-ssh-key
        fingerprint:
            description: Fingerprint of the ssh_key
            type: str
            returned: Always
            sample: b7:2f:30:a0:2f:6c:58:6c:21:04:58:61:ba:06:3b:2f
        public_key:
            description: Public key of the ssh_key
            type: str
            returned: Always
            sample: "ssh-rsa AAAjjk76kgf...Xt"
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
    from hcloud.volumes.domain import Volume
    from hcloud.ssh_keys.domain import SSHKey
    from hcloud.ssh_keys.domain import Server
    from hcloud import APIException
except ImportError:
    pass


class AnsibleHcloudSSHKey(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_ssh_key")
        self.hcloud_ssh_key = None

    def _prepare_result(self):
        return {
            "id": to_native(self.hcloud_ssh_key.id),
            "name": to_native(self.hcloud_ssh_key.name),
            "fingerprint": to_native(self.hcloud_ssh_key.fingerprint),
            "public_key": to_native(self.hcloud_ssh_key.public_key),
            "labels": self.hcloud_ssh_key.labels,
        }

    def _get_ssh_key(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_ssh_key = self.client.ssh_keys.get_by_id(
                    self.module.params.get("id")
                )
            elif self.module.params.get("fingerprint") is not None:
                self.hcloud_ssh_key = self.client.ssh_keys.get_by_fingerprint(
                    self.module.params.get("fingerprint")
                )
            elif self.module.params.get("name") is not None:
                self.hcloud_ssh_key = self.client.ssh_keys.get_by_name(
                    self.module.params.get("name")
                )

        except APIException as e:
            self.module.fail_json(msg=e.message)

    def _create_ssh_key(self):
        self.module.fail_on_missing_params(
            required_params=["name", "public_key"]
        )
        params = {
            "name": self.module.params.get("name"),
            "public_key": self.module.params.get("public_key"),
            "labels": self.module.params.get("labels")
        }

        if not self.module.check_mode:
            self.client.ssh_keys.create(**params)
        self._mark_as_changed()
        self._get_ssh_key()

    def _update_ssh_key(self):
        name = self.module.params.get("name")
        if name is not None and self.hcloud_ssh_key.name != name:
            self.module.fail_on_missing_params(
                required_params=["id"]
            )
            if not self.module.check_mode:
                self.hcloud_ssh_key.update(name=name)
            self._mark_as_changed()

        labels = self.module.params.get("labels")
        if labels is not None and self.hcloud_ssh_key.labels != labels:
            if not self.module.check_mode:
                self.hcloud_ssh_key.update(labels=labels)
            self._mark_as_changed()

        self._get_ssh_key()

    def present_ssh_key(self):
        self._get_ssh_key()
        if self.hcloud_ssh_key is None:
            self._create_ssh_key()
        else:
            self._update_ssh_key()

    def delete_ssh_key(self):
        self._get_ssh_key()
        if self.hcloud_ssh_key is not None:
            if not self.module.check_mode:
                self.client.ssh_keys.delete(self.hcloud_ssh_key)
            self._mark_as_changed()
        self.hcloud_ssh_key = None

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                name={"type": "str"},
                public_key={"type": "str"},
                fingerprint={"type": "str"},
                labels={"type": "dict"},
                state={
                    "choices": ["absent", "present"],
                    "default": "present",
                },
                **Hcloud.base_module_arguments()
            ),
            required_one_of=[['id', 'name', 'fingerprint']],
            required_if=[['state', 'present', ['name']]],
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudSSHKey.define_module()

    hcloud = AnsibleHcloudSSHKey(module)
    state = module.params.get("state")
    if state == "absent":
        hcloud.delete_ssh_key()
    elif state == "present":
        hcloud.present_ssh_key()

    module.exit_json(**hcloud.get_result())


if __name__ == "__main__":
    main()
