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
module: ucs_disk_group_policy
short_description: Configures disk group policies on Cisco UCS Manager
description:
- Configures disk group policies on Cisco UCS Manager.
- Examples can be used with the L(UCS Platform Emulator,https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - Desired state of the disk group policy.
    - If C(present), will verify that the disk group policy is present and will create if needed.
    - If C(absent), will verify that the disk group policy is absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - The name of the disk group policy.
      This name can be between 1 and 16 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after the policy is created.
    required: yes
  description:
    description:
    - The user-defined description of the storage profile.
      Enter up to 256 characters.
      "You can use any characters or spaces except the following:"
      "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
    aliases: [ descr ]
  raid_level:
    description:
    - "The RAID level for the disk group policy. This can be one of the following:"
    - "stripe - UCS Manager shows RAID 0 Striped"
    - "mirror - RAID 1 Mirrored"
    - "mirror-stripe - RAID 10 Mirrored and Striped"
    - "stripe-parity - RAID 5 Striped Parity"
    - "stripe-dual-parity - RAID 6 Striped Dual Parity"
    - "stripe-parity-stripe - RAID 50 Striped Parity and Striped"
    - "stripe-dual-parity-stripe - RAID 60 Striped Dual Parity and Striped"
    choices: [stripe, mirror, mirror-stripe, stripe-parity, stripe-dual-parity, stripe-parity-stripe, stripe-dual-parity-stripe]
    default: stripe
  configuration_mode:
    description:
    - "Disk group configuration mode. Choose one of the following:"
    - "automatic - Automatically configures the disks in the disk group."
    - "manual - Enables you to manually configure the disks in the disk group."
    choices: [automatic, manual]
    default: automatic
  num_drives:
    description:
    - Specify the number of drives for the disk group.
    - This can be from 0 to 24.
    - Option only applies when configuration mode is automatic.
    default: 1
  drive_type:
    description:
    - Specify the drive type to use in the drive group.
    - "This can be one of the following:"
    - "unspecified — Selects the first available drive type, and applies that to all drives in the group."
    - "HDD — Hard disk drive"
    - "SSD — Solid state drive"
    - Option only applies when configuration mode is automatic.
    choices: [unspecified, HDD, SSD]
    default: unspecified
  num_ded_hot_spares:
    description:
    - Specify the number of hot spares for the disk group.
    - This can be from 0 to 24.
    - Option only applies when configuration mode is automatic.
    default: unspecified
  num_glob_hot_spares:
    description:
    - Specify the number of global hot spares for the disk group.
    - This can be from 0 to 24.
    - Option only applies when configuration mode is automatic.
    default: unspecified
  min_drive_size:
    description:
    - Specify the minimum drive size or unspecified to allow all drive sizes.
    - This can be from 0 to 10240 GB.
    - Option only applies when configuration mode is automatic.
    default: 'unspecified'
  use_remaining_disks:
    description:
    - Specifies whether you can use all the remaining disks in the disk group or not.
    - Option only applies when configuration mode is automatic.
    choices: ['yes', 'no']
    default: 'no'
  manual_disks:
    description:
    - List of manually configured disks.
    - Options are only used when you choose manual configuration_mode.
    suboptions:
      name:
        description:
        - The name of the local LUN.
        required: yes
      slot_num:
        description:
        - The slot number of the specific disk.
      role:
        description:
        - "The role of the disk. This can be one of the following:"
        - "normal - Normal"
        - "ded-hot-spare - Dedicated Hot Spare"
        - "glob-hot-spare - Glob Hot Spare"
      span_id:
        description:
        - The Span ID of the specific disk.
        default: 'unspecified'
      state:
        description:
        - If C(present), will verify disk slot is configured within policy.
          If C(absent), will verify disk slot is absent from policy.
        choices: [ present, absent ]
        default: present
  virtual_drive:
    description:
    - Configuration of virtual drive options.
    suboptions:
      access_policy:
        description:
        - Configure access policy to virtual drive.
        choices: [blocked, hidden, platform-default, read-only, read-write, transport-ready]
        default: platform-default
      drive_cache:
        description:
        - Configure drive caching.
        choices: [disable, enable, no-change, platform-default]
        default: platform-default
      io_policy:
        description:
        - Direct or Cached IO path.
        choices: [cached, direct, platform-default]
        default: platform-default
      read_policy:
        description:
        - Read access policy to virtual drive.
        choices: [normal, platform-default, read-ahead]
        default: platform-default
      strip_size:
        description:
        - Virtual drive strip size.
        choices: [ present, absent ]
        default: platform-default
      write_cache_policy:
        description:
        - Write back cache policy.
        choices: [always-write-back, platform-default, write-back-good-bbu, write-through]
        default: platform-default
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
- Brett Johnson (@sdbrett)
version_added: '2.8'
'''

EXAMPLES = r'''
- name: Configure Disk Group Policy
  ucs_disk_group_policy:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: DEE-DG
    raid_level: mirror
    configuration_mode: manual
    manual_disks:
    - slot_num: '1'
      role: normal
    - slot_num: '2'
      role: normal

- name: Remove Disk Group Policy
  ucs_disk_group_policy:
    name: DEE-DG
    hostname: 172.16.143.150
    username: admin
    password: password
    state: absent

- name: Remove Disk from Policy
  ucs_disk_group_policy:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: DEE-DG
    description: Testing Ansible
    raid_level: stripe
    configuration_mode: manual
    manual_disks:
    - slot_num: '1'
      role: normal
    - slot_num: '2'
      role: normal
      state: absent
    virtual_drive:
      access_policy: platform-default
      io_policy: direct
      strip_size: 64KB
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def configure_disk_policy(ucs, module, dn):
    from ucsmsdk.mometa.lstorage.LstorageDiskGroupConfigPolicy import LstorageDiskGroupConfigPolicy
    from ucsmsdk.mometa.lstorage.LstorageDiskGroupQualifier import LstorageDiskGroupQualifier
    from ucsmsdk.mometa.lstorage.LstorageLocalDiskConfigRef import LstorageLocalDiskConfigRef

    if not module.check_mode:
        try:
            # create if mo does not already exist
            mo = LstorageDiskGroupConfigPolicy(
                parent_mo_or_dn=module.params['org_dn'],
                name=module.params['name'],
                descr=module.params['description'],
                raid_level=module.params['raid_level'],
            )
            if module.params['configuration_mode'] == 'automatic':
                LstorageDiskGroupQualifier(
                    parent_mo_or_dn=mo,
                    num_drives=module.params['num_drives'],
                    drive_type=module.params['drive_type'],
                    use_remaining_disks=module.params['use_remaining_disks'],
                    num_ded_hot_spares=module.params['num_ded_hot_spares'],
                    num_glob_hot_spares=module.params['num_glob_hot_spares'],
                    min_drive_size=module.params['min_drive_size'],
                )
            else:  # configuration_mode == 'manual'
                for disk in module.params['manual_disks']:
                    if disk['state'] == 'absent':
                        child_dn = dn + '/slot-' + disk['slot_num']
                        mo_1 = ucs.login_handle.query_dn(child_dn)
                        if mo_1:
                            ucs.login_handle.remove_mo(mo_1)
                    else:  # state == 'present'
                        LstorageLocalDiskConfigRef(
                            parent_mo_or_dn=mo,
                            slot_num=disk['slot_num'],
                            role=disk['role'],
                            span_id=disk['span_id'],
                        )

            if module.params['virtual_drive']:
                _configure_virtual_drive(module, mo)

            ucs.login_handle.add_mo(mo, True)
            ucs.login_handle.commit()
        except Exception as e:  # generic Exception handling because SDK can throw a variety
            ucs.result['msg'] = "setup error: %s " % str(e)
            module.fail_json(**ucs.result)

    ucs.result['changed'] = True


def check_disk_policy_props(ucs, module, mo, dn):
    props_match = True

    # check top-level mo props
    kwargs = dict(descr=module.params['description'])
    kwargs['raid_level'] = module.params['raid_level']
    if mo.check_prop_match(**kwargs):
        # top-level props match, check next level mo/props
        if module.params['configuration_mode'] == 'automatic':
            child_dn = dn + '/disk-group-qual'
            mo_1 = ucs.login_handle.query_dn(child_dn)
            if mo_1:
                kwargs = dict(num_drives=module.params['num_drives'])
                kwargs['drive_type'] = module.params['drive_type']
                kwargs['use_remaining_disks'] = module.params['use_remaining_disks']
                kwargs['num_ded_hot_spares'] = module.params['num_ded_hot_spares']
                kwargs['num_glob_hot_spares'] = module.params['num_glob_hot_spares']
                kwargs['min_drive_size'] = module.params['min_drive_size']
                props_match = mo_1.check_prop_match(**kwargs)

        else:  # configuration_mode == 'manual'
            for disk in module.params['manual_disks']:
                child_dn = dn + '/slot-' + disk['slot_num']
                mo_1 = ucs.login_handle.query_dn(child_dn)
                if mo_1:
                    if disk['state'] == 'absent':
                        props_match = False
                    else:  # state == 'present'
                        kwargs = dict(slot_num=disk['slot_num'])
                        kwargs['role'] = disk['role']
                        kwargs['span_id'] = disk['span_id']
                        if not mo_1.check_prop_match(**kwargs):
                            props_match = False
                            break
        if props_match:
            if module.params['virtual_drive']:
                props_match = check_virtual_drive_props(ucs, module, dn)
    else:
        props_match = False
    return props_match


def check_virtual_drive_props(ucs, module, dn):
    child_dn = dn + '/virtual-drive-def'
    mo_1 = ucs.login_handle.query_dn(child_dn)
    return mo_1.check_prop_match(**module.params['virtual_drive'])


def _configure_virtual_drive(module, mo):
    from ucsmsdk.mometa.lstorage.LstorageVirtualDriveDef import LstorageVirtualDriveDef
    LstorageVirtualDriveDef(parent_mo_or_dn=mo, **module.params['virtual_drive'])


def _virtual_drive_argument_spec():
    return dict(
        access_policy=dict(type='str', default='platform-default',
                           choices=["blocked", "hidden", "platform-default", "read-only", "read-write",
                                    "transport-ready"]),
        drive_cache=dict(type='str', default='platform-default',
                         choices=["disable", "enable", "no-change", "platform-default"]),
        io_policy=dict(type='str', default='platform-default',
                       choices=["cached", "direct", "platform-default"]),
        read_policy=dict(type='str', default='platform-default',
                         choices=["normal", "platform-default", "read-ahead"]),
        strip_size=dict(type='str', default='platform-default',
                        choices=["1024KB", "128KB", "16KB", "256KB", "32KB", "512KB", "64KB", "8KB",
                                 "platform-default"]),
        write_cache_policy=dict(type='str', default='platform-default',
                                choices=["always-write-back", "platform-default", "write-back-good-bbu",
                                         "write-through"]),
    )


def main():
    manual_disk = dict(
        slot_num=dict(type='str', required=True),
        role=dict(type='str', default='normal', choices=['normal', 'ded-hot-spare', 'glob-hot-spare']),
        span_id=dict(type='str', default='unspecified'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    argument_spec = ucs_argument_spec
    argument_spec.update(
        org_dn=dict(type='str', default='org-root'),
        name=dict(type='str', required=True),
        description=dict(type='str', aliases=['descr'], default=''),
        raid_level=dict(
            type='str',
            default='stripe',
            choices=[
                'stripe',
                'mirror',
                'mirror-stripe',
                'stripe-parity',
                'stripe-dual-parity',
                'stripe-parity-stripe',
                'stripe-dual-parity-stripe',
            ],
        ),
        num_drives=dict(type='str', default='1'),
        configuration_mode=dict(type='str', default='automatic', choices=['automatic', 'manual']),
        num_ded_hot_spares=dict(type='str', default='unspecified'),
        num_glob_hot_spares=dict(type='str', default='unspecified'),
        drive_type=dict(type='str', default='unspecified', choices=['unspecified', 'HDD', 'SSD']),
        use_remaining_disks=dict(type='str', default='no', choices=['yes', 'no']),
        min_drive_size=dict(type='str', default='unspecified'),
        manual_disks=dict(type='list', elements='dict', options=manual_disk),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        virtual_drive=dict(type='dict', options=_virtual_drive_argument_spec()),
    )
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )
    ucs = UCSModule(module)
    # UCSModule creation above verifies ucsmsdk is present and exits on failure.
    # Additional imports are done below or in called functions.

    ucs.result['changed'] = False
    props_match = False
    # dn is <org_dn>/disk-group-config-<name>
    dn = module.params['org_dn'] + '/disk-group-config-' + module.params['name']

    mo = ucs.login_handle.query_dn(dn)
    if mo:
        if module.params['state'] == 'absent':
            # mo must exist but all properties do not have to match
            if not module.check_mode:
                ucs.login_handle.remove_mo(mo)
                ucs.login_handle.commit()
            ucs.result['changed'] = True
        else:  # state == 'present'
            props_match = check_disk_policy_props(ucs, module, mo, dn)

    if module.params['state'] == 'present' and not props_match:
        configure_disk_policy(ucs, module, dn)

    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()
