#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be>
# (c) 2016, Matt Robinson <git@nerdoftheherd.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
author:
- Jeroen Hoekx (@jhoekx)
- Matt Robinson (@ribbons)
module: iso_extract
short_description: Extract files from an ISO image.
description:
- This module mounts an iso image in a temporary directory and extracts
  files from there to a given destination.
version_added: "2.3"
options:
  image:
    description:
    - The ISO image to extract files from.
    required: true
    aliases: ['path', 'src']
  dest:
    description:
    - The destination directory to extract files to.
    required: true
  files:
    description:
    - A list of files to extract from the image.
    - Extracting directories does not work.
    required: true
notes:
- Only the file hash (content) is taken into account for extracting files
  from the ISO image.
'''

EXAMPLES = r'''
- name: Extract kernel and ramdisk from a LiveCD
  iso_extract:
    image: /tmp/rear-test.iso
    dest: /tmp/virt-rear/
    files:
    - isolinux/kernel
    - isolinux/initrd.cgz
'''

RETURN = r'''
#
'''

import os
import shutil
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception

def main():
    module = AnsibleModule(
        argument_spec = dict(
            image = dict(required=True, type='path', aliases=['path', 'src']),
            dest = dict(required=True, type='path'),
            files = dict(required=True, type='list'),
        ),
        supports_check_mode = True,
    )
    image = module.params['image']
    dest = module.params['dest']
    files = module.params['files']

    changed = False

    if not os.path.exists(dest):
        module.fail_json(msg='Directory "%s" does not exist' % dest)

    if not os.path.exists(os.path.dirname(image)):
        module.fail_json(msg='ISO image "%s" does not exist' % image)

    tmp_dir = tempfile.mkdtemp()
    rc, out, err = module.run_command('mount -o loop,ro "%s" "%s"' % (image, tmp_dir))
    if rc != 0:
        os.rmdir(tmp_dir)
        module.fail_json(msg='Failed to mount ISO image "%s"' % image)

    e = None
    try:
        for file in files:
            tmp_src = os.path.join(tmp_dir, file)
            src_hash = module.sha1(tmp_src)

            dest_file = os.path.join(dest, os.path.basename(file))

            if os.path.exists(dest_file):
                dest_hash = module.sha1(dest_file)
            else:
                dest_hash = None

            if src_hash != dest_hash:
                if not module.check_mode:
                    shutil.copy(tmp_src, dest_file)

                changed = True
    finally:
        module.run_command('umount "%s"' % tmp_dir)
        os.rmdir(tmp_dir)

    module.exit_json(changed=changed)

if __name__ == '__main__':
    main()
