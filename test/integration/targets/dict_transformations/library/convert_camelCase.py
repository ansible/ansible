#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: convert_camelCase
short_description: test converting data to camelCase
description: test converting data to camelCase
options:
  data:
    description: Data to modify
    type: dict
    required: True
  capitalize_first:
    description: Whether to capitalize the first character
    default: False
    type: bool
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict


def main():
    module = AnsibleModule(
        argument_spec=dict(
            data=dict(type='dict', required=True),
            capitalize_first=dict(type='bool', default=False),
        ),
    )

    result = snake_dict_to_camel_dict(
        module.params['data'],
        module.params['capitalize_first']
    )

    module.exit_json(data=result)


if __name__ == '__main__':
    main()
