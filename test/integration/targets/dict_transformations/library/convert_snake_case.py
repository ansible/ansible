#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
---
module: convert_snake_case
short_description: test converting data to snake_case
description: test converting data to snake_case
options:
  data:
    description: Data to modify
    type: dict
    required: True
  reversible:
    description:
      - Make the snake_case conversion in a way that can be converted back to the original value
      - For example, convert IAMUser to i_a_m_user instead of iam_user
    default: False
  ignore_list:
    description: list of top level keys that should not have their contents converted
    type: list
    default: []
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict


def main():
    module = AnsibleModule(
        argument_spec=dict(
            data=dict(type='dict', required=True),
            reversible=dict(type='bool', default=False),
            ignore_list=dict(type='list', default=[]),
        ),
    )

    result = camel_dict_to_snake_dict(
        module.params['data'],
        module.params['reversible'],
        module.params['ignore_list']
    )

    module.exit_json(data=result)


if __name__ == '__main__':
    main()
