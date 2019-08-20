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
module: hcloud_location_info

short_description: Gather infos about your Hetzner Cloud locations.

version_added: "2.8"

description:
    - Gather infos about your Hetzner Cloud locations.
    - This module was called C(hcloud_location_facts) before Ansible 2.9, returning C(ansible_facts) and C(hcloud_location_facts).
      Note that the M(hcloud_location_info) module no longer returns C(ansible_facts) and the value was renamed to C(hcloud_location_info)!

author:
    - Lukas Kaemmerling (@LKaemmerling)

options:
    id:
        description:
            - The ID of the location you want to get.
        type: int
    name:
        description:
            - The name of the location you want to get.
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Gather hcloud location infos
  hcloud_location_info:
  register: output

- name: Print the gathered infos
  debug:
    var: output
"""

RETURN = """
hcloud_location_info:
    description: The location infos as list
    returned: always
    type: complex
    contains:
        id:
            description: Numeric identifier of the location
            returned: always
            type: int
            sample: 1937415
        name:
            description: Name of the location
            returned: always
            type: str
            sample: fsn1
        description:
            description: Detail description of the location
            returned: always
            type: str
            sample: Falkenstein DC Park 1
        country:
            description: Country code of the location
            returned: always
            type: str
            sample: DE
        city:
            description: City of the location
            returned: always
            type: str
            sample: Falkenstein
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.hcloud import Hcloud

try:
    from hcloud import APIException
except ImportError:
    pass


class AnsibleHcloudLocationInfo(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_location_info")
        self.hcloud_location_info = None

    def _prepare_result(self):
        tmp = []

        for location in self.hcloud_location_info:
            if location is not None:
                tmp.append({
                    "id": to_native(location.id),
                    "name": to_native(location.name),
                    "description": to_native(location.description),
                    "city": to_native(location.city),
                    "country": to_native(location.country)
                })
        return tmp

    def get_locations(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_location_info = [self.client.locations.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("name") is not None:
                self.hcloud_location_info = [self.client.locations.get_by_name(
                    self.module.params.get("name")
                )]
            else:
                self.hcloud_location_info = self.client.locations.get_all()

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
    module = AnsibleHcloudLocationInfo.define_module()

    is_old_facts = module._name == 'hcloud_location_facts'
    if is_old_facts:
        module.deprecate("The 'hcloud_location_info' module has been renamed to 'hcloud_location_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    hcloud = AnsibleHcloudLocationInfo(module)
    hcloud.get_locations()
    result = hcloud.get_result()
    if is_old_facts:
        ansible_info = {
            'hcloud_location_facts': result['hcloud_location_info']
        }
        module.exit_json(ansible_s=ansible_info)
    else:
        ansible_info = {
            'hcloud_location_info': result['hcloud_location_info']
        }
        module.exit_json(**ansible_info)


if __name__ == "__main__":
    main()
