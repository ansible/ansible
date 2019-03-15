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
module: hcloud_server_type_facts

short_description: Gather facts about the Hetzner Cloud server types.

version_added: "2.8"

description:
    - Gather facts about your Hetzner Cloud server types.

author:
    - Lukas Kaemmerling (@lkaemmerling)

options:
    id:
        description:
            - The ID of the server type you want to get.
        type: int
    name:
        description:
            - The name of the server type you want to get.
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Gather hcloud server type facts
  local_action:
    module: hcloud_server_type_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.hcloud_server_type_facts
"""

RETURN = """
ansible_facts:
    description: The server_type instances
    returned: Always
    type: complex
    contains:
        "hcloud_server_type_facts": [
             {
                "id": 1,
                "name": "cx11",
                "description": "CX11",
                "cores": 1,
                "memory": 1,
                "disk": 25,
                "storage_type": "local",
                "cpu_type": "shared"
            }
        ]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.hcloud import Hcloud

try:
    from hcloud.volumes.domain import Volume
    from hcloud.ssh_keys.domain import SSHKey
    from hcloud.server_types.domain import Server
    from hcloud import APIException
except ImportError:
    pass


class AnsibleHcloudLocationFacts(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_server_type_facts")
        self.hcloud_server_type_facts = None

    def _prepare_result(self):
        tmp = []

        for server_type in self.hcloud_server_type_facts:
            if server_type is not None:
                tmp.append({
                    "id": to_native(server_type.id),
                    "name": to_native(server_type.name),
                    "description": to_native(server_type.description),
                    "cores": server_type.cores,
                    "memory": server_type.memory,
                    "disk": server_type.disk,
                    "storage_type": to_native(server_type.storage_type),
                    "cpu_type": to_native(server_type.cpu_type)
                })
        return tmp

    def get_server_types(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_server_type_facts = [self.client.server_types.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("name") is not None:
                self.hcloud_server_type_facts = [self.client.server_types.get_by_name(
                    self.module.params.get("name")
                )]
            else:
                self.hcloud_server_type_facts = self.client.server_types.get_all()

        except APIException as e:
            self.module.fail_json(msg=e.message)

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                name={"type": "str"},
                **Hcloud.base_module_arguments()
            ),
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudLocationFacts.define_module()

    hcloud = AnsibleHcloudLocationFacts(module)
    hcloud.get_server_types()
    result = hcloud.get_result()
    ansible_facts = {
        'hcloud_server_type_facts': result['hcloud_server_type_facts']
    }
    module.exit_json(ansible_facts=ansible_facts)


if __name__ == "__main__":
    main()
