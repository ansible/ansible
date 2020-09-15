#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2019, Pavan Bidkar <pbidkar@vmware.com>
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
module: vmware_content_library_manager
short_description: Create, update and delete VMware content library
description:
- Module to manage VMware content Library
- Content Library feature is introduced in vSphere 6.0 version, so this module is not supported in the earlier versions of vSphere.
- All variables and VMware object names are case sensitive.
version_added: '2.9'
author:
- Pavan Bidkar (@pgbidkar)
notes:
- Tested on vSphere 6.5, 6.7
requirements:
- python >= 2.6
- PyVmomi
- vSphere Automation SDK
options:
    library_name:
      description:
      - The name of VMware content library to manage.
      type: str
      required: True
    library_description:
      description:
      - The content library description.
      - This is required only if C(state) is set to C(present).
      - This parameter is ignored, when C(state) is set to C(absent).
      - Process of updating content library only allows description change.
      type: str
      required: False
      default: ''
    library_type:
      description:
      - The content library type.
      - This is required only if C(state) is set to C(present).
      - This parameter is ignored, when C(state) is set to C(absent).
      type: str
      required: False
      default: 'local'
      choices: [ 'local', 'subscribed' ]
    datastore_name:
      description:
      - Name of the datastore on which backing content library is created.
      - This is required only if C(state) is set to C(present).
      - This parameter is ignored, when C(state) is set to C(absent).
      - Currently only datastore backing creation is supported.
      type: str
      required: False
      aliases: ['datastore']
    state:
      description:
      - The state of content library.
      - If set to C(present) and library does not exists, then content library is created.
      - If set to C(present) and library exists, then content library is updated.
      - If set to C(absent) and library exists, then content library is deleted.
      - If set to C(absent) and library does not exists, no action is taken.
      type: str
      required: False
      default: 'present'
      choices: [ 'present', 'absent' ]
extends_documentation_fragment: vmware_rest_client.documentation
'''

EXAMPLES = r'''
- name: Create Content Library
  vmware_content_library_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    library_name: test-content-lib
    library_description: 'Library with Datastore Backing'
    library_type: local
    datastore_name: datastore
    validate_certs: False
    state: present
  delegate_to: localhost

- name: Update Content Library
  vmware_content_library_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    library_name: test-content-lib
    library_description: 'Library with Datastore Backing'
    validate_certs: no
    state: present
  delegate_to: localhost

- name: Delete Content Library
  vmware_content_library_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    library_name: test-content-lib
    validate_certs: no
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
content_library_info:
  description: library creation success and library_id
  returned: on success
  type: dict
  sample: {
      "library_id": "d0b92fa9-7039-4f29-8e9c-0debfcb22b72",
      "library_description": 'Test description',
      "library_type": 'LOCAL',
      "msg": "Content Library 'demo-local-lib-4' created.",
    }
