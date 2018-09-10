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

contributors: Paul Martin @rawstorage
             

software versions=ansible 2.6.2
                  python version = 2.7.15rc1 (default, Apr 15 2018,
                  PyU4V v3.0.5 or higher
short_description: 
    Module to Create Host Group for Masking Storage to a Cluster, 
    host groups are collections of hosts.  This module requires that hosts 
    have already 

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
- name: Create Cluster
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
    dellpmax_createhostgroup:
             unispherehost: "{{unispherehost}}"
             universion: "{{universion}}"
             verifycert: "{{verifycert}}"
             user: "{{user}}"
             password: "{{password}}"
             array_id: "{{array_id}}"
             host_list:
              - "AnsibleHost1"
              - "AnsibleHost2"
             cluster_name: "AnsibleCluster"

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
            cluster_name=dict(type='str', required=True),
            host_list=dict(type='list', required=True),

        )
    )
    # Make REST call to Unisphere Server and execute create Host

    payload = (
        {
        "hostGroupId": module.params['cluster_name'],
        "hostId":
        module.params['host_list']
        }
    )
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
    # Check for each host in the host list that it exists, otherwise fail
    # module.

    configuredhostlist = dellemc.get_host_list()

    for host in configuredhostlist:
        if host in configuredhostlist:
            dellemc.create_hostgroup(hostgroup_id=module.params['cluster_name']
                                     ,host_list=module.params['host_list'])
        else:
            module.fail_json(msg='Host %s does not exist, failing task' % (
                host))


    module.exit_json(changed=changed)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()


