#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Adam Števko <adam.stevko@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: smartos_image_info
short_description: Get SmartOS image details.
description:
    - Retrieve information about all installed images on SmartOS.
    - This module was called C(smartos_image_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(smartos_image_info) module no longer returns C(ansible_facts)!
version_added: "2.2"
author: Adam Števko (@xen0l)
options:
    filters:
        description:
            - Criteria for selecting image. Can be any value from image
              manifest and 'published_date', 'published', 'source', 'clones',
              and 'size'. More information can be found at U(https://smartos.org/man/1m/imgadm)
              under 'imgadm list'.
'''

EXAMPLES = '''
# Return information about all installed images.
- smartos_image_info:
  register: result

# Return all private active Linux images.
- smartos_image_info: filters="os=linux state=active public=false"
  register: result

# Show, how many clones does every image have.
- smartos_image_info:
  register: result

- debug: msg="{{ result.smartos_images[item]['name'] }}-{{ result.smartos_images[item]['version'] }}
            has {{ result.smartos_images[item]['clones'] }} VM(s)"
  with_items: "{{ result.smartos_images.keys() | list }}"

# When the module is called as smartos_image_facts, return values are published
# in ansible_facts['smartos_images'] and can be used as follows.
# Note that this is deprecated and will stop working in Ansible 2.13.
- debug: msg="{{ smartos_images[item]['name'] }}-{{ smartos_images[item]['version'] }}
            has {{ smartos_images[item]['clones'] }} VM(s)"
  with_items: "{{ smartos_images.keys() | list }}"
'''

RETURN = '''
'''

import json
from ansible.module_utils.basic import AnsibleModule


class ImageFacts(object):

    def __init__(self, module):
        self.module = module

        self.filters = module.params['filters']

    def return_all_installed_images(self):
        cmd = [self.module.get_bin_path('imgadm')]

        cmd.append('list')
        cmd.append('-j')

        if self.filters:
            cmd.append(self.filters)

        (rc, out, err) = self.module.run_command(cmd)

        if rc != 0:
            self.module.exit_json(
                msg='Failed to get all installed images', stderr=err)

        images = json.loads(out)

        result = {}
        for image in images:
            result[image['manifest']['uuid']] = image['manifest']
            # Merge additional attributes with the image manifest.
            for attrib in ['clones', 'source', 'zpool']:
                result[image['manifest']['uuid']][attrib] = image[attrib]

        return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            filters=dict(default=None),
        ),
        supports_check_mode=False,
    )
    is_old_facts = module._name == 'smartos_image_facts'
    if is_old_facts:
        module.deprecate("The 'smartos_image_facts' module has been renamed to 'smartos_image_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    image_facts = ImageFacts(module)

    data = dict(smartos_images=image_facts.return_all_installed_images())

    if is_old_facts:
        module.exit_json(ansible_facts=data)
    else:
        module.exit_json(**data)


if __name__ == '__main__':
    main()