'''

import uuid
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware_rest_client import VmwareRestClient
from ansible.module_utils.vmware import PyVmomi

HAS_VAUTOMATION_PYTHON_SDK = False
try:
    from com.vmware.content_client import LibraryModel
    from com.vmware.content.library_client import StorageBacking
    HAS_VAUTOMATION_PYTHON_SDK = True
except ImportError:
    pass


class VmwareContentLibCreate(VmwareRestClient):
    def __init__(self, module):
        """Constructor."""
        super(VmwareContentLibCreate, self).__init__(module)
        self.content_service = self.api_client
        self.local_libraries = dict()
        self.library_name = self.params.get('library_name')
        self.library_description = self.params.get('library_description')
        self.library_type = self.params.get('library_type')
        self.library_types = dict()
        self.datastore_name = self.params.get('datastore_name')
        self.get_all_libraries()
        self.pyv = PyVmomi(module=module)

    def process_state(self):
        """
        Manage states of Content Library
        """
        self.desired_state = self.params.get('state')
        library_states = {
            'absent': {
                'present': self.state_destroy_library,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'present': self.state_update_library,
                'absent': self.state_create_library,
            }
        }
        library_states[self.desired_state][self.check_content_library_status()]()

    def get_all_libraries(self):
        content_libs = self.content_service.content.LocalLibrary.list()
        if content_libs:
            for content_lib in content_libs:
                lib_details = self.content_service.content.LocalLibrary.get(content_lib)
                self.local_libraries[lib_details.name] = dict(
                    lib_name=lib_details.name,
                    lib_description=lib_details.description,
                    lib_id=lib_details.id,
                    lib_type=lib_details.type
                )

    def check_content_library_status(self):
        """
        Check if Content Library exists or not
        Returns: 'present' if library found, else 'absent'

        """
        ret = 'present' if self.library_name in self.local_libraries else 'absent'
        return ret

    def state_create_library(self):
        # Find the datastore by the given datastore name
        datastore_id = self.pyv.find_datastore_by_name(datastore_name=self.datastore_name)
        if not datastore_id:
            self.module.fail_json(msg="Failed to find the datastore %s" % self.datastore_name)
        self.datastore_id = datastore_id._moId
        # Build the storage backing for the library to be created
        storage_backings = []
        storage_backing = StorageBacking(type=StorageBacking.Type.DATASTORE, datastore_id=self.datastore_id)
        storage_backings.append(storage_backing)

        # Build the specification for the library to be created
        create_spec = LibraryModel()
        create_spec.name = self.library_name
        create_spec.description = self.library_description
        self.library_types = {'local': create_spec.LibraryType.LOCAL,
                              'subscribed': create_spec.LibraryType.SUBSCRIBED}
        create_spec.type = self.library_types[self.library_type]
        create_spec.storage_backings = storage_backings

        # Create a local content library backed the VC datastore
        library_id = self.content_service.content.LocalLibrary.create(create_spec=create_spec,
                                                                      client_token=str(uuid.uuid4()))
        if library_id:
            self.module.exit_json(
                changed=True,
                content_library_info=dict(
                    msg="Content Library '%s' created." % create_spec.name,
                    library_id=library_id,
                    library_description=self.library_description,
                    library_type=create_spec.type,
                )
            )
        self.module.exit_json(changed=False,
                              content_library_info=dict(msg="Content Library not created. Datastore and library_type required", library_id=''))

    def state_update_library(self):
        """
        Update Content Library

        """
        changed = False
        library_id = self.local_libraries[self.library_name]['lib_id']
        content_library_info = dict(msg="Content Library %s is unchanged." % self.library_name, library_id=library_id)
        library_update_spec = LibraryModel()
        library_desc = self.local_libraries[self.library_name]['lib_description']
        desired_lib_desc = self.params.get('library_description')
        if library_desc != desired_lib_desc:
            library_update_spec.description = desired_lib_desc
            self.content_service.content.LocalLibrary.update(library_id, library_update_spec)
            content_library_info['msg'] = 'Content Library %s updated.' % self.library_name
            changed = True

        self.module.exit_json(changed=changed, content_library_info=content_library_info)

    def state_destroy_library(self):
        """
        Delete Content Library

        """
        library_id = self.local_libraries[self.library_name]['lib_id']
        self.content_service.content.LocalLibrary.delete(library_id=library_id)
        self.module.exit_json(
            changed=True,
            content_library_info=dict(
                msg="Content Library '%s' deleted." % self.library_name,
                library_id=library_id
            )
        )

    def state_exit_unchanged(self):
        """
        Return unchanged state

        """
        self.module.exit_json(changed=False)


def main():
    argument_spec = VmwareRestClient.vmware_client_argument_spec()
    argument_spec.update(
        library_name=dict(type='str', required=False),
        library_description=dict(type='str', required=False),
        library_type=dict(type='str', required=False, choices=['local', 'subscribed'], default='local'),
        datastore_name=dict(type='str', required=False, aliases=['datastore']),
        state=dict(type='str', choices=['present', 'absent'], default='present', required=False),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    vmware_contentlib_create = VmwareContentLibCreate(module)
    vmware_contentlib_create.process_state()


if __name__ == '__main__':
    main()
