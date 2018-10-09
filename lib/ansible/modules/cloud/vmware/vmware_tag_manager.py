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
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
- vSphere Automation SDK
- vCloud Suite SDK
options:
    tag_names:
      description:
      - List of tag(s) to be manage.
      required: True
    action:
      description:
      - C(add) will add the tags to the existing tag list of the given object.
      - C(remove) will remove the tags from the existing tag list of the given object.
      - C(set) will replace the tags of the given objects with user defined list of tags.
      default: add
      choices: [ add, remove, set ]
    object_type:
      description:
      - Type of object to work with.
      required: True
      choices: [ VirtualMachine ]
    object_name:
      description:
      - Name of the object to work with.
      required: True
extends_documentation_fragment: vmware_rest_client.documentation
'''

EXAMPLES = r'''
- name: Assign a tag to a virtual machine
  vmware_tag_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    tag_names:
      - Sample_Tag_0002
    object_name: Fedora_VM
    object_type: VirtualMachine
    state: add
  delegate_to: localhost

- name: Remove a tag to a virtual machine
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
from ansible.module_utils.vmware import PyVmomi
try:
    from com.vmware.vapi.std_client import DynamicID
    from com.vmware.cis.tagging_client import Tag, TagAssociation
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

        if self.object_type == 'VirtualMachine':
            self.managed_object = self.pyv.get_vm_or_template(self.object_name)
            self.dynamic_managed_object = DynamicID(type=self.object_type, id=self.managed_object._moId)

        if self.managed_object is None:
            self.module.fail_json(msg="Failed to find the managed object for %s with type %s" % (self.object_name, self.object_type))

        self.tag_service = Tag(self.connect)
        self.tag_association_svc = TagAssociation(self.connect)

        self.tag_names = self.params.get('tag_names')

    def get_tags_for_object(self, dobj):
        """
        Return tags associated with an object
        Args:
            dobj: Dynamic object

        Returns: List of tags associated with the given object

        """
        tag_ids = self.tag_association_svc.list_attached_tags(dobj)
        tags = []
        for tag_id in tag_ids:
            tags.append(self.tag_service.get(tag_id))
        return tags

    def ensure_state(self):
        """
        Manage the internal state of tags

        """
        results = dict(
            changed=False,
            tag_status=dict(),
        )
        changed = False
        action = self.params.get('action')
        available_tag_obj = self.get_tags_for_object(self.dynamic_managed_object)
        # Already existing tags from given object
        avail_tag_obj_name_list = [tag.name for tag in available_tag_obj]
        results['tag_status']['previous_tags'] = avail_tag_obj_name_list
        results['tag_status']['desired_tags'] = self.tag_names
        if action == 'add':
            changed = set(self.tag_names) - set(avail_tag_obj_name_list)
            if changed:
                for tag_to_add in changed:
                    tag_obj = self.search_svc_object_byname(self.tag_service, tag_to_add)
                    if tag_obj:
                        self.tag_association_svc.attach(tag_id=tag_obj.id, object_id=self.dynamic_managed_object)
                    else:
                        self.module.fail_json(msg="Unable to find tag object for tag %s" % tag_to_add)
        elif action == 'set':
            # Remove all tags first
            for av_tag in available_tag_obj:
                self.tag_association_svc.detach(tag_id=av_tag.id, object_id=self.dynamic_managed_object)

            # Add new tags
            for user_tag in self.tag_names:
                tag_obj = self.search_svc_object_byname(self.tag_service, user_tag)
                if tag_obj:
                    self.tag_association_svc.attach(tag_id=tag_obj.id, object_id=self.dynamic_managed_object)
                    changed = True
                else:
                    self.module.fail_json(msg="Unable to find tag object for tag %s" % user_tag)
        elif action == 'remove':
            # Remove all tags
            for user_tag in self.tag_names:
                if user_tag not in avail_tag_obj_name_list:
                    changed = False
                    continue
                tag_obj = self.search_svc_object_byname(self.tag_service, user_tag)
                if tag_obj:
                    self.tag_association_svc.detach(tag_id=tag_obj.id, object_id=self.dynamic_managed_object)
                    changed = True
                else:
                    self.module.fail_json(msg="Unable to find tag object for tag %s" % user_tag)

        results['tag_status']['current_tags'] = [tag.name for tag in self.get_tags_for_object(self.dynamic_managed_object)]
        results['changed'] = changed

        self.module.exit_json(**results)


def main():
    argument_spec = VmwareRestClient.vmware_client_argument_spec()
    argument_spec.update(
        tag_names=dict(type='list', required=True),
        action=dict(type='str', choices=['add', 'set', 'remove'], default='add'),
        object_name=dict(type='str', required=True),
        object_type=dict(type='str', required=True, choices=['VirtualMachine']),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    vmware_tag_manager = VmwareTagManager(module)
    vmware_tag_manager.ensure_state()


if __name__ == '__main__':
    main()
