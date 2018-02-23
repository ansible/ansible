#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-instance-attributes, broad-except
# Prasanna Nanda <pnanda@cloudsimple.com>

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""Manages Storage Profiles"""

from ansible.module_utils.vmware import vmware_argument_spec, connect_to_api, find_datastore_by_name
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.spbm_client import SPBMClient

try:
    from pyVmomi import vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_spbm
short_description: VMware Storage Profile Utilities
description:
    - Create, Destroy VM Storage Profiles
version_added: 2.6
author:
    - Prasanna Nanda <pnanda@cloudsimple.com>
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.7"
    - PyVmomi
options:
    profile_name:
        description:
            - Name of the storage profile to Create
        required: True
    state:
        description:
            - Valid values are present or absent
        required: True
    description:
        description:
            - Some Text Describing the Storage profile
        required: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
  - name: Create a Storage Profile
    vmware_spbm:
      hostname: A vCenter host
      username: vCenter username
      password: vCenter password
      profile_name: Name of the storage profile to create
      description: Text Describing Storage Profile
      state: present|absent
'''

class vmware_spbm(object):
    """VMware Storage Profile Methods"""
    def __init__(self, module):
        self.module = module
        self.name = module.params['profile_name']
        self.description = module.params['description']
        self.desiredstate = module.params['state']
        self.rules = module.params['rules']
        self.currentstate = 'absent'
        self.content = None
        try:
            service_instance, content = connect_to_api(module, return_service_instance=True)
            self.content = content
            self.spbmclient = SPBMClient(vc_si=service_instance, hostname=module.params['hostname'])
        except vmodl.RuntimeFault as runtime_fault:
            module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            module.fail_json(msg=method_fault.msg)
        except Exception as e:
            module.fail_json(msg=to_native(e))

    def force_provision(self):
        """Allow Force Provision on vsanDatastore"""
        datastore = find_datastore_by_name(self.content, "vsanDatastore")
        vsan_profile_id = self.spbmclient.get_ds_default_profile(datastore)
        rules = [{'forceProvisioning': True}]
        self.spbmclient.update_storage_profile(profile_id=vsan_profile_id, rules=rules)

    def process_state(self):
        """Process Current State of Profiles"""
        profiles = self.spbmclient.get_profiles()
        if not profiles:
            self.module.fail_json(changed=False, msg="Could not retrieve \
            Storage Profile Information from vCenter")
        else:
            for profile in profiles:
                if self.module.params['profile_name'] == profile.name:
                    self.currentstate = 'present'
        # Current State of System and Desired State are same
        if self.currentstate == self.desiredstate:
            self.module.exit_json(changed=False)

        # Profile is absent and you need to create one
        if self.currentstate == 'absent' and self.desiredstate == 'present':
            profileId = self.spbmclient.create_storage_profile(profile_name=self.name, \
            description=self.description, rules=self.rules)
            if profileId:
                self.module.exit_json(changed=True, msg="Created Storage Profile {} \
                and ID {}".format(self.name, profileId.uniqueId))
            else:
                self.module.fail_json(changed=False, msg="Failed to create \
                Storage Profile {}".format(self.name))

        # Profile is Present and you need to delete one
        if self.currentstate == 'present' and self.desiredstate == 'absent':
            results = self.spbmclient.delete_storage_profile(profile_name=self.name)
            if not results:
                self.module.exit_json(changed=True, \
                msg="Deleted Storage Profile {}".format(self.name))
            else:
                profile_op_outcome = results[0]
                if profile_op_outcome.fault is not None:
                    self.module.fail_json(changed=False, msg=str(profile_op_outcome.fault))


def main():
    """Manages VM Storage Profiles"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(profile_name=dict(required=True, type='str'), \
    description=dict(required=False, type='str', default='Sample Storage Profile'), \
    force_provision=dict(required=False, type='bool', default=False), \
    rules=dict(required=False, type='list', default=[{'stripeWidth': 1}, \
    {'hostFailuresToTolerate': 1}, {'replicaPreference':'RAID-5/6 (Erasure Coding) - Capacity'}]), \
    state=dict(default='present', choices=['present', 'absent'], type='str')))
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_PYVMOMI:
        module.fail_json(msg="pyvmomi is required for this module")
    spbm = vmware_spbm(module)
    if module.params['force_provision']:
        spbm.force_provision()
        module.exit_json(changed=True, msg="Allow Force Provision")
    else:
        spbm.process_state()

if __name__ == '__main__':
    main()
