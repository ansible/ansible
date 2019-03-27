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
module: hcloud_image_facts

short_description: Gather facts about your Hetzner Cloud images.

version_added: "2.8"

description:
    - Gather facts about your Hetzner Cloud images.

author:
    - Lukas Kaemmerling (@lkaemmerling)

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
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Gather hcloud image facts
  local_action:
    module: hcloud_image_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.hcloud_image_facts
"""

RETURN = """
hcloud_image_facts:
    description: The image facts as list
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


class AnsibleHcloudImageFacts(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_image_facts")
        self.hcloud_image_facts = None

    def _prepare_result(self):
        tmp = []

        for image in self.hcloud_image_facts:
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

    def get_servers(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_image_facts = [self.client.images.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("name") is not None:
                self.hcloud_image_facts = [self.client.images.get_by_name(
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

                self.hcloud_image_facts = self.client.images.get_all(**params)

        except APIException as e:
            self.module.fail_json(msg=e.message)

    @staticmethod
    def define_module():
        return AnsibleModule(
            argument_spec=dict(
                id={"type": "int"},
                name={"type": "str"},
                label_selector={"type": "str"},
                type={"choices": ["system", "snapshot", "backup"], "default": "system"},
                **Hcloud.base_module_arguments()
            ),
            supports_check_mode=True,
        )


def main():
    module = AnsibleHcloudImageFacts.define_module()

    hcloud = AnsibleHcloudImageFacts(module)
    hcloud.get_servers()
    result = hcloud.get_result()
    ansible_facts = {
        'hcloud_image_facts': result['hcloud_image_facts']
    }
    module.exit_json(ansible_facts=ansible_facts)


if __name__ == "__main__":
    main()
