#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2019, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_vm_storage_policy_info
short_description: Gather information about vSphere storage profile defined storage policy information.
description:
- Returns basic information on vSphere storage profiles.
- A vSphere storage profile defines storage policy information that describes storage requirements
  for virtual machines and storage capabilities of storage providers.
version_added: '2.9'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Get SPBM info
  vmware_vm_storage_policy_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
  delegate_to: localhost
  register: profiles
'''

RETURN = r'''
spbm_profiles:
  description: list of dictionary of SPBM info
  returned: success
  type: list
  sample: [
        {
            "constraints_sub_profiles": [
                {
                    "rule_set_info": [
                        {
                            "id": "hostFailuresToTolerate",
                            "value": 1
                        },
                        {
                            "id": "stripeWidth",
                            "value": 1
                        },
                        {
                            "id": "forceProvisioning",
                            "value": false
                        },
                        {
                            "id": "proportionalCapacity",
                            "value": 0
                        },
                        {
                            "id": "cacheReservation",
                            "value": 0
                        }
                    ],
                    "rule_set_name": "VSAN sub-profile"
                }
            ],
            "description": "Storage policy used as default for vSAN datastores",
            "id": "aa6d5a82-1c88-45da-85d3-3d74b91a5bad",
            "name": "vSAN Default Storage Policy"
        },
    ]
'''

try:
    from pyVmomi import pbm
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware_spbm import SPBM
from ansible.module_utils.vmware import vmware_argument_spec


class SPBMClient(SPBM):
    def __init__(self, module):
        super(SPBMClient, self).__init__(module)

    def show_capabilities(self, capabilities):
        """
        Return property instance for given capabilities
        """
        capabilities_info = []
        for capability in capabilities:
            for constraint in capability.constraint:
                if hasattr(constraint, 'propertyInstance'):
                    for propertyInstance in constraint.propertyInstance:
                        capabilities_info.append(
                            {
                                'id': propertyInstance.id,
                                'value': propertyInstance.value
                            }
                        )
        return capabilities_info

    def get_storage_policy_info(self):
        self.get_spbm_connection()

        results = dict(changed=False, spbm_profiles=[])
        profile_manager = self.spbm_content.profileManager
        profile_ids = profile_manager.PbmQueryProfile(
            resourceType=pbm.profile.ResourceType(resourceType="STORAGE"),
            profileCategory="REQUIREMENT"
        )
        profiles = []
        if profile_ids:
            profiles = profile_manager.PbmRetrieveContent(profileIds=profile_ids)

        for profile in profiles:
            temp_profile_info = {
                'name': profile.name,
                'id': profile.profileId.uniqueId,
                'description': profile.description,
                'constraints_sub_profiles': []
            }
            if hasattr(profile.constraints, 'subProfiles'):
                subprofiles = profile.constraints.subProfiles
                temp_sub_profiles = []
                for subprofile in subprofiles:
                    temp_sub_profiles.append({
                        'rule_set_name': subprofile.name,
                        'rule_set_info': self.show_capabilities(subprofile.capability),
                    })
                temp_profile_info['constraints_sub_profiles'] = temp_sub_profiles

            results['spbm_profiles'].append(temp_profile_info)

        self.module.exit_json(**results)


def main():
    argument_spec = vmware_argument_spec()

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    spbm_client = SPBMClient(module)
    spbm_client.get_storage_policy_info()


if __name__ == '__main__':
    main()
