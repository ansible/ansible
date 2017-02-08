#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be>
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

DOCUMENTATION = '''
---
author: Jeroen Hoekx
module: qemu_img
short_description: Create qemu images
description:
  - "This module creates images for qemu."
version_added: "1.2"
options:
  dest:
    description:
    - The image file to create or remove
    required: true
  format:
    description:
    - The image format - default qcow2
    required: false
  size:
    description:
    - The size of the image in megabytes.
    required: false
  opt:
    description:
    - Comma separated list of format specific options in a name=value format.
    required: false
  state:
    choices: [ "absent", "present" ]
    description:
    - If the image should be present or absent - default present
    required: false
examples:
  - description: Create a raw image of 5M.
    code: qemu_img dest=/tmp/testimg size=5 format=raw
  - description: Enlarge the image to 6M.
    code: qemu_img dest=/tmp/testimg size=6 format=raw
  - description: Remove the image
    code: qemu_img dest=/tmp/testimg state=absent
notes:
  - This module does not change the type of the image.
'''

import os

from ansible.module_utils.basic import AnsibleModule

def main():

    module = AnsibleModule(
        argument_spec = dict(
            dest = dict(type='str', required=True),
            opt = dict(type='str'),
            format = dict(type='str', default='qcow2'),
            size = dict(type='int'),
            state = dict(type='str', choices=['absent', 'present'], default='present'),
        ),
        supports_check_mode = True,
    )

    changed = False
    qemu_img = module.get_bin_path('qemu-img', True)

    dest = module.params['dest']
    img_format = module.params['format']
    opt = module.params['opt']

    if module.params['state'] == 'present':
        if not module.params['size']:
            module.fail_json(msg="Parameter 'size' required")
        size = module.params['size'] * 1024 * 1024

        if not os.path.exists(dest):
            if not module.check_mode:
                if not opt:
                    module.run_command('%s create -f %s "%s" %s'%(qemu_img, img_format, dest, size), check_rc=True)
                else:
                    module.run_command('%s create -f %s -o %s "%s" %s'%(qemu_img, img_format, opt, dest, size), check_rc=True)
            changed = True
        else:
            rc, stdout, _ = module.run_command('%s info "%s"'%(qemu_img, dest), check_rc=True)
            current_size = None
            for line in stdout.splitlines():
                if 'virtual size' in line:
                    ### virtual size: 5.0M (5242880 bytes)
                    current_size = int(line.split('(')[1].split()[0])
            if not current_size:
                module.fail_json(msg='Unable to read virtual disk size of %s'%(dest))
            if current_size != size:
                if not module.check_mode:
                    module.run_command('%s resize "%s" %s'%(qemu_img, dest, size), check_rc=True)
                changed = True

    if module.params['state'] == 'absent':
        if os.path.exists(dest):
            if not module.check_mode:
                os.remove(dest)
            changed = True

    module.exit_json(changed=changed)

if __name__ == '__main__':
    main()
