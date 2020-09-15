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
module: hcloud_volume_info

short_description: Gather infos about your Hetzner Cloud volumes.

version_added: "2.8"
description:
    - Gather infos about your Hetzner Cloud volumes.

author:
    - Lukas Kaemmerling (@LKaemmerling)

options:
    id:
        description:
            - The ID of the volume you want to get.
        type: int
    name:
        description:
            - The name of the volume you want to get.
        type: str
    label_selector:
        description:
            - The label selector for the volume you want to get.
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Gather hcloud volume infos
  hcloud_volume_info:
  register: output
- name: Print the gathered infos
  debug:
    var: output.hcloud_volume_info
"""

RETURN = """
hcloud_volume_info:
    description: The volume infos as list
    returned: always
    type: complex
    contains:
        id:
            description: Numeric identifier of the volume
            returned: always
            type: int
            sample: 1937415
        name:
            description: Name of the volume
            returned: always
            type: str
            sample: my-volume
        size:
            description: Size of the volume
            returned: always
            type: str
            sample: 10
        location:
            description: Name of the location where the volume resides in
            returned: always
            type: str
            sample: fsn1
        server:
            description: Name of the server where the volume is attached to
            returned: always
            type: str
            sample: my-server
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


class AnsibleHcloudVolumeInfo(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_volume_info")
        self.hcloud_volume_info = None

    def _prepare_result(self):
        tmp = []

        for volume in self.hcloud_volume_info:
            if volume is not None:
                server_name = None
                if volume.server is not None:
                    server_name = volume.server.name
                tmp.append({
                    "id": to_native(volume.id),
                    "name": to_native(volume.name),
                    "size": volume.size,
                    "location": to_native(volume.location.name),
                    "labels": volume.labels,
                    "server": to_native(server_name),
                })

        return tmp

    def get_volumes(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_volume_info = [self.client.volumes.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("name") is not None:
                self.hcloud_volume_info = [self.client.volumes.get_by_name(
                    self.module.params.get("name")
                )]
            elif self.module.params.get("label_selector") is not None:
                self.hcloud_volume_info = self.client.volumes.get_all(
                    label_selector=self.module.params.get("label_selector"))
            else:
                self.hcloud_volume_info = self.client.volumes.get_all()

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
    module = AnsibleHcloudVolumeInfo.define_module()

    is_old_facts = module._name == 'hcloud_volume_facts'
    if is_old_facts:
        module.deprecate("The 'hcloud_volume_facts' module has been renamed to 'hcloud_volume_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    hcloud = AnsibleHcloudVolumeInfo(module)

    hcloud.get_volumes()
    result = hcloud.get_result()
    if is_old_facts:
        ansible_info = {
            'hcloud_volume_facts': result['hcloud_volume_info']
        }
        module.exit_json(ansible_facts=ansible_info)
    else:
        ansible_info = {
            'hcloud_volume_info': result['hcloud_volume_info']
        }
        module.exit_json(**ansible_info)


if __name__ == "__main__":
    main()
