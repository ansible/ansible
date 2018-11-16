#!/usr/bin/python

from __future__ import absolute_import, division, print_function
import PyU4V
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'VMAX REST API Community '
                                    'https://community.emc.com/docs/DOC-56447'
                    }
DOCUMENTATION = r'''
---
module: dellpmax_manage_srdf

contributors: Paul Martin, Rob Mortell

software versions=ansible 2.6.3
                  python version = 2.7.15rc1 (default, Apr 15 2018,

short_description: 
    - Module to control SRDF state of storage group, supported actions are 
    failover, failback, split, suspend, establish.  Requires that storage 
    group must exist and have RDF replication already configured and 
    running.  Single Site SRDF support only in module.     
 



notes:
    - This module has been tested against UNI 9.0.  Every effort has been
    made to verify the scripts run with valid input.  These modules
    are a tech preview.  Additional error handling will be added at a later
    date, base functionality only right now.

Requirements:
    - Ansible, Python 2.7, Unisphere for PowerMax version 9.0 or higher.
    VMAX All Flash, VMAX3, or PowerMax storage Array

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
        
'''

EXAMPLES = r'''
- name: Create SnapVX SnapShot of existing Storage Group
  hosts: localhost
  connection: local
  no_log: True
  vars:
        unispherehost: '192.168.156.63'
        universion: "90"
        verifycert: False
        user: 'smc'
        password: 'smc'


  tasks:
  - name: Split SRDF
    dellpmax_manage_srdf:
        unispherehost: "{{unispherehost}}"
        universion: "{{universion}}"
        verifycert: "{{verifycert}}"
        user: "{{user}}"
        password: "{{password}}"
        array_id: '000197600156'
        sgname: 'Ansible_SG'
        action: 'Split'
'

RETURN = r'''



def main():
    changed = False
    module = AnsibleModule(
        argument_spec=dict(
            unispherehost=dict(required=True),
            universion=dict(type='int', required=False),
            verifycert=dict(type='bool', required=True),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True),
            array_id=dict(type='str', required=True),
            sgname=dict(type='str', required=True),
            action=dict(type='str',choices=['Establish','Suspend','Split',
                                            'Failover','Failback'],
                        required=True)
        )
    )
    # Make REST call to Unisphere Server and execute SRDF control operation

    conn = PyU4V.U4VConn(server_ip=module.params['unispherehost'], port=8443,
                         array_id=module.params['array_id'],
                         u4v_version=module.params['universion'],
                         verify=module.params['verifycert'],
                         username=module.params['user'],
                         password=module.params['password'])

    rep=conn.replication
    rdf_sglist = rep.get_storage_group_rep_list(has_srdf=True)

    if module.params['sgname'] in rdf_sglist:
        rdfg_list = rep.get_storagegroup_srdfg_list(module.params['sgname'])
        if len(rdfg_list)<=1:
            rdfg = rdfg_list[0]
            rep.modify_storagegroup_srdf(storagegroup_id=module.params['sgname']
            , action=module.params['action'], rdfg=rdfg)
            changed = True
        else:
            module.fail_json(changed=changed,
                msg='Specified Storage Group has mult-site RDF Protection '
                    'Ansible Module currently supports single Site SRDF '
                    'please use Unishpere for PowerMax UI for SRDF group '
                    'managment')

    else:

        module.fail_json(msg='Specified Storage Group is not currently SRDF '
                             'Protected')


    module.exit_json(changed=changed)

if __name__ == '__main__':
    main()
