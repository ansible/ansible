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
short_description: "Create a new masking view on Dell EMC PowerMax or VMAX All
Flash"
version_added: "2.8"
description:
  - "This module has been tested against UNI 9.0. Every effort has been made
  to verify the scripts run with valid input. These modules are a tech preview"
module: dellpmax_createmaskingview
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
  sgname:
    description:
      - "32 Character string representing storage group name"
  host_or_cluster:
    description:
      - "Host or Cluster Name, Unique 32 Character string representing
      masking"
  maskingview_name:
    description:
      - "32 Character string representing masking view name, name must not
      already be in use"

requirements:
  - Ansible
  - "Unisphere for PowerMax version 9.0 or higher."
  - "VMAX All Flash, VMAX3, or PowerMax storage Array."
  - "PyU4V version 3.0.0.8 or higher using PIP python -m pip install PyU4V"
'''
EXAMPLES = '''
---
- name: "Create a Masking View from existing components"
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
    - name: "Create Masking View for Host Access to storage group volumes"
      dellpmax_createsg:
        array_id: "{{array_id}}"
        password: "{{password}}"
        unispherehost: "{{unispherehost}}"
        universion: "{{universion}}"
        user: "{{user}}"
        verifycert: "{{verifycert}}"
        sgname: "{{sgname}}"
        portgroup_id: "Ansible_PG"
        maskingview_name: "MyMaskingView"
'''
RETURN = r'''
'''
from ansible.module_utils.basic import AnsibleModule


def main():
    changed = False
    module = AnsibleModule(
        argument_spec=dict(
            unispherehost=dict(required=True),
            universion=dict(type='int', required=False),
            verifycert=dict(type='bool', required=True),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            array_id=dict(type='str', required=True),
            sgname=dict(type='str', required=True),
            host_or_cluster=dict(type='str', required=True),
            portgroup_id=dict(type='str', required=True),
            maskingview_name=dict(type='str', required=True)
        )
    )
    # Make REST call to Unisphere Server and execute create Host

    # Crete Connection to Unisphere Server to Make REST calls
    try:
        import PyU4V
    except:
        module.fail_json(
            msg='Requirements not met PyU4V is not installed, please install'
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

    # Make REST call to Unisphere Server and execute create storage group

    # Compile a list of existing stroage groups.

    mvlist = dellemc.get_masking_view_list()

    # Check if Storage Group already exists

    if module.params['maskingview_name'] not in mvlist:
        dellemc.create_masking_view_existing_components(
            port_group_name=module.params['portgroup_id'],
            masking_view_name=module.params['maskingview_name'],
            host_name=module.params['host_or_cluster'],
            storage_group_name=module.params['sgname'])
        changed = True
    else:
        module.fail_json(msg='Masking View Already Exists')
    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
