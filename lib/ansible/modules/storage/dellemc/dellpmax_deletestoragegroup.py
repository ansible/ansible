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

Author: Paul Martin @rawstorage

Contributors: Rob Mortell @robmortell

software versions=ansible 2.6.2
                  python version = 2.7.15rc1 (default, Apr 15 2018,

short_description: 
    -Module to delete a storage group.  Should be used with Caution!! 
    Microcode will block deleting a storage group that is part of a masking 
    view, however other checks are advised.  Checks should be made to unlink 
    any snapshots if Storage Group is used as snapvx link target.   

requirements:
    -Storage Group must not be in masking view

notes:
    - This module has been tested against UNI 9.0.  Every effort has been 
    made to verify the scripts run with valid input.  These modules 
    are a tech preview.  Additional error handling will be added at a later 
    date, base functionality only right now.

Requirements:
    - Ansible, Python 2.7, Unisphere for PowerMax version 9.0 or higher. 
    VMAX All Flash, VMAX3, or PowerMAX storage Array. Python module PyU4V 
    also needs to be installed from pip or PyPi

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
    storagegroup:
        description:
            - Name of storage Group to provision storage volume to host.  
            Must already be created  
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
    - name: Create Masking View for Host Access
    dellpmax_deletestoragegroup:
             unispherehost: "{{unispherehost}}"
             universion: "{{universion}}"
             verifycert: "{{verifycert}}"
             user: "{{user}}"
             password: "{{password}}"
             array_id: "{{array_id}}"
             sgname: "Ansible_SG"
             
'''
RETURN = r'''
'''


def main():
    changed = False
    # print (changed)
    module = AnsibleModule(
        argument_spec=dict(
            unispherehost=dict(required=True),
            universion=dict(type='int', required=False),
            verifycert=dict(type='bool', required=True),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True),
            array_id=dict(type='str', required=True),
            sgname=dict(type='str', required=True)
        )
    )
    # Make REST call to Unisphere Server and execute create Host

    # Crete Connection to Unisphere Server to Make REST calls

    conn = PyU4V.U4VConn(server_ip=module.params['unispherehost'], port=8443,
                         array_id=module.params['array_id'],
                         verify=module.params['verifycert'],
                         username=module.params['user'],
                         password=module.params['password'],
                         u4v_version=module.params['universion'])

    # Setting connection shortcut to Provisioning modules to simplify code

    dellemc = conn.provisioning


    changed = False
    # Compile a list of existing storage groups.

    sglist = dellemc.get_storage_group_list(filters="num_of_masking_views=0")

    # Check if Storage Group already exists

    if module.params['sgname'] in sglist:
        #module.exit_json(msg=sglist)
        dellemc.delete_storagegroup(
            storagegroup_id=module.params['sgname'])
        changed = True


    else:
        module.fail_json(msg='Storage Group Does not exist or is part of  '
                             'Part of a Masking view unable to proceed')

    module.exit_json(changed=changed)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()


