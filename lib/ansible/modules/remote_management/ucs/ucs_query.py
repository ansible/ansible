#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ucs_query

short_description: Queries UCS Manager objects by class or distinguished name

description:
  -Queries UCS Manager objects by class or distinguished name.

extends_documentation_fragment: ucs

options:
    class_ids:
        description:
        - One or more UCS Manager Class IDs to query.
        - As a comma separated list
        type: str

    distinguished_names:
        description:
        - One or more UCS Manager Distinguished Names to query.
        - As a comma separated list
        type: str

    delegate_to:
        description:
        - Where the module will be run
        default: localhost
        type: str

requirements:
    - ucsmsdk

author:
    - John McDonough (@movinalot)
    - CiscoUcs (@CiscoUcs)
version_added: "2.10"
'''

EXAMPLES = r'''
- name: Query UCS Class ID
  ucs_query:
    hostname: "{{ ucs_hostname }}"
    username: "{{ ucs_username }}"
    password: "{{ ucs_password }}"
    class_ids: computeBlade
    delegate_to: localhost

- name: Query UCS Class IDs
  ucs_query:
    hostname: "{{ ucs_hostname }}"
    username: "{{ ucs_username }}"
    password: "{{ ucs_password }}"
    class_ids: computeBlade, fabricVlan
    delegate_to: localhost

- name: Query UCS Distinguished Name
  ucs_query:
    hostname: "{{ ucs_hostname }}"
    username: "{{ ucs_username }}"
    password: "{{ ucs_password }}"
    distinguished_names: org-root
    delegate_to: localhost

- name: Query UCS Distinguished Names
  ucs_query:
    hostname: "{{ ucs_hostname }}"
    username: "{{ ucs_username }}"
    password: "{{ ucs_password }}"
    distinguished_names: org-root, sys/rack-unit-1, sys/chassis-1/blade-2
    delegate_to: localhost
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def retrieve_class_id(class_id, ucs):
    return ucs.login_handle.query_classid(class_id)


def retrieve_distinguished_name(distinguished_name, ucs):
    return ucs.login_handle.query_dn(distinguished_name)


def make_mo_dict(ucs_mo):
    obj_dict = {}
    for mo_property in ucs_mo.prop_map.values():
        obj_dict[mo_property] = getattr(ucs_mo, mo_property)
    return obj_dict


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        class_ids=dict(type='str'),
        distinguished_names=dict(type='str'),
        delegate_to=dict(type='str', default='localhost'),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=False,
        mutually_exclusive=[
            ['class_ids', 'distinguished_names'],
        ],
    )

    # UCSModule verifies ucsmsdk is present and exits on failure.
    # Imports are below for UCS object creation.
    ucs = UCSModule(module)
    err = False
    query_result = {}

    try:
        if module.params['class_ids']:
            class_ids = [
                x.strip() for x in module.params['class_ids'].split(',')
            ]
            for class_id in class_ids:
                query_result[class_id] = []
                ucs_mos = retrieve_class_id(class_id, ucs)
                if ucs_mos:
                    for ucs_mo in ucs_mos:
                        query_result[class_id].append(make_mo_dict(ucs_mo))

            ucs.result['objects'] = query_result

        elif module.params['distinguished_names']:
            distinguished_names = [
                x.strip()
                for x in module.params['distinguished_names'].split(',')
            ]
            for distinguished_name in distinguished_names:
                query_result[distinguished_name] = {}
                ucs_mo = retrieve_distinguished_name(distinguished_name, ucs)

                if ucs_mo:
                    query_result[distinguished_name] = make_mo_dict(ucs_mo)

            ucs.result['objects'] = query_result

    except Exception as e:
        err = True
        ucs.result['msg'] = "setup error: %s " % str(e)

    if err:
        module.fail_json(**ucs.result)

    ucs.result['changed'] = False
    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()
