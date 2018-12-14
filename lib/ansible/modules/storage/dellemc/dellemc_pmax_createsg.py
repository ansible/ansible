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
module: dellemc_pmax_createsg
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
      required of different sizes, additional tasks should be added to
      playbooks to use dellemc_pmax_addvolume module"
    required: true
  sgname:
    description:
      - "Storage Group name 32 Characters no special characters other than
      underscore"
    required: true
  slo:
    description:
      - "Service Level for the storage group, Supported on VMAX3 and All Flash
      and PowerMAX NVMe Arrays running PowerMAX OS 5978 and above.  Default is
      set to Diamond, but user can override this by setting a different value."
    required: false
  srp_id:
    description:
      - "Storage Resource Pool Name, Default is set to SRP_1, if your system
      has mainframe or multiple pools you can set this to a different value to
      match your environment"
    required: false
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
      - "Boolean, security check on ssl certificates"
    type: bool
    required: true
  vol_size:
    description:
      - "Integer value for the size of volumes.  All volumes will be created
      with same size.  Use dellemc_pmax_addvol to add additional volumes if you
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
  workload:
    description:
      - "Block workload type, optional and can only be set on VMAX3 Hybrid
      Storage Arrays. Default None."
    required: false
requirements:
  - Ansible
  - "Unisphere for PowerMax version 9.0 or higher."
  - "VMAX All Flash, VMAX3, or PowerMax storage Array."
  - "PyU4V version 3.0.0.8 or higher using PIP python -m pip install PyU4V"
'''
EXAMPLES = '''
---
- name: "Provision Storage For DB Cluster"
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
    - name: "Create New Storage Group and add data volumes"
      dellemc_pmax_createsg:
        array_id: "{{array_id}}"
        cap_unit: GB
        num_vols: 1
        password: "{{password}}"
        sgname: "{{sgname}}"
        slo: Diamond
        srp_id: SRP_1
        unispherehost: "{{unispherehost}}"
        universion: "{{universion}}"
        user: "{{user}}"
        verifycert: "{{verifycert}}"
        vol_size: 1
        workload: None
        volumeIdentifier: 'REDO'
'''
RETURN = '''
'''
from ansible.module_utils.basic import AnsibleModule


def main():
    changed = False
    module = AnsibleModule(
        argument_spec=dict(
            sgname=dict(type='str', required=True),
            unispherehost=dict(required=True),
            universion=dict(type='int', required=False),
            verifycert=dict(type='bool', required=True),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            array_id=dict(type='str', required=True),
            srp_id=dict(type='str', required=False),
            slo=dict(type='str', required=False),
            workload=dict(type='str', required=False),
            num_vols=dict(type='int', required=True),
            vol_size=dict(type='int', required=True),
            cap_unit=dict(type='str', required=True, choices=['GB',
                                                              'TB',
                                                              'MB', 'CYL']),
            volumeIdentifier=dict(type='str', required=False)))
    try:
        import PyU4V
    except:
        module.fail_json(
            msg='Requirements not met PyU4V is not installed, please install '
                'via PIP')
        module.exit_json(changed=changed)

    conn = PyU4V.U4VConn(server_ip=module.params['unispherehost'], port=8443,
                         array_id=module.params['array_id'],
                         verify=module.params['verifycert'],
                         username=module.params['user'],
                         password=module.params['password'],
                         u4v_version=module.params['universion'])
    dellemc = conn.provisioning
    # Compile a list of existing storage groups.
    sglist = dellemc.get_storage_group_list()
    # Check if Storage Group already exists
    if module.params['sgname'] not in sglist:
        dellemc.create_storage_group(srp_id='SRP_1',
                                     sg_id=module.params['sgname'],
                                     slo=module.params['slo'],
                                     num_vols=module.params['num_vols'],
                                     vol_size=module.params['vol_size'],
                                     cap_unit=module.params['cap_unit'],
                                     workload=None,
                                     vol_name=module.params['volumeIdentifier']
                                     )
        changed = True
    else:
        module.fail_json(msg='Storage Group Already Exists')
    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
