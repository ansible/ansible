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
module: hcloud_datacenter_info

short_description: Gather info about the Hetzner Cloud datacenters.

version_added: "2.8"
description:
    - Gather info about your Hetzner Cloud datacenters.
    - This module was called C(hcloud_datacenter_facts) before Ansible 2.9, returning C(ansible_facts) and C(hcloud_datacenter_facts).
      Note that the M(hcloud_datacenter_info) module no longer returns C(ansible_facts) and the value was renamed to C(hcloud_datacenter_info)!

author:
    - Lukas Kaemmerling (@LKaemmerling)

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
- name: Gather hcloud datacenter info
  hcloud_datacenter_info:
  register: output
- name: Print the gathered info
  debug:
    var: output
"""

RETURN = """
hcloud_datacenter_info:
    description:
      - The datacenter info as list
      - This module was called C(hcloud_datacenter_facts) before Ansible 2.9, returning C(ansible_facts) and C(hcloud_datacenter_facts).
        Note that the M(hcloud_datacenter_info) module no longer returns C(ansible_facts) and the value was renamed to C(hcloud_datacenter_info)!
    returned: always
    type: complex
    contains:
        id:
            description: Numeric identifier of the datacenter
            returned: always
            type: int
            sample: 1937415
        name:
            description: Name of the datacenter
            returned: always
            type: str
            sample: fsn1-dc8
        description:
            description: Detail description of the datacenter
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


class AnsibleHcloudDatacenterInfo(Hcloud):
    def __init__(self, module):
        Hcloud.__init__(self, module, "hcloud_datacenter_info")
        self.hcloud_datacenter_info = None

    def _prepare_result(self):
        tmp = []

        for datacenter in self.hcloud_datacenter_info:
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
                self.hcloud_datacenter_info = [self.client.datacenters.get_by_id(
                    self.module.params.get("id")
                )]
            elif self.module.params.get("name") is not None:
                self.hcloud_datacenter_info = [self.client.datacenters.get_by_name(
                    self.module.params.get("name")
                )]
            else:
                self.hcloud_datacenter_info = self.client.datacenters.get_all()

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
    module = AnsibleHcloudDatacenterInfo.define_module()

    is_old_facts = module._name == 'hcloud_datacenter_facts'
    if is_old_facts:
        module.deprecate("The 'hcloud_datacenter_facts' module has been renamed to 'hcloud_datacenter_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')
    hcloud = AnsibleHcloudDatacenterInfo(module)

    hcloud.get_datacenters()
    result = hcloud.get_result()
    if is_old_facts:
        ansible_info = {
            'hcloud_datacenter_facts': result['hcloud_datacenter_info']
        }
        module.exit_json(ansible_facts=ansible_info)
    else:
        ansible_info = {
            'hcloud_datacenter_info': result['hcloud_datacenter_info']
        }
        module.exit_json(**ansible_info)


if __name__ == "__main__":
    main()
