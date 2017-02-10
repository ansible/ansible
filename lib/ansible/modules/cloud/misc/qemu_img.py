#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be>, Toshaan Bharvani <toshaan@vantosh.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = { 'status': ['preview'],
                     'supported_by': 'community',
                     'version': '1.0'}

DOCUMENTATION = '''
---
author:
  - Jeroen Hoekx (@jhoekx)
  - Toshaan Bharvani (@toshywoshy)
module: qemu_img
short_description: Create qemu images
description:
  - "This module creates images for qemu."
version_added: "2.3"
options:
  dest:
    description:
    - The image file to create or remove
    required: true
  format:
    description:
    - The image format - default qcow2
    default: qcow2
  size:
    description:
    - The size of the image in megabytes.
  options:
    description:
    - Comma separated list of format specific options in a name=value format.
  size:
    description:
    - The size of the image
  grow:
    choices: [ "yes", "no" ]
    defaults: "yes"
    description:
    - Whether the image should grow
  shrink:
    choices: [ "yes", "no" ]
    defaults: "no"
    description:
    - Whether the image should shrink
  state:
    choices: [ "absent", "present"]
    description:
    - If the image should be present or absent - default present
notes:
  - This module does not change the type/format of the image
  - This module does not take snapshots, and should be implemented seperate
'''

EXAMPLES = '''
# Create a raw image of 5M.
- qemu_img:
    dest: /tmp/testimg
    size: 5M
    format: raw

# Enlarge the image to 6G.
- qemu_img:
    dest: /tmp/testimg
    size: 6G
    format: qcow2

# Shrink the image by 3G
    code: qemu_img
    dest: /tmp/testing
    size: -3G
    shrink: yes
    format: qcow2

# Remove the image
- qemu_img:
    dest: /tmp/testimg
    state: absent
'''

RETURN = '''
# create qemu image
present:
  type: string
  sample: "success"
  returned: success
# remove qemu image
absent:
  type: string
  sample: "success"
  returned: success
# resize qemu image
resize:
  type: string
  sample: "success"
  returned: success
'''

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception

def main():

    module = AnsibleModule(
        argument_spec = dict(
            dest = dict(type='str', required=True),
            options = dict(type='str', default='preallocation=metadata'),
            format = dict(type='str', default='qcow2'),
            size = dict(type='str'),
            grow= dict(type="bool", default=True),
            shrink = dict(type="bool", default=False),
            state = dict(type='str', choices=['absent', 'present'], default='present'),
        ),
        supports_check_mode = True,
    )

    result = dict(
        changed = False,
    )

    state = module.params['state']
    dest = module.params['dest']
    img_format = module.params['format']
    img_options = module.params['options']
    size = module.params['size']
    grow = module.boolean(module.params['grow'])
    shrink = module.boolean(module.params['shrink'])

    qemu_img = module.get_bin_path('qemu-img', True)

    if state == 'present':
        if not size:
            module.fail_json(msg="No size defined, creating a disk image requires a size")
        if not os.path.exists(dest):
            if not module.check_mode:
                if not img_options:
                    module.run_command('%s create -f %s "%s" %s' % (qemu_img, img_format, dest, size), check_rc=True)
                else:
                    module.run_command('%s create -f %s -o "%s" "%s" %s' % (qemu_img, img_format, img_options, dest, size), check_rc=True)
            result['changed'] = True
        else:
            size_unit = size[-1:]
            if size_unit not in ['T','G','M','k','b','']:
                module.fail_json(msg="No valid size unit specified")
            else:
                if(size_unit == 'T'):
                    unitmultiplier = 1024*1024*1024*1024
                elif(size_unit == 'G'):
                    unitmultiplier = 1024*1024*1024
                elif(size_unit == 'M'):
                    unitmultiplier = 1024*1024
                elif(size_unit == 'k'):
                    unitmultiplier = 1024
                else:
                    unitmultiplier = 1
            size = size[:-1]
            size_increase = False
            size_decrease = False
            if(size[:1] == '+'):
                size_increase = True
                size = size[1:]
            elif(size[:1] == '-'):
                size_descrease = True
                size = size[1:]
            size = int(float(size)*float(unitmultiplier))
            rc, stdout, _ = module.run_command('%s info "%s"' % (qemu_img, dest), check_rc=True)
            current_size = None
            for line in stdout.splitlines():
                if 'virtual size' in line:
                    ### virtual size: 5.0M (5242880 bytes)
                    current_size = int(line.split('(')[1].split()[0])
            if not current_size:
                module.fail_json(msg='Unable to read virtual disk size of %s' % (dest))
            if(grow):
                newsize = size - current_size
                if(newsize > 0):
                    if not module.check_mode:
                        module.run_command('%s resize "%s" %s' % (qemu_img, dest, size), check_rc=True)
                    result['changed'] = True
            if(shrink):
                if(img_format == 'qcow2'):
                    module.fail_json(msg="qemu-img does not support shrinking qcow2 images")
                if (size[:1] == '-'):
                    newsize = current_size - size
                else:
                    newsize = current_size - size
                if(newsize > 0):
                    if not module.check_mode:
                        module.run_command('%s resize "%s" %s' % (qemu_img, dest, size), check_rc=True)
                    result['changed'] = True

    if state == 'absent':
        if os.path.exists(dest):
            if not module.check_mode:
                try:
                    os.remove(dest)
                except:
                    e = get_exception()
                    module.fail_json(msg=str(e))
            result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
