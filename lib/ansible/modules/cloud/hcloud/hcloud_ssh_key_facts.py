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
module: hcloud_ssh_key_facts
short_description: Gather facts about your Hetzner Cloud ssh_keys.
version_added: "2.8"
description:
    - Gather facts about your Hetzner Cloud ssh_keys.
author:
    - Christopher Schmitt (@cschmitt-hcloud)
options:
    id:
        description:
            - The ID of the ssh key you want to get.
        type: int
    name:
        description:
            - The name of the ssh key you want to get.
        type: str
    fingerprint:
        description:
            - The fingerprint of the ssh key you want to get.
        type: str
    label_selector:
        description:
            - The label selector for the ssh key you want to get.
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Gather hcloud sshkey facts
  local_action:
    module: hcloud_ssh_key_facts
- name: Print the gathered facts
  debug:
    var: ansible_facts.hcloud_ssh_key_facts
"""

RETURN = """
hcloud_ssh_key_facts:
    description: The ssh key instances
    returned: Always
    type: complex
    contains:
        id:
            description: Numeric identifier of the ssh_key
            returned: always
            type: int
            sample: 1937415
        name:
            description: Name of the ssh_key
            returned: always
            type: str
            sample: my-ssh-key
        fingerprint:
            description: Fingerprint of the ssh key
            returned: always
            type: str
            sample: 0e:e0:bd:c7:2d:1f:69:49:94:44:91:f1:19:fd:35:f3
        public_key:
            description: The acctual public key
            returned: always
            type: str
            sample: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGpl/tnk74nnQJxxLAtutUApUZMRJxryKh7VXkNbd4g9 john@example.com"
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


class AnsibleHcloudSSHKeyFacts(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_ssh_key_facts")
        self.hcloud_ssh_key_facts = None

    def _prepare_result(self):
        ssh_keys = []

        for ssh_key in self.hcloud_ssh_key_facts:
            if ssh_key:
                ssh_keys.append({
                    "id": to_native(ssh_key.id),
                    "name": to_native(ssh_key.name),
                    "fingerprint": to_native(ssh_key.fingerprint),
                    "public_key": to_native(ssh_key.public_key),
                    "labels": ssh_key.labels
                })
        return ssh_keys

    def get_ssh_keys(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_ssh_key_facts = [self.client.ssh_keys.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("name") is not None:
                self.hcloud_ssh_key_facts = [self.client.ssh_keys.get_by_name(
                    self.module.params.get("name")
                )]
            elif self.module.params.get("fingerprint") is not None:
                self.hcloud_ssh_key_facts = [self.client.ssh_keys.get_by_fingerprint(
                    self.module.params.get("fingerprint")
                )]
            elif self.module.params.get("label_selector") is not None:
                self.hcloud_ssh_key_facts = self.client.ssh_keys.get_all(
                    label_selector=self.module.params.get("label_selector"))
            else:
                self.hcloud_ssh_key_facts = self.client.ssh_keys.get_all()

        except APIException as e:
            self.module.fail_json(msg=e.message)

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                name={"type": "str"},
                fingerprint={"type": "str"},
                label_selector={"type": "str"},
                **Hcloud.base_module_arguments()
            ),
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudSSHKeyFacts.define_module()

    hcloud = AnsibleHcloudSSHKeyFacts(module)
    hcloud.get_ssh_keys()
    result = hcloud.get_result()
    ansible_facts = {
        'hcloud_ssh_key_facts': result['hcloud_ssh_key_facts']
    }
    module.exit_json(ansible_facts=ansible_facts)


if __name__ == "__main__":
    main()
