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
module: hcloud_floating_ip_facts

short_description: Gather facts about the Hetzner Cloud Floating IPs.

version_added: "2.8"
description:
    - Gather facts about your Hetzner Cloud Floating IPs.

author:
    - Lukas Kaemmerling (@lkaemmerling)

options:
    id:
        description:
            - The ID of the Floating IP you want to get.
        type: int
    label_selector:
        description:
            - The label selector for the Floating IP you want to get.
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Gather hcloud Floating ip facts
  local_action:
    module: hcloud_floating_ip_facts
- name: Print the gathered facts
  debug:
    var: ansible_facts.hcloud_floating_ip_facts
"""

RETURN = """
hcloud_floating_ip_facts:
    description: The Floating ip facts as list
    returned: always
    type: complex
    contains:
        id:
            description: Numeric identifier of the Floating IP
            returned: always
            type: int
            sample: 1937415
        description:
            description: Description of the Floating IP
            returned: always
            type: str
            sample: Falkenstein DC 8
        ip:
            description: IP address of the Floating IP
            returned: always
            type: str
            sample: 131.232.99.1
        type:
            description: Type of the Floating IP
            returned: always
            type: str
            sample: ipv4
        server:
            description: Name of the server where the Floating IP is assigned to.
            returned: always
            type: str
            sample: my-server
        home_location:
            description: Location the Floating IP was created in
            returned: always
            type: str
            sample: fsn1
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


class AnsibleHcloudFloatingIPFacts(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_floating_ip_facts")
        self.hcloud_floating_ip_facts = None

    def _prepare_result(self):
        tmp = []

        for floating_ip in self.hcloud_floating_ip_facts:
            if floating_ip is not None:
                server_name = None
                if floating_ip.server is not None:
                    server_name = floating_ip.server.name
                tmp.append({
                    "id": to_native(floating_ip.id),
                    "description": to_native(floating_ip.description),
                    "ip": to_native(floating_ip.ip),
                    "type": to_native(floating_ip.type),
                    "server": to_native(server_name),
                    "home_location": to_native(floating_ip.home_location.name),
                    "labels": floating_ip.labels,
                })

        return tmp

    def get_floating_ips(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_floating_ip_facts = [self.client.floating_ips.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("label_selector") is not None:
                self.hcloud_floating_ip_facts = self.client.floating_ips.get_all(
                    label_selector=self.module.params.get("label_selector"))
            else:
                self.hcloud_floating_ip_facts = self.client.floating_ips.get_all()

        except APIException as e:
            self.module.fail_json(msg=e.message)

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                label_selector={"type": "str"},
                **Hcloud.base_module_arguments()
            ),
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudFloatingIPFacts.define_module()

    hcloud = AnsibleHcloudFloatingIPFacts(module)

    hcloud.get_floating_ips()
    result = hcloud.get_result()
    ansible_facts = {
        'hcloud_floating_ip_facts': result['hcloud_floating_ip_facts']
    }
    module.exit_json(ansible_facts=ansible_facts)


if __name__ == "__main__":
    main()
