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
    - module to create an Empty storage group on Dell EMC PowerMax, An Empty 
    SG is usually created for Parent Child Relationship, child storage group 
    can be created with dellpmax_createsg module and added with 
    dellpmax_addcasascadedsg module  


notes:
    - This module has been tested against UNI 9.0. Every effort has been 
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
    sgname:
        description:
            - Storage Group name
        required:True     
    array_id:
        description:
            - Integer 12 Digit Serial Number of PowerMAX or VMAX array.
        required:True
    srp_id:
        description:
            - Storage Resource Pool Name, Default is set to SRP_1, if your 
            system has mainframe or multiple pools you can set this to a 
            different value to match your environemt
        required:Optional
    slo:
        description:
            - Service Level for the storage group, Supported on VMAX3 and All 
            Flash and PoweMAX NVMe Arrays running PowerMAX OS 5978 and 
            above.  Default is set to None as it is expected user will set 
            at child storage group.
        required: Optional
    workload:
        description:
            - Block workload type, optional and can only be set on VMAX3 
            Hybrid Storage Arrays.  Default None.
        required:Optional
    async:
        Optional Parameter to set REST call to run Asyncronously, job will 
        be submitted to job queue and executed.  Task Id will be returned in 
        JSON for lookup purposed to check job completion status. 


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
        sgname: 'Ansible_EMPTYSG'
        array_id: '000197600123'
  tasks:
  - name: Create New Empty Storage Group
    dellpmax_create_emptysg:
        unispherehost: "{{unispherehost}}"
        universion: "{{universion}}"
        verifycert: "{{verifycert}}"
        user: "{{user}}"
        password: "{{password}}"
        sgname: "{{sgname}}"
        array_id: "{{array_id}}"
        srp_id: 'SRP_1'
        slo: None
        workload: None

'''
RETURN = r'''
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            sgname=dict(type='str',required=True),
            unispherehost=dict(required=True),
            universion=dict(type='int', required=False),
            verifycert=dict(type='bool', required=True),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True),
            array_id=dict(type='str', required=True),
            srp_id=dict(type='str', required=False),
            slo=dict(type='str', required=False),
            workload=dict(type='str', required=False)

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
    # Compile a list of existing storage groups.

    sglist = dellemc.get_storage_group_list()

    # Check if Storage Group already exists

    if module.params['sgname'] not in sglist:
        dellemc.create_empty_sg(srp_id='SRP_1',
                                              sg_id=module.params['sgname'],
                                              slo=module.params['slo'],
                                              workload=None
                                              )
        changed = True

    else:
        module.fail_json(msg='Storage Group Already Exists')

    module.exit_json(changed=changed)



from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()


