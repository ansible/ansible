#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Adam Števko <adam.stevko@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.
#

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
        required: false
        default: None
'''

EXAMPLES = '''
# Return facts about all installed images.
smartos_image_facts:

# Return all private active Linux images.
smartos_image_facts: filters="os=linux state=active public=false"

# Show, how many clones does every image have.
smartos_image_facts:

debug: msg="{{ smartos_images[item]['name'] }}-{{smartos_images[item]['version'] }}
            has {{ smartos_images[item]['clones'] }} VM(s)"
with_items: "{{ smartos_images.keys() }}"
'''

RETURN = '''
# this module returns ansible_facts
'''

try:
    import json
except ImportError:
    import simplejson as json


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

    data = {}
    data['smartos_images'] = image_facts.return_all_installed_images()

    module.exit_json(ansible_facts=data)

from ansible.module_utils.basic import *
main()
