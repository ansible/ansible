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
module: smartos_image_facts
short_description: Get SmartOS image details.
description:
    - Retrieve facts about all installed images on SmartOS. Facts will be
      inserted to the ansible_facts key.
version_added: "2.2"
author: Adam Števko (@xen0l)
options:
    filters:
        description:
            - Criteria for selecting image. Can be any value from image
              manifest and 'published_date', 'published', 'source', 'clones',
              and 'size'. More informaton can be found at U(https://smartos.org/man/1m/imgadm)
              under 'imgadm list'.
'''

EXAMPLES = '''
# Return facts about all installed images.
- smartos_image_facts:

# Return all private active Linux images.
- smartos_image_facts: filters="os=linux state=active public=false"

# Show, how many clones does every image have.
- smartos_image_facts:

- debug: msg="{{ smartos_images[item]['name'] }}-{{smartos_images[item]['version'] }}
            has {{ smartos_images[item]['clones'] }} VM(s)"
  with_items: "{{ smartos_images.keys() }}"
'''

RETURN = '''
# this module returns ansible_facts
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

    image_facts = ImageFacts(module)

    data = dict(smartos_images=image_facts.return_all_installed_images())

    module.exit_json(ansible_facts=data)


if __name__ == '__main__':
    main()
