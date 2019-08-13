#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 VMware, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_vcenter_permission
short_description: manages permissions on vCenter
description:
    - creates, updates or deletes permissions on vCenter objects
version_added: "2.9"
author: Christian Neugum (@digifuchsi)
options:
    entity:
        description:
            - describes vCenter object to apply permission on
        required: true
        type: dict
        options:
            name:
                description:
                    - name of object
                required: true
                type: str
            folder:
                description:
                    - folder of object
                required: true
                type: str
            type:
                description:
                    - type of object
                required: true
                type: str
                choices: ['vCenter', 'Datacenter', 'Cluster', 'ResourcePool',
                          'Host', 'Folder', 'DistributedSwitch',
                          'DistributedPortgroup', 'NsxtNetwork']
    principal:
        description:
            - describes user to set permission to
        required: true
        type: dict
        options:
            name:
                description:
                    - name of user
                required: true
                type: str
            domain:
                description:
                    - domain of user
                required: true
                type: str
            isGroup:
                description:
                    - indicates if user is a group
                default: false
                type: bool
    role_name:
        description:
            - Name of the role to assign
            - required if state is present
        required: false
        type: str
    propagate:
        description:
            - set to true if permisison should be propagated to children
        required: false
        type: bool
        default: false
    state:
        description:
            - set to present to add/update permisisons, absent to delete them
        required: false
        type: str
        choices: ['present', 'absent']
        default: 'present'
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: add or update permission on datacenter DC
  vmware_vcenter_permission:
    hostname: "{{ vCenter_hostname }}"
    username: "{{ vCenter_username }}"
    password: "{{ vCenter_password }}"
    validate_certs: False
    role_name: 'VM-Power'
    entity:
          name: 'DC'
          type: 'Datacenter'
    principal:
          name: 'test'
          domain: 'vsphere.local'
          isGroup: False
    propagate: True
    state: present

- name: remove permission from datacenter DC
  vmware_vcenter_permission:
    hostname: "{{ vCenter_hostname }}"
    username: "{{ vCenter_username }}"
    password: "{{ vCenter_password }}"
    validate_certs: False
    role_name: 'VM-Power'
    entity:
          name: 'DC'
          type: 'Datacenter'
    principal:
          name: 'test'
          domain: 'vsphere.local'
          isGroup: False
    propagate: True
    state: absent
'''

RETURN = '''

'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (HAS_PYVMOMI,
                                         connect_to_api,
                                         vmware_argument_spec,
                                         find_object_by_name
                                         )

