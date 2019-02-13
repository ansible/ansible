#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Jeroen Hoekx <jeroen.hoekx@dsquare.be>
# Copyright: (c) 2013, Toshaan Bharvani <toshaan@vantosh.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = r'''
---
author:
- Jeroen Hoekx (@jhoekx)
- Toshaan Bharvani (@toshywoshy)
module: qemu_img
short_description: Manage qemu images
description:
- This module creates images for qemu.
version_added: '2.8'
options:
  dest:
    description:
    - The image file to create or remove.
    type: str
    required: true
  format:
    description:
    - The image format.
    type: str
    default: qcow2
  options:
    description:
    - List of format specific options in a name=value format.
    type: list
  size:
    description:
    - The size of the image.
    type: str
  grow:
    description:
    - Whether the image is allowed grow.
    type: bool
    default: yes
  shrink:
    description:
    - Whether the image is allowed shrink.
    type: bool
    default: no
  state:
    description:
    - If the image should be present or absent.
    type: str
    default: present
    choices: [ absent, present ]
notes:
  - This module does not change the type/format of the image.
  - This module does not take snapshots, and should be implemented seperate.
'''

EXAMPLES = r'''
- name: Create a raw image of 5M.
  qemu_img:
    dest: /tmp/testimg
    size: 5M
    format: raw

- name: Enlarge the image to 6G.
  qemu_img:
    dest: /tmp/testimg
    size: 6G
    format: qcow2

- name: Shrink the image by 3G
  qemu_img:
    dest: /tmp/testing
    size: -3G
    shrink: yes
    format: qcow2

- name: Remove the image
  qemu_img:
    dest: /tmp/testimg
    state: absent
'''

RETURN = r'''
# create qemu image
present:
  description:
  - Returns the status of the qemu image that was created
  type: str
  sample: success
  returned: success
# remove qemu image
absent:
  description:
  - Returns the status of the qemu image that was removed
  type: str
  sample: success
  returned: success
# resize qemu image
resize:
  description:
  - Returns the status of the qemu image that was resized
  type: str
  sample: success
  returned: success
'''

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():

    module = AnsibleModule(
        argument_spec=dict(
            dest=dict(type='str', required=True),
            options=dict(type='list', default='preallocation=metadata'),
            format=dict(type='str', default='qcow2'),
            size=dict(type='str'),
            grow=dict(type="bool", default=True),
            shrink=dict(type="bool", default=False),
            state=dict(type='str', default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ["size"]),
        ],
    )

    result = dict(
        changed=False,
    )

    state = module.params['state']
    dest = module.params['dest']
    img_format = module.params['format']
    img_options = ','.join(module.params['options'])
    size = module.params['size']
    grow = module.params['grow']
    shrink = module.params['shrink']

    qemu_img = module.get_bin_path('qemu-img', True)

    if state == 'present':
        if not os.path.exists(dest):
            if not module.check_mode:
                if not img_options:
                    rc, stdout, stderr = module.run_command('%s create -f %s "%s" %s' % (qemu_img, img_format, dest, size), check_rc=True)
                else:
                    rc, stdout, stderr = module.run_command('%s create -f %s -o "%s" "%s" %s' % (qemu_img, img_format, img_options, dest, size), check_rc=True)
            result['changed'] = True
        else:
            try:
                size_unit = str(size[-1:])
                size = size[:-1]
            except Exception as e:
                size_unit = 'b'
            try:
                units = list(['b', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'])
                unitmultiplier = 1024**units.index(size_unit)
            except Exception as e:
                module.fail_json(msg='Unknown size unit : %s' % (size_unit))
            size_increase = False
            size_decrease = False
            if (size[:1] == '+'):
                size_increase = True
                size = size[1:]
            elif (size[:1] == '-'):
                size_descrease = True
                size = size[1:]
            size = int(float(size) * float(unitmultiplier))
            rc, stdout, stderr = module.run_command('%s info "%s"' % (qemu_img, dest), check_rc=True)
            current_size = None
            for line in stdout.splitlines():
                if 'virtual size' in line:
                    # virtual size: 5.0M (5242880 bytes)
                    current_size = int(line.split('(')[1].split()[0])
            if not current_size:
                module.fail_json(msg='Unable to read virtual disk size of %s' % (dest))
            if (grow):
                newsize = size - current_size
                if (newsize > 0):
                    if not module.check_mode:
                        rc, stdout, stderr = module.run_command('%s resize "%s" %s' % (qemu_img, dest, size), check_rc=True)
                    result['changed'] = True
            if (shrink):
                if (img_format == 'qcow2'):
                    module.fail_json(msg="qemu-img does not support shrinking qcow2 images")
                if (size[:1] == '-'):
                    newsize = current_size - size
                else:
                    newsize = current_size - size
                if (newsize > 0):
                    if not module.check_mode:
                        rc, stdout, stderr = module.run_command('%s resize "%s" %s' % (qemu_img, dest, size), check_rc=True)
                    result['changed'] = True

    if state == 'absent':
        if os.path.exists(dest):
            if not module.check_mode:
                try:
                    os.remove(dest)
                except Exception as e:
                    module.fail_json(msg=to_native(e))
            result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
