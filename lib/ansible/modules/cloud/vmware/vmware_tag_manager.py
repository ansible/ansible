#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_tag_manager
short_description: Manage association of VMware tags with VMware objects
description:
- This module can be used to assign / remove VMware tags from the given VMware objects.
- Tag feature is introduced in vSphere 6 version, so this module is not supported in the earlier versions of vSphere.
- All variables and VMware object names are case sensitive.
version_added: 2.8
author:
- Abhijeet Kasurde (@Akasurde)
- Frederic Van Reet (@GBrawl)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
- vSphere Automation SDK
options:
    tag_names:
      description:
      - List of tag(s) to be managed.
      - You can also specify category name by specifying colon separated value. For example, "category_name:tag_name".
      - You can skip category name if you have unique tag names.
      required: True
      type: list
    state:
      description:
      - If C(state) is set to C(add) or C(present) will add the tags to the existing tag list of the given object.
      - If C(state) is set to C(remove) or C(absent) will remove the tags from the existing tag list of the given object.
      - If C(state) is set to C(set) will replace the tags of the given objects with the user defined list of tags.
      default: add
      choices: [ present, absent, add, remove, set ]
      type: str
    object_type:
      description:
      - Type of object to work with.
      required: True
      choices: [ VirtualMachine, Datacenter, ClusterComputeResource, HostSystem, DistributedVirtualSwitch, DistributedVirtualPortgroup ]
      type: str
    object_name:
      description:
      - Name of the object to work with.
      - For DistributedVirtualPortgroups the format should be "switch_name:portgroup_name"
      required: True
      type: str
extends_documentation_fragment: vmware_rest_client.documentation
'''

EXAMPLES = r'''
- name: Add tags to a virtual machine
  vmware_tag_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    tag_names:
      - Sample_Tag_0002
      - Category_0001:Sample_Tag_0003
    object_name: Fedora_VM
    object_type: VirtualMachine
    state: add
  delegate_to: localhost

- name: Remove a tag from a virtual machine
  vmware_tag_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    tag_names:
      - Sample_Tag_0002
    object_name: Fedora_VM
    object_type: VirtualMachine
    state: remove
  delegate_to: localhost

- name: Add tags to a distributed virtual switch
  vmware_tag_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    tag_names:
      - Sample_Tag_0003
    object_name: Switch_0001
    object_type: DistributedVirtualSwitch
    state: add
  delegate_to: localhost

- name: Add tags to a distributed virtual portgroup
  vmware_tag_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    tag_names:
      - Sample_Tag_0004
    object_name: Switch_0001:Portgroup_0001
    object_type: DistributedVirtualPortgroup
    state: add
  delegate_to: localhost
'''

RETURN = r'''
tag_status:
    description: metadata about tags related to object configuration
    returned: on success
    type: list
    sample: {
        "current_tags": [
            "backup",
            "security"
        ],
        "desired_tags": [
            "security"
        ],
        "previous_tags": [
            "backup",
            "security"
        ]
    }
