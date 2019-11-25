#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: asa_ogcontent
version_added: "2.10"
author:
    - "Federico Olivieri (@Federico87)"
short_description: Find object-group' s contet.
description:
    - Find object-group' s contet including content of parent and child nested object-groups on Cisco ASA device.
options:
    name:
        description:
            - Name of the object-group.
        required: true
        type: str
"""

EXAMPLES = """
---
- name: find object-group's content.
  asa_ogcontent:
    name: aws_all_critical_vpcs
"""

RETURN = """
commands:
  description: return output
  returned: always
  type: list
  sample: [
    "Parent object-group: aws_all_critical_vpcs",
     "group-object aws_critical_west",
        "group-object aws_critical_west_ngnix",
          "network-object 10.0.160.0 255.255.248.0",
        "group-object aws_critical_west_sql",
          "network-object 10.0.168.0 255.255.248.0",
     "group-object aws_critical_est",
        "group-object aws_critical_est_apache",
          "network-object 10.0.192.0 255.255.248.0",
        "group-object aws_critical_est_postgres",
          "network-object 10.0.200.0 255.255.248.0"
  ]
"""
from collections import defaultdict

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.asa.asa import check_args
from ansible.module_utils.network.asa.asa import get_config


def find_obj_lines(module):
    obj_list = list()
    obj_dict = defaultdict(list)
    sh_all_ogs = get_config(module, flags=['object-group'])

    for count, value in enumerate(sh_all_ogs.splitlines()):
        if 'object-group network' in value:
            obj_dict_key = value.split()[-1]
            obj_dict[obj_dict_key] = list()
            obj_list.append(obj_dict)
            index = count + 1

            for line in sh_all_ogs.splitlines()[index:]:
                if 'description' in line:
                    pass
                elif 'object-group' not in line:
                    obj_dict[obj_dict_key].append(line)
                elif 'object-group' in line:
                    break

    return obj_list


def expand_nested_object_group(module, obj_list):
    my_obj = module.params['name']
    exp_og_list = list()

    expanded_og_list = recurse_object_groups(exp_og_list, obj_list, my_obj)
    expanded_og_list.insert(0, 'Parent object-group: ' + my_obj)

    return expanded_og_list


def recurse_object_groups(exp_og_list, obj_list, my_obj):
    blank_og_list = list()
    my_obj_id = obj_list[0].get(my_obj)

    if my_obj_id:
        for value in my_obj_id:
            exp_og_list.append(value)

            if 'group-object' in value:
                my_netsed_obj = obj_list[0].get(value.split()[1])

                for i in my_netsed_obj:
                    exp_og_list.append('  ' + i)
                    nested_obj = obj_list[0].get(i.split()[1])

                    if nested_obj:
                        for nested in obj_list[0].get(i.split()[1]):
                            exp_og_list.append('    ' + nested)

                        expand_og = recurse_object_groups(blank_og_list, obj_list, i)
                        if expand_og:
                            exp_og_list.extend(expand_og)
            else:
                continue

    return exp_og_list


def main():

    argument_spec = dict(name=dict(required=True))

    module = AnsibleModule(argument_spec=argument_spec)
    result = {'changed': False}

    obj_lines = find_obj_lines(module)
    my_nested_obj = expand_nested_object_group(module, obj_lines)
    result['commands'] = my_nested_obj

    if my_nested_obj:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
