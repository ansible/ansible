#!/usr/bin/python

#
# Copyright (c) 2018 Red Hat, Inc.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: filament

short_description: This is my sample module

version_added: "2.4"

description:
    - "This is my longer description explaining my sample module"

options:
    foo:
        choices:
            - a
            - b
            - c
        description:
            - The foobar argument
        required: true

author:
    - Zhikang Zhang (@redhat.com)
'''

EXAMPLES = '''
# Create a VDO volume
- name: Create 2 TB VDO volume vdo1 on device /dev/md0
  vdo:
    name: vdo1
    state: present
    device: /dev/md0
    logicalsize: 2T

# Remove a VDO volume
- name: Remove VDO volume vdo1
  vdo:
    name: vdo1
    state: absent
'''

from ansible.module_utils.basic import AnsibleModule
import pdb


def main():
    module_args = dict(foo=dict(choices=["a", "b", "c"]))
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )
    foo = module.params["foo"]
    pdb.set_trace()


if __name__ == "__main__":
    main()
