#!/usr/bin/python


from __future__ import absolute_import, division, print_function
import PyU4V
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'VMAX REST API Community '
                                    'https://community.emc.com/docs/DOC-56447'
                    }
DOCUMENTATION = r'''
---
module: dellpmax_createsg

contributors: Paul Martin, Rob Mortell

software versions=ansible 2.6.2
                  python version = 2.7.15rc1 (default, Apr 15 2018,
                  PyU4V v3.0.5 or higher

short_description: 
    module to add new volumes to existing storage group. This module can be 
    repeated multiple times in a playbook.

notes:
    - This module has been tested against UNI 9.0.  Every effort has been 
    made to verify the scripts run with valid input.  These modules 
    are a tech preview.  Additional error handling will be added at a later 
    date, base functionality only right now.



Requirements:
    - Ansible, Python 2.7, Unisphere for PowerMax version 9.0 or higher. 
    VMAX All Flash, VMAX3, or PowerMAX storage Array



playbook options:
    unispherehost:
        description:
            - Full Qualified Domain Name or IP address of Unisphere for 
            PowerMax host.
        required:True

    universion:
        -description:
            - Integer, version of unipshere software 
            https://{HostName|IP}:8443/univmax/restapi/{version}/{resource}
            90 is the release at time of writing module.
        -required:True
    verifycert:
        description: 
            -Boolean, securitly check on ssl certificates
        required:True             

        required: True
    array_id:
        description:
            - Integer 12 Digit Serial Number of PowerMAX or VMAX array.
        required:True
    host_id:
         description:
            -  String value to denote hostname, No  Special Character 
            support except for _.  Case sensistive for REST Calls.
        required:True
    initiator_list:
        description:
            - List of Initiator WWN or IQN 
        required:True
    consistent_lun:
        description:
            - Boolean Value, specifying consistent_lun ensures LUN address 
            consistency across ports, this is not required on most modern 
            operating systems as WWN or UUID is used to Uniqely identify luns
        required:True    
    async:
        Optional Parameter to set REST call to run Asyncronously, job will 
        be submitted to job queue and executed.  Task Id will be returned in 
        JSON for lookup purposed to check job completion status. 

'''

EXAMPLES = r'''
- name: Create Host
  hosts: localhost
  connection: local
  vars:
        unispherehost: '192.168.20.63'
        uniport: 8443
        universion: "90"
        verifycert: False
        user: 'smc'
        password: 'smc'
        array_id: "000197600123"
  tasks:
  - name: Create Host2
    dellpmax_createhost:
        unispherehost: "{{unispherehost}}"
        universion: "{{universion}}"
        verifycert: "{{verifycert}}"
        user: "{{user}}"
        password: "{{password}}"
        array_id: "{{array_id}}"
        initiator_list:
        - 10000000c98ffea2
        - 10000000c98ffeb3
        host_id: "AnsibleHost2"

'''
RETURN = r'''
'''


def main():

    module = AnsibleModule(
        argument_spec=dict(
            unispherehost=dict(required=True),
            universion=dict(type='int', required=False),
            verifycert=dict(type='bool', required=True),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True),
            array_id=dict(type='str', required=True),
            host_id=dict(type='str', required=True),
            initiator_list=dict(type='list', required=True),

        )
    )

#Crete Connection to Unisphere Server to Make REST calls

    conn = PyU4V.U4VConn(server_ip=module.params['unispherehost'], port=8443,
                         array_id=module.params['array_id'],
                         verify=module.params['verifycert'],
                         username=module.params['user'],
                         password=module.params['password'],
                         u4v_version=module.params['universion'])

    # Setting connection shortcut to Provisioning modules to simplify code

    dellemc = conn.provisioning

    changed = False
    # Compile a list of existing stroage groups.

    hostlist = dellemc.get_host_list()

    # Check if Host Name already exists

    if module.params['host_id'] not in hostlist:
        dellemc.create_host(host_name=module.params['host_id'],
                            initiator_list=module.params['initiator_list'])
        changed = True

    else:
        module.fail_json(msg='Host Name already exists, Failing Task')

    module.exit_json(changed=changed)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
