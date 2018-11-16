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
module: dellpmax_createsnapshot

contributors: Paul Martin, Rob Mortell

software versions=ansible 2.6.3
                  python version = 2.7.15rc1 (default, Apr 15 2018,

short_description: module to create a snapvx snapshot, of an existing storage 
group on Dell EMC PowerMax VMAX All Flash or VMAX3 storage array. If 
Generation is not specified the module will link the latest version of a 
snapshot providing both storage group name is valid and has a snapshot of 
the specified name.  Module will check to see if storage group exists. 

#TODO add check to make sure stroage group is not empty right now this will 
fail

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

    snapshotname:
        Name of the snapshot to be linked
    target_sgname:
        Name of the Target Stroage group, if TGT stroage group doesn't 
        exist, it will be created with correct number of volumes and 
        snapshot will be linked.
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
  - name: Create SnapShot
    dellpmax_manage_snap:
        unispherehost: "{{unispherehost}}"
        port: "{{uniport}}"
        universion: "{{universion}}"
        verifycert: "{{verifycert}}"
        user: "{{user}}"
        password: "{{password}}"
        sgname: 'Ansible_test1234'
        array_id: '000197623456'
        ttl: 1
        snapshotname: 'Ansible_SnapShot'
        timeinhours: True
'''
RETURN = r'''
'''


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
            snapshotname=dict(type='str', required=True),
            target_sgname=dict(type='str', required=True),
            action=dict(type='str', choices=['link', 'relink', 'unlink'],
                        required=True)
        )
    )
    # Make REST call to Unisphere Server and execute create snapshot/

    conn = PyU4V.U4VConn(server_ip=module.params['unispherehost'], port=8443,
                         array_id=module.params['array_id'],
                         u4v_version=module.params['universion'],
                         verify=module.params['verifycert'],
                         username=module.params['user'],
                         password=module.params['password'])

    prov = conn.provisioning
    rep = conn.replication
    sglist = prov.get_storage_group_list()
    snaplist = rep.get_storagegroup_snapshot_list(module.params['sgname'])

    if module.params['sgname'] in sglist and module.params['snapshotname'] \
            in snaplist:
        if module.params['action'] == 'link':
            rep.modify_storagegroup_snap(source_sg_id=module.params['sgname'],
                                         snap_name=module.params[
                                             'snapshotname'],
                                         target_sg_id=module.params[
                                             'target_sgname'],
                                         link=True, new_name=None, gen_num=0,
                                         async=True)
        elif module.params['action'] == 'relink':
            rep.modify_storagegroup_snap(source_sg_id=module.params['sgname'],
                                         snap_name=module.params[
                                             'snapshotname'],
                                         target_sg_id=module.params[
                                             'target_sgname'],
                                         relink=True, gen_num=0, async=True)
        elif module.params['action'] == 'unlink':
            rep.modify_storagegroup_snap(source_sg_id=module.params['sgname'],
                                         snap_name=module.params[
                                             'snapshotname'],
                                         target_sg_id=module.params[
                                             'target_sgname'],
                                         unlink=True, gen_num=0,
                                         async=True)

        changed = True

        module.exit_json(changed=changed, msg='SnapVX Action completed '
                                              'Sucessfully')

    else:
        module.fail_json(msg='No Snapshot found with the supplied Parameters')


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
