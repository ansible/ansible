#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Cumulus Networks <ce-ceng@cumulusnetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cl_img_install
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Install a different Cumulus Linux version.
deprecated:
  removed_in: "2.5"
  why: The image slot system no longer exists in Cumulus Linux.
  alternative: n/a
description:
    - install a different version of Cumulus Linux in the inactive slot. For
      more details go the Image Management User Guide at
      U(http://docs.cumulusnetworks.com/).
options:
    src:
        description:
            - The full path to the Cumulus Linux binary image. Can be a local path,
              http or https URL. If the code version is in the name of the file,
              the module will assume this is the version of code you wish to
              install.
        required: true
    version:
        description:
            - Inform the module of the exact version one is installing. This
              overrides the automatic check of version in the file name. For
              example, if the binary file name is called CumulusLinux-2.2.3.bin,
              and version is set to '2.5.0', then the module will assume it is
              installing '2.5.0' not '2.2.3'. If version is not included, then
              the module will assume '2.2.3' is the version to install.
    switch_slot:
        description:
            - Switch slots after installing the image.
              To run the installed code, reboot the switch.
        type: bool

requirements: ["Cumulus Linux OS"]

'''
EXAMPLES = '''
## Download and install the image from a webserver.
- name: Install image using using http url. Switch slots so the subsequent will load the new version
  cl_img_install:
    version: 2.0.1
    src: http://10.1.1.1/CumulusLinux-2.0.1.bin
    switch_slot: yes

## Copy the software from the ansible server to the switch.
## The module will get the code version from the filename
## The code will be installed in the alternate slot but the slot will not be primary
## A subsequent reload will not run the new code

- name: Download cumulus linux to local system
  get_url:
    src: ftp://cumuluslinux.bin
    dest: /root/CumulusLinux-2.0.1.bin

- name: Install image from local filesystem. Get version from the filename.
  cl_img_install:
    src: /root/CumulusLinux-2.0.1.bin

## If the image name has been changed from the original name, use the `version` option
## to inform the module exactly what code version is been installed

- name: Download cumulus linux to local system
  get_url:
    src: ftp://CumulusLinux-2.0.1.bin
    dest: /root/image.bin

- name: install image and switch slots. Only reboot needed
  cl_img_install:
    version: 2.0.1
    src: /root/image.bin
    switch_slot: yes
'''

RETURN = '''
changed:
    description: whether the interface was changed
    returned: changed
    type: bool
    sample: True
msg:
    description: human-readable report of success or failure
    returned: always
    type: string
    sample: "interface bond0 config updated"
'''

from ansible.module_utils.common.removed import removed_module

if __name__ == '__main__':
    removed_module()