class VmwareVcenterPermission(object):

    def __init__(self, module):
        self.module = module
        self.state = self.module.params['state']

        self.content = connect_to_api(module)
        self.authMgr = self.content.authorizationManager

        if self.state == 'present':
            self.role_name = self.module.params['role_name']
            self.role      = self.get_role(self.role_name)
        else:
            self.role_name = None
            self.role      = None

        self.propagate = self.module.params['propagate']

        self.entity = self.get_entity(self.module.params['entity'])
        self.principal = self.module.params['principal']

    def process_state(self):
        """map current vs desired state and change accordingly"""
        try:
            role_states = {
                'absent': {
                    'present': self.state_delete_permission,
                    'absent': self.state_exit_unchanged,
                },
                'present': {
                    'update': self.state_update_permission,
                    'present': self.state_exit_unchanged,
                    'absent': self.state_set_permission,
                }
            }
            role_states[self.state][self.check_permission()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def check_permission(self):
        """checks if desired state matches actual state"""
        perms = self.authMgr.RetrieveEntityPermissions(self.entity, False)
        for perm in perms:
            # check for a permission assigned to the principal
            if perm.principal == self.principal['domain'].upper() + '\\' + self.principal['name'] and \
               perm.group == self.principal['isGroup']:
                # if role is not defined desired state is absent
                if self.role is None:
                    # return present if no desired role is defined
                    return 'present'

                # check if role and propagate attribute matches
                if perm.roleId == self.role.roleId and perm.propagate == self.propagate:
                    # return present if permisison is matching user, role and propagate attribute
                    return 'present'
                else:
                    # return present if permisison is matching user but not role and/or propagate attribute
                    return 'update'
                break

        # return absent when no permisison is found for the principal on vCenter object
        return 'absent'

    def get_role(self, role_name):
        """finds role based on its name and returns vCenter role object"""
        for role in self.authMgr.roleList:
            if role.name == role_name:
                return role
        module.fail_json(msg='Role ' + role_name + ' could not be found')

    def get_entity(self, entity):
        """finds vCenter entity and returns vCenter managedEntity"""
        if entity['type'] == 'vCenter':
            return self.content.rootFolder

        out = None
        out = find_object_by_name(content=self.content,
                                  name=entity['name'],
                                  obj_type=[self.translate_objectType(entity['type'])],
                                  folder=entity['folder']
                                 )
        if out == None:
            self.module.fail_json(msg='Object ' + entity['name'] + ' of type ' + entity['type'] + ' could not be found')

        return out

    def translate_objectType(self, type):
        """translates given entity.type to a vim-object type"""
        # you may extend this list (and entity argument spec) to be able to manage more objects
        objectTypes = {
            'Datacenter': vim.Datacenter,
            'Cluster': vim.ClusterComputeResource,
            'ResourcePool': vim.ResourcePool,
            'Host': vim.HostSystem,
            'Folder': vim.Folder,
            'DistributedSwitch': vim.DistributedVirtualSwitch,
            'DistributedPortgroup': vim.dvs.DistributedVirtualPortgroup,
            'NsxtNetwork': vim.OpaqueNetwork
        }

        return objectTypes.get(type)

    def setOrUpdatePermission(self):
        """sets or updates a permission"""
        # build permission object
        perm = vim.AuthorizationManager.Permission()
        perm.entity = self.entity
        perm.group = self.principal['isGroup']
        perm.principal = self.principal['domain'].upper() + '\\' + self.principal['name']
        perm.propagate = self.propagate
        perm.roleId = self.role.roleId

        try:
            self.authMgr.SetEntityPermissions(self.entity, [perm])
        except vim.fault.UserNotFound as noUser_fault:
            self.module.fail_json(msg=noUser_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def state_set_permission(self):
        """handler to move from absent to present state"""
        if self.module.check_mode:
            self.module.exit_json(changed=True,result='CHECKMODE: permission would have been set')

        self.setOrUpdatePermission()

        self.module.exit_json(changed=True,result='permission set')

    def state_update_permission(self):
        """handler to move from update to present state"""
        if self.module.check_mode:
            self.module.exit_json(changed=True,result='CHECKMODE: permission would have been updated')

        self.setOrUpdatePermission()

        self.module.exit_json(changed=True,result='permission updated')

    def state_delete_permission(self):
        """handler to move from present to absent state"""
        if self.module.check_mode:
            self.module.exit_json(changed=True,result='CHECKMODE: permission would have been removed')

        try:
            self.authMgr.RemoveEntityPermission(self.entity, self.principal['domain'].upper() + '\\' + self.principal['name'], self.principal['isGroup'])
        except Exception as e:
            self.module.fail_json(msg=str(e))

        self.module.exit_json(changed=True,result='permission removed')


    def state_exit_unchanged(self):
        """handler to keep current state"""
        self.module.exit_json(changed=False)

def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        entity    = dict(type     = 'dict',
                         required = True,
                         options  = dict(
                             name   = dict(type='str',
                                           required=True),
                             folder = dict(type='str',
                                           required=False),
                             type   = dict(type='str',
                                           required=True,
                                           choices=[
                                              'vCenter',
                                              'Datacenter',
                                              'Cluster',
                                              'ResourcePool',
                                              'Host',
                                              'Folder',
                                              'DistributedSwitch',
                                              'DistributedPortgroup',
                                              'NsxtNetwork'
                                          ])
                        )),
        principal = dict(type     = 'dict',
                         required = True,
                         options  = dict(
                             name    = dict(type='str',
                                            required=True),
                             domain  = dict(type='str',
                                            required=True),
                             isGroup = dict(type='bool',
                                            default=False)
                        )),
        role_name = dict(type     = 'str',
                         required = False),
        propagate = dict(type    = 'bool',
                         default = False),
        state     = dict(type     = 'str',
                         default  = 'present',
                         choices  = ['present', 'absent']),
    ))

    required_if= [
      ['state', 'present', ['role_name']]
    ]

    module = AnsibleModule(
        argument_spec       = argument_spec,
        required_if         = required_if,
        supports_check_mode = True
    )

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vmware_vcenter_permission = VmwareVcenterPermission(module)
    vmware_vcenter_permission.process_state()

if __name__ == '__main__':
    main()
