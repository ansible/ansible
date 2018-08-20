#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
#
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
module: vmware_category
short_description: Manage VMware categories
description:
- This module can be used to create / delete / update VMware categories.
- Tag feature is introduced in vSphere 6 version, so this module is not supported in the earlier versions of vSphere.
- All variables and VMware object names are case sensitive.
version_added: '2.7'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
- vSphere Automation SDK
- vCloud Suite SDK
options:
    category_name:
      description:
      - The name of category to manage.
      required: True
    category_description:
      description:
      - The category description.
      - This is required only if C(state) is set to C(present).
      - This parameter is ignored, when C(state) is set to C(absent).
      default: ''
    category_cardinality:
      description:
      - The category cardinality.
      - This parameter is ignored, when updating existing category.
      choices: ['multiple', 'single']
      default: 'multiple'
    new_category_name:
      description:
      - The new name for an existing category.
      - This value is used while updating an existing category.
    state:
      description:
      - The state of category.
      - If set to C(present) and category does not exists, then category is created.
      - If set to C(present) and category exists, then category is updated.
      - If set to C(absent) and category exists, then category is deleted.
      - If set to C(absent) and category does not exists, no action is taken.
      - Process of updating category only allows name, description change.
      default: 'present'
      choices: [ 'present', 'absent' ]
extends_documentation_fragment: vmware_rest_client.documentation
'''

EXAMPLES = r'''
- name: Create a category
  vmware_category:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    category_name: Sample_Cat_0001
    category_description: Sample Description
    category_cardinality: 'multiple'
    state: present

- name: Rename category
  vmware_category:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    category_name: Sample_Category_0001
    new_category_name: Sample_Category_0002
    state: present

- name: Update category description
  vmware_category:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    category_name: Sample_Category_0001
    category_description: Some fancy description
    state: present

- name: Delete category
  vmware_category:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    category_name: Sample_Category_0002
    state: absent
'''

RETURN = r'''
category_results:
  description: dictionary of category metadata
  returned: on success
  type: dict
  sample: {
        "category_id": "urn:vmomi:InventoryServiceCategory:d7120bda-9fa5-4f92-9d71-aa1acff2e5a8:GLOBAL",
        "msg": "Category NewCat_0001 updated."
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware_rest_client import VmwareRestClient
try:
    from com.vmware.cis.tagging_client import Category, CategoryModel
except ImportError:
    pass


class VmwareCategory(VmwareRestClient):
    def __init__(self, module):
        super(VmwareCategory, self).__init__(module)
        self.category_service = Category(self.connect)
        self.global_categories = dict()
        self.category_name = self.params.get('category_name')
        self.get_all_categories()

    def ensure_state(self):
        """Manage internal states of categories. """
        desired_state = self.params.get('state')
        states = {
            'present': {
                'present': self.state_update_category,
                'absent': self.state_create_category,
            },
            'absent': {
                'present': self.state_delete_category,
                'absent': self.state_unchanged,
            }
        }
        states[desired_state][self.check_category_status()]()

    def state_create_category(self):
        """Create category."""
        category_spec = self.category_service.CreateSpec()
        category_spec.name = self.category_name
        category_spec.description = self.params.get('category_description')

        if self.params.get('category_cardinality') == 'single':
            category_spec.cardinality = CategoryModel.Cardinality.SINGLE
        else:
            category_spec.cardinality = CategoryModel.Cardinality.MULTIPLE

        category_spec.associable_types = set()

        category_id = self.category_service.create(category_spec)
        if category_id:
            self.module.exit_json(changed=True,
                                  category_results=dict(msg="Category '%s' created." % category_spec.name,
                                                        category_id=category_id))
        self.module.exit_json(changed=False,
                              category_results=dict(msg="No category created", category_id=''))

    def state_unchanged(self):
        """Return unchanged state."""
        self.module.exit_json(changed=False)

    def state_update_category(self):
        """Update category."""
        category_id = self.global_categories[self.category_name]['category_id']
        changed = False
        results = dict(msg="Category %s is unchanged." % self.category_name,
                       category_id=category_id)

        category_update_spec = self.category_service.UpdateSpec()
        change_list = []
        old_cat_desc = self.global_categories[self.category_name]['category_description']
        new_cat_desc = self.params.get('category_description')
        if new_cat_desc and new_cat_desc != old_cat_desc:
            category_update_spec.description = new_cat_desc
            results['msg'] = 'Category %s updated.' % self.category_name
            change_list.append(True)

        new_cat_name = self.params.get('new_category_name')
        if new_cat_name in self.global_categories:
            self.module.fail_json(msg="Unable to rename %s as %s already"
                                      " exists in configuration." % (self.category_name, new_cat_name))
        old_cat_name = self.global_categories[self.category_name]['category_name']

        if new_cat_name and new_cat_name != old_cat_name:
            category_update_spec.name = new_cat_name
            results['msg'] = 'Category %s updated.' % self.category_name
            change_list.append(True)

        if any(change_list):
            self.category_service.update(category_id, category_update_spec)
            changed = True

        self.module.exit_json(changed=changed,
                              category_results=results)

    def state_delete_category(self):
        """Delete category."""
        category_id = self.global_categories[self.category_name]['category_id']
        self.category_service.delete(category_id=category_id)
        self.module.exit_json(changed=True,
                              category_results=dict(msg="Category '%s' deleted." % self.category_name,
                                                    category_id=category_id))

    def check_category_status(self):
        """
        Check if category exists or not
        Returns: 'present' if category found, else 'absent'

        """
        if self.category_name in self.global_categories:
            return 'present'
        else:
            return 'absent'

    def get_all_categories(self):
        """Retrieve all category information."""
        for category in self.category_service.list():
            category_obj = self.category_service.get(category)
            self.global_categories[category_obj.name] = dict(
                category_description=category_obj.description,
                category_used_by=category_obj.used_by,
                category_cardinality=str(category_obj.cardinality),
                category_associable_types=category_obj.associable_types,
                category_id=category_obj.id,
                category_name=category_obj.name,
            )


def main():
    argument_spec = VmwareRestClient.vmware_client_argument_spec()
    argument_spec.update(
        category_name=dict(type='str', required=True),
        category_description=dict(type='str', default='', required=False),
        category_cardinality=dict(type='str', choices=["multiple", "single"], default="multiple"),
        new_category_name=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    vmware_category = VmwareCategory(module)
    vmware_category.ensure_state()


if __name__ == '__main__':
    main()
