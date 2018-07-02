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
module: ucs_storage_profile
short_description: Configures storage profiles on Cisco UCS Manager
description:
- Configures storage profiles on Cisco UCS Manager.
- Examples can be used with the L(UCS Platform Emulator, https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify that the storage profile is present and will create if needed.
    - If C(absent), will verify that the storage profile is absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - The name of the storage profile.
    - This name can be between 1 and 16 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after profile is created.
    required: yes
  description:
    description:
    - The user-defined description of the storage profile.
    - Enter up to 256 characters.
    - "You can use any characters or spaces except the following:"
    - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
    aliases: [descr]
  local_luns:
    description:
    - List of Local LUNs used by the storage profile.
    - "Each list element has the following suboptions:"
    - "= name"
    - "  The name of the local LUN (required)."
    - "- size"
    - "  Size of this LUN in GB. The size can range from 1 to 10240 GB."
    - "- auto_deploy"
    - "  Whether the local LUN should be automatically deployed or not."
    - "  choices: [auto-deploy, no-auto-deploy]"
    - "  default: auto-deploy"
    - "- expand_to_avail"
    - "  Specifies that this LUN can be expanded to use the entire available disk group."
    - "  For each service profile, only one LUN can use this option."
    - "  Expand To Available option is not supported for already deployed LUN."
    - "  choices: ['yes', 'no']"
    - "  default: 'no'"
    - "- fractional_size"
    - "  Fractional size of this LUN in MB."
    - "- disk_policy_name"
    - "  The disk group configuration policy to be applied to this local LUN."
    - "- state"
    - "  If present, will verify local LUN is present on profile."
    - "  If absent, will verify local LUN is absent on profile."
    - "  choices: [present, absent]"
    - "  default: present"
  org_dn:
    description:
    - The distinguished name (dn) of the organization where the resource is assigned.
    default: org-root
requirements:
- ucsmsdk
author:
- Sindhu Sudhir (@sisudhir)
- David Soper (@dsoper2)
- CiscoUcs (@CiscoUcs)
version_added: '2.7'
'''

EXAMPLES = r'''
- name: Configure Storage Profile
  ucs_storage_profile:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: DEE-StgProf
    local_luns:
    - name: Boot-LUN
      size: '60'
      disk_policy_name: DEE-DG
    - name: Data-LUN
      size: '200'
      disk_policy_name: DEE-DG

- name: Remove Storage Profile
  ucs_storage_profile:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: DEE-StgProf
    state: absent

- name: Remove Local LUN from Storage Profile
  ucs_storage_profile:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: DEE-StgProf
    local_luns:
    - name: Data-LUN
      state: absent
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        org_dn=dict(type='str', default='org-root'),
        name=dict(type='str', required=True),
        description=dict(type='str', aliases=['descr'], default=''),
        local_luns=dict(type='list'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )
    ucs = UCSModule(module)

    err = False

    # UCSModule creation above verifies ucsmsdk is present and exits on failure.  Additional imports are done below.
    from ucsmsdk.mometa.lstorage.LstorageProfile import LstorageProfile
    from ucsmsdk.mometa.lstorage.LstorageDasScsiLun import LstorageDasScsiLun

    ucs.result['changed'] = False
    try:
        mo_exists = False
        props_match = False
        # dn is <org_dn>/profile-<name>
        dn = module.params['org_dn'] + '/profile-' + module.params['name']

        mo = ucs.login_handle.query_dn(dn)
        if mo:
            mo_exists = True

        if module.params['state'] == 'absent':
            # mo must exist but all properties do not have to match
            if mo_exists:
                if not module.check_mode:
                    ucs.login_handle.remove_mo(mo)
                    ucs.login_handle.commit()
                ucs.result['changed'] = True
        else:
            # set default params for lists which can't be done in the argument_spec
            if module.params.get('local_luns'):
                for lun in module.params['local_luns']:
                    if not lun.get('state'):
                        lun['state'] = 'present'
                    if not lun.get('size'):
                        lun['size'] = '1'
                    if not lun.get('auto_deploy'):
                        lun['auto_deploy'] = 'auto-deploy'
                    if not lun.get('expand_to_avail'):
                        lun['expand_to_avail'] = 'no'
                    if not lun.get('fractional_size'):
                        lun['fractional_size'] = '0'
            if mo_exists:
                # check top-level mo props
                kwargs = dict(descr=module.params['description'])
                if mo.check_prop_match(**kwargs):
                    # top-level props match, check next level mo/props
                    if not module.params.get('local_luns'):
                        props_match = True
                    else:
                        # check local lun props
                        for lun in module.params['local_luns']:
                            child_dn = dn + '/das-scsi-lun-' + lun['name']
                            mo_1 = ucs.login_handle.query_dn(child_dn)
                            if lun['state'] == 'absent':
                                if mo_1:
                                    props_match = False
                                    break
                            else:
                                if mo_1:
                                    kwargs = dict(size=str(lun['size']))
                                    kwargs['auto_deploy'] = lun['auto_deploy']
                                    kwargs['expand_to_avail'] = lun['expand_to_avail']
                                    kwargs['fractional_size'] = str(lun['fractional_size'])
                                    kwargs['local_disk_policy_name'] = lun['disk_policy_name']
                                    if mo_1.check_prop_match(**kwargs):
                                        props_match = True
                                else:
                                    props_match = False
                                    break

            if not props_match:
                if not module.check_mode:
                    # create if mo does not already exist
                    mo = LstorageProfile(
                        parent_mo_or_dn=module.params['org_dn'],
                        name=module.params['name'],
                        descr=module.params['description'],
                    )

                    if module.params.get('local_luns'):
                        for lun in module.params['local_luns']:
                            if lun['state'] == 'absent':
                                child_dn = dn + '/das-scsi-lun-' + lun['name']
                                mo_1 = ucs.login_handle.query_dn(child_dn)
                                ucs.login_handle.remove_mo(mo_1)
                            else:
                                mo_1 = LstorageDasScsiLun(
                                    parent_mo_or_dn=mo,
                                    name=lun['name'],
                                    size=str(lun['size']),
                                    auto_deploy=lun['auto_deploy'],
                                    expand_to_avail=lun['expand_to_avail'],
                                    fractional_size=str(lun['fractional_size']),
                                    local_disk_policy_name=lun['disk_policy_name'],
                                )

                    ucs.login_handle.add_mo(mo, True)
                    ucs.login_handle.commit()
                ucs.result['changed'] = True

    except Exception as e:
        err = True
        ucs.result['msg'] = "setup error: %s " % str(e)

    if err:
        module.fail_json(**ucs.result)
    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()
