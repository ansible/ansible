#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, David Shrewsbury <dshrewsb@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: filament
version_added: '2.10'
short_description: Test module
description:
    - Just a test module.
author: "David Shrewsbury (@Shrews)"
'''

EXAMPLES = '''
'''

RETURN = ''' # '''

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type


def run_module():
    module = AnsibleModule(argument_spec={})
    result = dict(changed=True)
    result['myvar'] = 'world'
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
