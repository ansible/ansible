#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Kairo Araujo <kairo@kairo.eti.br>
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
author: Kairo Araujo (@kairoaraujo)
module: mksysb
short_description: Generates AIX mksysb rootvg backups.
description:
  - This module manages a basic AIX mksysb (image) of rootvg.
version_added: "2.5"
options:
  backup_crypt_files:
    description:
      - Backup encrypted files.
    type: bool
    default: "yes"
  backup_dmapi_fs:
    description:
      - Back up DMAPI filesystem files.
    type: bool
    default: "yes"
  create_map_files:
    description:
      - Creates a new MAP files.
    type: bool
    default: "no"
  exclude_files:
    description:
      - Excludes files using C(/etc/rootvg.exclude).
    type: bool
    default: "no"
  exclude_wpar_files:
    description:
      - Excludes WPAR files.
    type: bool
    default: "no"
  extended_attrs:
    description:
      - Backup extended attributes.
    type: bool
    default: "yes"
  name:
    description:
      - Backup name
    required: true
  new_image_data:
    description:
      - Creates a new file data.
    type: bool
    default: "yes"
  software_packing:
    description:
      - Exclude files from packing option listed in
        C(/etc/exclude_packing.rootvg).
    type: bool
    default: "no"
  storage_path:
    description:
      - Storage path where the mksysb will stored.
    required: true
  use_snapshot:
    description:
      - Creates backup using snapshots.
    type: bool
    default: "no"
'''

EXAMPLES = '''
- name: Running a backup image mksysb
  mksysb:
    name: myserver
    storage_path: /repository/images
    exclude_files: yes
    exclude_wpar_files: yes
'''

RETURN = '''
changed:
  description: Return changed for mksysb actions as true or false.
  returned: always
  type: bool
  version_added: 2.5
msg:
  description: Return message regarding the action.
  returned: always
  type: str
  version_added: 2.5
'''


from ansible.module_utils.basic import AnsibleModule
import os


def main():
    module = AnsibleModule(
        argument_spec=dict(
            backup_crypt_files=dict(type='bool', default=True),
            backup_dmapi_fs=dict(type='bool', default=True),
            create_map_files=dict(type='bool', default=False),
            exclude_files=dict(type='bool', default=False),
            exclude_wpar_files=dict(type='bool', default=False),
            extended_attrs=dict(type='bool', default=True),
            name=dict(required=True),
            new_image_data=dict(type='bool', default=True),
            software_packing=dict(type='bool', default=False),
            storage_path=dict(required=True),
            use_snapshot=dict(type='bool', default=False)
        ),
        supports_check_mode=True,
    )

    # Command options.
    map_file_opt = {
        True: '-m',
        False: ''
    }

    use_snapshot_opt = {
        True: '-T',
        False: ''
    }

    exclude_files_opt = {
        True: '-e',
        False: ''
    }

    exclude_wpar_opt = {
        True: '-G',
        False: ''
    }

    new_image_data_opt = {
        True: '-i',
        False: ''
    }

    soft_packing_opt = {
        True: '',
        False: '-p'
    }

    extend_attr_opt = {
        True: '',
        False: '-a'
    }

    crypt_files_opt = {
        True: '',
        False: '-Z'
    }

    dmapi_fs_opt = {
        True: '-a',
        False: ''
    }

    backup_crypt_files = crypt_files_opt[module.params['backup_crypt_files']]
    backup_dmapi_fs = dmapi_fs_opt[module.params['backup_dmapi_fs']]
    create_map_files = map_file_opt[module.params['create_map_files']]
    exclude_files = exclude_files_opt[module.params['exclude_files']]
    exclude_wpar_files = exclude_wpar_opt[module.params['exclude_wpar_files']]
    extended_attrs = extend_attr_opt[module.params['extended_attrs']]
    name = module.params['name']
    new_image_data = new_image_data_opt[module.params['new_image_data']]
    software_packing = soft_packing_opt[module.params['software_packing']]
    storage_path = module.params['storage_path']
    use_snapshot = use_snapshot_opt[module.params['use_snapshot']]

    # Validate if storage_path is a valid directory.
    if os.path.isdir(storage_path):
        if not module.check_mode:
            # Generates the mksysb image backup.
            mksysb_cmd = module.get_bin_path('mksysb', True)
            rc, mksysb_output, err = module.run_command(
                "%s -X %s %s %s %s %s %s %s %s %s %s/%s" % (
                    mksysb_cmd, create_map_files, use_snapshot, exclude_files,
                    exclude_wpar_files, software_packing, extended_attrs,
                    backup_crypt_files, backup_dmapi_fs, new_image_data,
                    storage_path, name))
            if rc == 0:
                module.exit_json(changed=True, msg=mksysb_output)
            else:
                module.fail_json(msg="mksysb failed.", rc=rc, err=err)

        module.exit_json(changed=True)

    else:
        module.fail_json(msg="Storage path %s is not valid." % storage_path)


if __name__ == '__main__':
    main()
