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
module: hcloud_floating_ip_info

short_description: Gather infos about the Hetzner Cloud Floating IPs.

version_added: "2.8"
description:
    - Gather facts about your Hetzner Cloud Floating IPs.
    - This module was called C(hcloud_floating_ip_facts) before Ansible 2.9, returning C(ansible_facts) and C(hcloud_floating_ip_facts).
      Note that the M(hcloud_floating_ip_info) module no longer returns C(ansible_facts) and the value was renamed to C(hcloud_floating_ip_info)!

author:
    - Lukas Kaemmerling (@LKaemmerling)

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
- name: Gather hcloud Floating ip infos
  hcloud_floating_ip_info:
  register: output
- name: Print the gathered infos
  debug:
    var: output
"""

RETURN = """
hcloud_floating_ip_info:
    description: The Floating ip infos as list
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


class AnsibleHcloudFloatingIPInfo(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_floating_ip_info")
        self.hcloud_floating_ip_info = None

    def _prepare_result(self):
        tmp = []

        for floating_ip in self.hcloud_floating_ip_info:
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
                self.hcloud_floating_ip_info = [self.client.floating_ips.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("label_selector") is not None:
                self.hcloud_floating_ip_info = self.client.floating_ips.get_all(
                    label_selector=self.module.params.get("label_selector"))
            else:
                self.hcloud_floating_ip_info = self.client.floating_ips.get_all()

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
    module = AnsibleHcloudFloatingIPInfo.define_module()

    is_old_facts = module._name == 'hcloud_floating_ip_facts'
    if is_old_facts:
        module.deprecate("The 'hcloud_floating_ip_facts' module has been renamed to 'hcloud_floating_ip_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    hcloud = AnsibleHcloudFloatingIPInfo(module)

    hcloud.get_floating_ips()
    result = hcloud.get_result()
    if is_old_facts:
        ansible_info = {
            'hcloud_floating_ip_facts': result['hcloud_floating_ip_info']
        }
        module.exit_json(ansible_facts=ansible_info)
    else:
        ansible_info = {
            'hcloud_floating_ip_info': result['hcloud_floating_ip_info']
        }
        module.exit_json(**ansible_info)


if __name__ == "__main__":
    main()
