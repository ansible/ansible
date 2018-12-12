#!/usr/bin/python
# Copyright (C) 2018 DellEMC
# Author(s): Paul Martin <paule.martin@dell.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
author:
  - "Paul Martin (@rawstorage)"
short_description: "Create storage group on Dell EMC PowerMax or VMAX All
Flash"
version_added: "2.8"
description:
  - "This module has been tested against UNI 9.0. Every effort has been made
  to verify the scripts run with valid input. These modules are a tech preview"
module: dellpmax_addvolume
options:
  array_id:
    description:
      - "Integer 12 Digit Serial Number of PowerMAX or VMAX array."
    required: true
  cap_unit:
    choices:
      - GB
      - TB
      - MB
      - CYL
    description:
      - "String value, default is set to GB"
    required: false
  num_vols:
    description:
      - "integer value for the number of volumes. Minimum is 1, module will
      fail if less than one volume is specified or value is 0. If volumes are
      required of different sizes, addional tasks should be added to playbooks
      to use dellpmax_addvolume module"
    required: true
  sgname:
    description:
      - "Existing Storage Group name 32 Characters no special characters other 
      than underscore."
    required: true
  unispherehost:
    description:
      - "Fully Qualified Domain Name or IP address of Unisphere for PowerMax
      host."
    required: true
  universion:
    description:
      - "Integer, version of unipshere software  e.g. 90"
    required: true
  verifycert:
    description:
      - "Boolean, securitly check on ssl certificates"
    type: bool
    required: true
  vol_size:
    description:
      - "Integer value for the size of volumes.  All volumes will be created
      with same size.  Use dellpmax_addvol to add additional volumes if you
      require different sized volumes once storage group is created."
    required: true
  volumeIdentifier:
    description:
      - "String up to 64 Characters no special character other than
      underscore sets a label to make volumes easily identified on hosts can
      run Dell EMC inq utility command to see this label is  inq -identifier
      device_name"
    required: false
  user:
    description:
      - "Unisphere username"
  password:
    description:
      - "password for Unisphere user"
requirements:
  - Ansible
  - "Unisphere for PowerMax version 9.0 or higher."
  - "VMAX All Flash, VMAX3, or PowerMax storage Array."
  - "PyU4V version 3.0.0.8 or higher using PIP python -m pip install PyU4V"
'''
EXAMPLES = '''
---
- name: "Add volumes to existing storage group"
  connection: local
  hosts: localhost
  vars:
    array_id: 000197600156
    password: smc
    sgname: Ansible_SG
    unispherehost: "192.168.1.123"
    universion: "90"
    user: smc
    verifycert: false

  tasks:
  - name: Add REDO Volumes to Storage Group
    dellpmax_addvolume:
        unispherehost: "{{unispherehost}}"
        universion: "{{universion}}"
        verifycert: "{{verifycert}}"
        user: "{{user}}"
        password: "{{password}}"
        sgname: "{{sgname}}"
        array_id: "{{array_id}}"
        num_vols: 1
        vol_size:  2
        cap_unit: 'GB'
        volumeIdentifier: 'REDO'
'''
RETURN = '''
'''
from ansible.module_utils.basic import AnsibleModule


def main():
    changed = False
    # print (changed)
    module = AnsibleModule(
        argument_spec=dict(
            sgname=dict(type='str', required=True),
            unispherehost=dict(required=True),
            universion=dict(type='int', required=False),
            verifycert=dict(type='bool', required=True),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            array_id=dict(type='str', required=True),
            num_vols=dict(type='int', required=True),
            vol_size=dict(type='int', required=True),
            cap_unit=dict(type='str', required=True, choices=['GB',
                                                              'TB',
                                                              'MB', 'CYL']),
            volumeIdentifier=dict(type='str', required=True)
        )
    )
    try:
        import PyU4V
    except:
        module.fail_json(
            msg='Requirements not met PyU4V is not installed, please install '
                'via PIP')
        module.exit_json(changed=changed)

    # Crete Connection to Unisphere Server to Make REST calls

    conn = PyU4V.U4VConn(server_ip=module.params['unispherehost'], port=8443,
                         array_id=module.params['array_id'],
                         verify=module.params['verifycert'],
                         username=module.params['user'],
                         password=module.params['password'],
                         u4v_version=module.params['universion'])

    #Setting connection shortcut to Provisioning modules to simplify code

    dellemc = conn.provisioning

    changed = False

    # Compile a list of existing stroage groups.

    sglist = dellemc.get_storage_group_list()

    # Check if Storage Group already exists

    if module.params['sgname'] not in sglist:
        module.fail_json(msg='Storage group does not Exist, Failing Task')
    else:
        dellemc.add_new_vol_to_storagegroup(sg_id=module.params['sgname'],
                                            num_vols=module.params['num_vols'],
                                            cap_unit=module.params['cap_unit'],
                                            vol_size=module.params['vol_size'],
                                            vol_name=module.params[
                                                'volumeIdentifier'],
                                            async=False)
        changed = True
    module.exit_json(changed=changed)

if __name__ == '__main__':
    main()