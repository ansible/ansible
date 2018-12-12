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
short_description: "Create port group on Dell EMC PowerMax or VMAX All
Flash"
version_added: "2.8"
description:
  - "This module has been tested against UNI 9.0. Every effort has been made
  to verify the scripts run with valid input. These modules are a tech preview"
module: dellpmax_createportgroup
options:
  array_id:
    description:
      - "Integer 12 Digit Serial Number of PowerMAX or VMAX array."
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
      - "Boolean, security check on ssl certificates"
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
  portgroup_id:
    description:
      - "32 Character string no special character permitted except for
      underscore"
  port_list:
    description:
      - "List of WWNs of Frontend Ports to be part of Port Group either FA
      or SE"
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
      dellpmax_createportgroup:
             unispherehost: "{{unispherehost}}"
             universion: "{{universion}}"
             verifycert: "{{verifycert}}"
             user: "{{user}}"
             password: "{{password}}"
             array_id: "{{array_id}}"
             port_list:
                     -
                      directorId: "FA-1D"
                      portId: "4"
                     -
                      directorId: "FA-2D"
                      portId: "4"
             portgroup_id: "Ansible_PG"
'''
RETURN = r'''
'''
from ansible.module_utils.basic import AnsibleModule


def main():
    changed = False
    # print (changed)
    module = AnsibleModule(
        argument_spec=dict(
            unispherehost=dict(required=True),
            universion=dict(type='int', required=False),
            verifycert=dict(type='bool', required=True),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            array_id=dict(type='str', required=True),
            portgroup_id=dict(type='str', required=True),
            port_list=dict(type='list', required=True),

        )
    )
    # Make REST call to Unisphere Server and execute create Host

    payload = (
        {
            "portGroupId": module.params['portgroup_id'],
            "symmetrixPortKey": module.params['port_list']
        }
    )

    headers = ({

        'Content-Type': 'application/json'

    })
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

    # Setting connection shortcut to Provisioning modules to simplify code

    dellemc = conn.provisioning

    changed = False


    pglist = dellemc.get_portgroup_list()

    if module.params['portgroup_id'] in pglist:
        module.fail_json(msg='Portgroup already exists, failing task')

    else:
        dellemc.create_multiport_portgroup(portgroup_id=module.params['portgroup_id'],
                                           ports=module.params['port_list'])
        changed = True

    module.exit_json(changed=changed)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
