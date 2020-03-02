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


def get_category_by_id(module, category_id):
    category_id_url = module.get_url('category') + '/id:' + category_id
    response = dict()
    response['status'], response['data'] = module._connection.send_request(category_id_url, {}, method='GET')
    if response['status'] == 200:
        return response['data']['value']
    return {}


def get_categories_used_by_id(module, used_by_id):
    results = []
    url = module.get_url('category') + '?~action=list-used-categories'
    data = {
        'used_by_entity': used_by_id
    }
    response = dict()
    response['status'], response['data'] = module._connection.send_request(url, data, method='POST')
    if response['status'] == 200:
        for cat_id in response['data']['value']:
            results.append(get_category_by_id(module, category_id=cat_id))
    module.exit_json(category=results)


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

    results = []

    url = module.get_url('category')
    response = dict()
    response['status'], response['data'] = module._connection.send_request(url, {}, method='GET')
    if response['status'] != 200:
        module.fail_json(msg="Failed to get information about categories")

    category_ids = response['data'].get('value', [])
    if category_id is not None:
        if category_id in category_ids:
            results.append(get_category_by_id(module, category_id=category_id))
        module.exit_json(category=results)
    elif category_name is not None:
        for cat_id in category_ids:
            category_obj = get_category_by_id(module, category_id=cat_id)
            if category_obj['name'] == category_name:
                results.append(category_obj)
        module.exit_json(category=results)
    elif used_by_name is not None:
        if used_by_type == 'tag':
            tag_url = module.get_url('tag')
            response = dict()
            response['status'], response['data'] = module._connection.send_request(tag_url, {}, method='GET')
            if response['status'] == 200:
                for tag_id in response['data']['value']:
                    tag_details_url = tag_url + '/id:' + tag_id
                    response = dict()
                    response['status'], response['data'] = module._connection.send_request(tag_details_url, {}, method='GET')
                    if response['status'] != 200:
                        continue
                    if response['data']['value']['name'] == used_by_name:
                        used_by_id = tag_id
                        break
                get_categories_used_by_id(module, used_by_id)
        else:
            used_by_id = module.get_id(used_by_type, used_by_name)
            get_categories_used_by_id(module, used_by_id)
    elif used_by_id is not None:
        get_categories_used_by_id(module, used_by_id)
    else:
        for cat_id in category_ids:
            results.append(get_category_by_id(module, category_id=cat_id))
        module.exit_json(category=results)


if __name__ == '__main__':
    main()
