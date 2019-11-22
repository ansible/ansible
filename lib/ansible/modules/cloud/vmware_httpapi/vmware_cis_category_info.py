#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Paul Knight <paul.knight@delaware.gov>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_cis_category_info
short_description: Gathers info about all, or a specified category.
description:
- This module can be used to gather information about a specific category.
- This module can also gather facts about all categories.
- This module is based on REST API and uses httpapi connection plugin for persistent connection.
version_added: '2.10'
author:
- Paul Knight (@n3pjk)
notes:
- Tested on vSphere 6.7
requirements:
- python >= 2.6
options:
  category_id:
    description:
    - The object id of the category.
    - Exclusive of category_name and used_by_*.
    required: false
    type: str
  category_name:
    description:
    - The name of the category.
    - Exclusive of category_id and used_by_*.
    required: false
    type: str
  used_by_id:
    description:
    - The id of the entity to list applied categories.
    - Exclusive of other used_by_* and category_*.
    type: str
  used_by_name:
    description:
    - The name of the entity to list applied categories, whose type is specified in used_by_type.
    - Exclusive of other used_by_id and category_*.
    type: str
  used_by_type:
    description:
    - The type of the entity to list applied categories, whose name is specified in used_by_name.
    - Exclusive of other used_by_id and category_*.
    choices: ['cluster', 'content_library', 'content_type', 'datacenter',
              'datastore', 'folder', 'host', 'local_library', 'network',
              'resource_pool', 'subscribed_library', 'tag', 'vm']
    type: str
extends_documentation_fragment: VmwareRestModule.documentation
'''

EXAMPLES = r'''
- name: Get all categories
  vmware_cis_category_info:
'''

RETURN = r'''
category:
    description: facts about the specified category
    returned: always
    type: dict
    sample: {
        "value": true
    }
'''

from ansible.module_utils.vmware_httpapi.VmwareRestModule import VmwareRestModule


def main():
    argument_spec = VmwareRestModule.create_argument_spec()
    argument_spec.update(
        category_name=dict(type='str', required=False),
        category_id=dict(type='str', required=False),
        used_by_name=dict(type='str', required=False),
        used_by_type=dict(
            type='str',
            required=False,
            choices=[
                'cluster',
                'content_library',
                'content_type',
                'datacenter',
                'datastore',
                'folder',
                'host',
                'local_library',
                'network',
                'resource_pool',
                'subscribed_library',
                'tag',
                'vm',
            ],
        ),
        used_by_id=dict(type='str', required=False),
    )

    required_together = [
        ['used_by_name', 'used_by_type']
    ]

    mutually_exclusive = [
        ['category_name', 'category_id', 'used_by_id', 'used_by_name'],
        ['category_name', 'category_id', 'used_by_id', 'used_by_type'],
    ]

    module = VmwareRestModule(argument_spec=argument_spec,
                              required_together=required_together,
                              mutually_exclusive=mutually_exclusive,
                              supports_check_mode=True)

    category_name = module.params['category_name']
    category_id = module.params['category_id']
    used_by_name = module.params['used_by_name']
    used_by_type = module.params['used_by_type']
    used_by_id = module.params['used_by_id']

    url = module.get_url('category')
    data = {}
    if category_name is not None:
        category_id = module.get_id('category', category_name)
    if category_id is not None:
        url += '/id:' + category_id
        module.get(url=url)
    else:
        if used_by_name is not None:
            used_by_id = module.get_id(used_by_type, used_by_name)
        url += '?~action=list-used-categories'
        data = {
            'used_by_entity': used_by_id
        }
        module.post(url=url, data=data)
    module.exit()


if __name__ == '__main__':
    main()
