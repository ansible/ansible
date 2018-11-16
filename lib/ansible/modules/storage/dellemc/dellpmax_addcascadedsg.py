#!/usr/bin/python
from ansible.module_utils.six.moves.urllib.error import HTTPError

__metaclass__ = type
import PyU4V

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
                  
short_description: 
    - module to add Child SG to Parent storage group on Dell EMC PowerMax, 
    Storage Groups must already exist and either be an empty SG or 

notes:
    - This module has been tested against UNI 9.0.    Every effort has been 
    made to verify the scripts run with valid input.  These modules 
    are a tech preview.  Additional error handling will be added at a later 
    date, base functionality only right now.

Requirements:
    - Ansible, Python 2.7, Unisphere for PowerMax version 9.0 or higher. 
    VMAX All Flash, VMAX3, or PowerMax storage Array
    Also requires PyU4V to be installed from PyPi using PIP
    python -m pip install PyU4V

playbook options:
    Note:- Some Options are repeated across modules, we will look at 
    reducing these in future work, however you can use variables in your 
    playbook at the outset and reference in the task to reduce error, 
    this also allows flexibility in versioning within a single playbook.   
    
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
    parent_sg:
        description:
            - Storage Group name for parent storage group
        required:True     
    array_id:
        description:
            - Integer 12 Digit Serial Number of PowerMAX or VMAX array.
        required:True
    child_sg:
        description:
            - Storage Group Name for Child SG

'''

EXAMPLES = r'''
- name: Simple Sample Playbook
  hosts: localhost
  connection: local
  vars:
        unispherehost: '192.168.156.63'
        universion: "90"
        verifycert: False
        user: 'smc'
        password: 'smc'
        array_id: '000197600123'
  tasks:
  - name: add child sg to parent
    dellpmax_addcascadedsg:
        unispherehost: "{{unispherehost}}"
        universion: "{{universion}}"
        verifycert: "{{verifycert}}"
        user: "{{user}}"
        password: "{{password}}"
        parent_sg: 'ansible_p'
        child_sg: 'ansible_d'
        array_id: "{{array_id}}"

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
            parent_sg=dict(type='str', required=True),
            child_sg=dict(type='str', required=True)
        )
    )

    conn = PyU4V.U4VConn(server_ip=module.params['unispherehost'], port=8443,
                         array_id=module.params['array_id'],
                         verify=module.params['verifycert'],
                         username=module.params['user'],
                         password=module.params['password'],
                         u4v_version=module.params['universion'])

    dellemc = conn.provisioning

    # Make REST call to Unisphere Server and execute create storage group

    changed = False
    # Compile a list of existing stroage groups.

    sglist = dellemc.get_storage_group_list()

    # Check if Storage Group already exists

    if module.params['parent_sg'] and module.params['child_sg'] in sglist:
        dellemc.add_child_sg_to_parent_sg(child_sg=module.params[
            'child_sg'],parent_sg=module.params['parent_sg'])
        changed = True

    else:
        module.fail_json(msg='Both Parent and Child SG must exist for module '
                             'to run sucessfully')

    module.exit_json(changed=changed)



from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()


