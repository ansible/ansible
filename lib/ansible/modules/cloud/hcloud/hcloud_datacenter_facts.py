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
module: hcloud_datacenter_facts

short_description: Gather facts about the Hetzner Cloud datacenters.

version_added: "2.8"
description:
    - Gather facts about your Hetzner Cloud datacenters.

author:
    - Lukas Kaemmerling (@lkaemmerling)

options:
    id:
        description:
            - The ID of the datacenter you want to get.
        type: int
    name:
        description:
            - The name of the datacenter you want to get.
        type: str
extends_documentation_fragment: hcloud
"""

EXAMPLES = """
- name: Gather hcloud datacenter facts
  local_action:
    module: hcloud_datacenter_facts
- name: Print the gathered facts
  debug:
    var: ansible_facts.hcloud_datacenter_facts
"""

RETURN = """
hcloud_datacenter_facts:
    description: The datacenter facts as list
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
            sample: fsn1-dc8
        description:
            description: Detail description of the location
            returned: always
            type: str
            sample: Falkenstein DC 8
        location:
            description: Name of the location where the datacenter resides in
            returned: always
            type: str
            sample: fsn1
        city:
            description: City of the location
            returned: always
            type: str
            sample: fsn1
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.hcloud import Hcloud

try:
    from hcloud import APIException
except ImportError:
    pass


class AnsibleHcloudDatacenterFacts(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_datacenter_facts")
        self.hcloud_datacenter_facts = None

    def _prepare_result(self):
        tmp = []

        for datacenter in self.hcloud_datacenter_facts:
            if datacenter is not None:
                tmp.append({
                    "id": to_native(datacenter.id),
                    "name": to_native(datacenter.name),
                    "description": to_native(datacenter.description),
                    "location": to_native(datacenter.location.name)
                })

        return tmp

    def get_datacenters(self):
        try:
            if self.module.params.get("id") is not None:
                self.hcloud_datacenter_facts = [self.client.datacenters.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("name") is not None:
                self.hcloud_datacenter_facts = [self.client.datacenters.get_by_name(
                    self.module.params.get("name")
                )]
            else:
                self.hcloud_datacenter_facts = self.client.datacenters.get_all()

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
    module = AnsibleHcloudDatacenterFacts.define_module()

    hcloud = AnsibleHcloudDatacenterFacts(module)

    hcloud.get_datacenters()
    result = hcloud.get_result()
    ansible_facts = {
        'hcloud_datacenter_facts': result['hcloud_datacenter_facts']
    }
    module.exit_json(ansible_facts=ansible_facts)


if __name__ == "__main__":
    main()
