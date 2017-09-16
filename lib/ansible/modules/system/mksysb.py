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
  name:
    description:
      - Backup name
    required: true
  storage_path:
    description:
      - Storage path where the mksysb will stored.
    required: true
  create_map_files:
    description:
      - Creates a new MAP files.
    choices: ["yes", "no"]
    default: "no"
  use_snapshot:
    description:
      - Creates backup using snapshots.
    choices: ["yes", "no"]
    default: "no"
  exclude_files:
    description:
      - Excludes files using /etc/rootvg.exclude.
    choices: ["yes", "no"]
    default: "no"
  exclude_wpar_files:
    description:
      - Excludes WPAR files.
    choices: ["yes", "no"]
    default: "no"
  new_image_data:
    description:
      - Creates a new file data.
    choices: ["yes", "no"]
    default: "yes"
  software_packing:
    description:
      - Exclude files from packing option listed in
        /etc/exclude_packing.rootvg.
    choices: ["yes", "no"]
    default: "no"
  extended_attrs:
    description:
      - Backup extended attributes.
    choices: ["yes", "no"]
    default: "yes"
  backup_crypt_files:
    description:
      - Backup encrypted files.
    choices: ["yes", "no"]
    default: "yes"
  backup_dmapi_fs:
    description:
      - Back up DMAPI filesystem files.
    choices: ["yes", "no"]
    default: "yes"
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
  type: boolean
  version_added: 2.5
msg:
  description: Return message regarding the action.
  returned: always
  type: string
  version_added: 2.5
'''


from ansible.module_utils.basic import AnsibleModule

# command options
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


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            storage_path=dict(required=True),
            create_map_files=dict(type="bool", default=False),
            use_snapshot=dict(type="bool", default=False),
            exclude_files=dict(type="bool", default=False),
            exclude_wpar_files=dict(type="bool", default=False),
            new_image_data=dict(type="bool", default=True),
            software_packing=dict(type="bool", default=False),
            extended_attrs=dict(type="bool", default=True),
            backup_crypt_files=dict(type="bool", default=True),
            backup_dmapi_fs=dict(type="bool", default=True)
        ))

    name = module.params['name']
    storage_path = module.params['storage_path']
    create_map_files = map_file_opt[module.params['create_map_files']]
    use_snapshot = use_snapshot_opt[module.params['use_snapshot']]
    exclude_files = exclude_files_opt[module.params['exclude_files']]
    exclude_wpar_files = exclude_wpar_opt[module.params['exclude_wpar_files']]
    new_image_data = new_image_data_opt[module.params['new_image_data']]
    software_packing = soft_packing_opt[module.params['software_packing']]
    extended_attrs = extend_attr_opt[module.params['extended_attrs']]
    backup_crypt_files = crypt_files_opt[module.params['backup_crypt_files']]
    backup_dmapi_fs = dmapi_fs_opt[module.params['backup_dmapi_fs']]

    mksysb_cmd = module.get_bin_path("mksysb", True)

    # generates the mksysb image backup
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

if __name__ == '__main__':
    main()
