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
module: hcloud_image_info

short_description: Gather infos about your Hetzner Cloud images.

version_added: "2.8"

description:
    - Gather infos about your Hetzner Cloud images.
    - This module was called C(hcloud_location_facts) before Ansible 2.9, returning C(ansible_facts) and C(hcloud_location_facts).
      Note that the M(hcloud_image_info) module no longer returns C(ansible_facts) and the value was renamed to C(hcloud_image_info)!

author:
    - Lukas Kaemmerling (@LKaemmerling)

options:
    id:
        description:
            - The ID of the image you want to get.
        type: int
    name:
        description:
            - The name of the image you want to get.
        type: str
    label_selector:
        description:
            - The label selector for the images you want to get.
        type: str
    type:
        description:
            - The label selector for the images you want to get.
        default: system
        choices: [ system, snapshot, backup ]
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Gather hcloud image infos
  hcloud_image_info:
  register: output

- name: Print the gathered infos
  debug:
    var: output
"""

RETURN = """
hcloud_image_info:
    description: The image infos as list
    returned: always
    type: complex
    contains:
        id:
            description: Numeric identifier of the image
            returned: always
            type: int
            sample: 1937415
        type:
            description: Type of the image
            returned: always
            type: str
            sample: system
        status:
            description: Status of the image
            returned: always
            type: str
            sample: available
        name:
            description: Name of the image
            returned: always
            type: str
            sample: ubuntu-18.04
        description:
            description: Detail description of the image
            returned: always
            type: str
            sample: Ubuntu 18.04 Standard 64 bit
        os_flavor:
            description: OS flavor of the image
            returned: always
            type: str
            sample: ubuntu
        os_version:
            description: OS version of the image
            returned: always
            type: str
            sample: 18.04
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


class AnsibleHcloudImageInfo(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_image_info")
        self.hcloud_image_info = None

    def _prepare_result(self):
        tmp = []

        for image in self.hcloud_image_info:
            if image is not None:
                tmp.append({
                    "id": to_native(image.id),
                    "status": to_native(image.status),
                    "type": to_native(image.type),
                    "name": to_native(image.name),
                    "description": to_native(image.description),
                    "os_flavor": to_native(image.os_flavor),
                    "os_version": to_native(image.os_version),
                    "labels": image.labels,
                })
        return tmp

    def get_images(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_image_info = [self.client.images.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("name") is not None:
                self.hcloud_image_info = [self.client.images.get_by_name(
                    self.module.params.get("name")
                )]
            else:
                params = {}
                label_selector = self.module.params.get("label_selector")
                if label_selector:
                    params["label_selector"] = label_selector

                image_type = self.module.params.get("type")
                if image_type:
                    params["type"] = image_type

                self.hcloud_image_info = self.client.images.get_all(**params)

        except APIException as e:
            self.module.fail_json(msg=e.message)

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                name={"type": "str"},
                label_selector={"type": "str"},
                type={"choices": ["system", "snapshot", "backup"], "default": "system", "type": "str"},
                **Hcloud.base_module_arguments()
            ),
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudImageInfo.define_module()

    is_old_facts = module._name == 'hcloud_image_facts'
    if is_old_facts:
        module.deprecate("The 'hcloud_image_facts' module has been renamed to 'hcloud_image_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    hcloud = AnsibleHcloudImageInfo(module)
    hcloud.get_images()
    result = hcloud.get_result()

    if is_old_facts:
        ansible_info = {
            'hcloud_imagen_facts': result['hcloud_image_info']
        }
        module.exit_json(ansible_s=ansible_info)
    else:
        ansible_info = {
            'hcloud_image_info': result['hcloud_image_info']
        }
        module.exit_json(**ansible_info)


if __name__ == "__main__":
    main()
