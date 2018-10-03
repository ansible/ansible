#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: filament
short_description: just Tutorial
description:
   - Tutorial module
version_added: "2.8"
notes:
   - Tutorial module
options:
  data:
    description:
      - Tutorial module
    default: hello world
author:
    - Takashi Sugimura
'''

EXAMPLES = '''
- filament:
'''

RETURN = '''
filament:
    description: value provided with the data parameter
    returned: success
    type: string
    sample: hello world
'''

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            data=dict(type='str', default='hello world'),
        ),
        supports_check_mode=True
    )

    if module.params['data'] == 'crash':
        raise Exception("boom")

    result = dict(
        ping=module.params['data'],
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