'''
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware_rest_client import VmwareRestClient
from ansible.module_utils.vmware import (PyVmomi, find_dvs_by_name, find_dvspg_by_name)
try:
    from com.vmware.vapi.std_client import DynamicID
    from com.vmware.vapi.std.errors_client import Error
except ImportError:
    pass


class VmwareTagManager(VmwareRestClient):
    def __init__(self, module):
        """
        Constructor
        """
        super(VmwareTagManager, self).__init__(module)
        self.pyv = PyVmomi(module=module)

        self.object_type = self.params.get('object_type')
        self.object_name = self.params.get('object_name')
        self.managed_object = None

        if self.object_type == 'VirtualMachine':
            self.managed_object = self.pyv.get_vm_or_template(self.object_name)

        if self.object_type == 'Datacenter':
            self.managed_object = self.pyv.find_datacenter_by_name(self.object_name)

        if self.object_type == 'ClusterComputeResource':
            self.managed_object = self.pyv.find_cluster_by_name(self.object_name)

        if self.object_type == 'HostSystem':
            self.managed_object = self.pyv.find_hostsystem_by_name(self.object_name)

        if self.object_type == 'DistributedVirtualSwitch':
            self.managed_object = find_dvs_by_name(self.pyv.content, self.object_name)
            self.object_type = 'VmwareDistributedVirtualSwitch'

        if self.object_type == 'DistributedVirtualPortgroup':
            dvs_name, pg_name = self.object_name.split(":", 1)
            dv_switch = find_dvs_by_name(self.pyv.content, dvs_name)
            if dv_switch is None:
                self.module.fail_json(msg="A distributed virtual switch with name %s does not exist" % dvs_name)
            self.managed_object = find_dvspg_by_name(dv_switch, pg_name)

        if self.managed_object is None:
            self.module.fail_json(msg="Failed to find the managed object for %s with type %s" % (self.object_name, self.object_type))

        if not hasattr(self.managed_object, '_moId'):
            self.module.fail_json(msg="Unable to find managed object id for %s managed object" % self.object_name)

        self.dynamic_managed_object = DynamicID(type=self.object_type, id=self.managed_object._moId)

        self.tag_service = self.api_client.tagging.Tag
        self.category_service = self.api_client.tagging.Category
        self.tag_association_svc = self.api_client.tagging.TagAssociation

        self.tag_names = self.params.get('tag_names')

    def is_tag_category(self, cat_obj, tag_obj):
        for tag in self.tag_service.list_tags_for_category(cat_obj.id):
            if tag_obj.name == self.tag_service.get(tag).name:
                return True
        return False

    def ensure_state(self):
        """
        Manage the internal state of tags

        """
        results = dict(
            changed=False,
            tag_status=dict(),
        )
        changed = False
        action = self.params.get('state')
        available_tag_obj = self.get_tags_for_object(tag_service=self.tag_service,
                                                     tag_assoc_svc=self.tag_association_svc,
                                                     dobj=self.dynamic_managed_object)
        # Already existing tags from the given object
        avail_tag_obj_name_list = [tag.name for tag in available_tag_obj]
        results['tag_status']['previous_tags'] = avail_tag_obj_name_list
        results['tag_status']['desired_tags'] = self.tag_names

        # Check if category and tag combination exists as per user request
        removed_tags_for_set = False
        for tag in self.tag_names:
            category_obj, category_name, tag_name = None, None, None
            if ":" in tag:
                # User specified category
                category_name, tag_name = tag.split(":", 1)
                category_obj = self.search_svc_object_by_name(self.category_service, category_name)
                if not category_obj:
                    self.module.fail_json(msg="Unable to find the category %s" % category_name)
            else:
                # User specified only tag
                tag_name = tag

            tag_obj = self.search_svc_object_by_name(self.tag_service, tag_name)
            if not tag_obj:
                self.module.fail_json(msg="Unable to find the tag %s" % tag_name)

            if category_name and category_obj and not self.is_tag_category(category_obj, tag_obj):
                self.module.fail_json(msg="Category %s does not contain tag %s" % (category_name, tag_name))

            if action in ('add', 'present'):
                if tag_obj not in available_tag_obj:
                    # Tag is not already applied
                    try:
                        self.tag_association_svc.attach(tag_id=tag_obj.id, object_id=self.dynamic_managed_object)
                        changed = True
                    except Error as error:
                        self.module.fail_json(msg="%s" % self.get_error_message(error))

            elif action == 'set':
                # Remove all tags first
                try:
                    if not removed_tags_for_set:
                        for av_tag in available_tag_obj:
                            self.tag_association_svc.detach(tag_id=av_tag.id, object_id=self.dynamic_managed_object)
                        removed_tags_for_set = True
                    self.tag_association_svc.attach(tag_id=tag_obj.id, object_id=self.dynamic_managed_object)
                    changed = True
                except Error as error:
                    self.module.fail_json(msg="%s" % self.get_error_message(error))

            elif action in ('remove', 'absent'):
                if tag_obj in available_tag_obj:
                    try:
                        self.tag_association_svc.detach(tag_id=tag_obj.id, object_id=self.dynamic_managed_object)
                        changed = True
                    except Error as error:
                        self.module.fail_json(msg="%s" % self.get_error_message(error))

        results['tag_status']['current_tags'] = [tag.name for tag in self.get_tags_for_object(self.tag_service,
                                                                                              self.tag_association_svc,
                                                                                              self.dynamic_managed_object)]
        results['changed'] = changed
        self.module.exit_json(**results)


def main():
    argument_spec = VmwareRestClient.vmware_client_argument_spec()
    argument_spec.update(
        tag_names=dict(type='list', required=True),
        state=dict(type='str', choices=['absent', 'add', 'present', 'remove', 'set'], default='add'),
        object_name=dict(type='str', required=True),
        object_type=dict(type='str', required=True, choices=['VirtualMachine', 'Datacenter', 'ClusterComputeResource',
                                                             'HostSystem', 'DistributedVirtualSwitch',
                                                             'DistributedVirtualPortgroup']),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    vmware_tag_manager = VmwareTagManager(module)
    vmware_tag_manager.ensure_state()


if __name__ == '__main__':
    main()
