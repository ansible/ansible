#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ucs_managed_objects
short_description: Configures Managed Objects on Cisco UCS Manager
description:
- Configures Managed Objects on Cisco UCS Manager.
- The Python SDK module, Python class within the module (UCSM Class), and all properties must be directly specified.
- More information on the UCSM Python SDK and how to directly configure Managed Objects is available at L(UCSM Python SDK,http://ucsmsdk.readthedocs.io/).
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify that the Managed Objects are present and will create if needed.
    - If C(absent), will verify that the Managed Objects are absent and will delete if needed.
    choices: [ absent, present ]
    default: present
  objects:
    description:
    - List of managed objects to configure.  Each managed object has suboptions the specify the Python SDK module, class, and properties to configure.
    suboptions:
      module:
        description:
        - Name of the Python SDK module implementing the required class.
        required: yes
      class_name:
        description:
        - Name of the Python class that will be used to configure the Managed Object.
        required: yes
      properties:
        description:
        - List of properties to configure on the Managed Object.  See the UCSM Python SDK for information on properties for each class.
        required: yes
      children:
        description:
        - Optional list of child objects.  Each child has its own module, class, and properties suboptions.
        - The parent_mo_or_dn property for child objects is automatically set as the list of children is configured.
    required: yes
requirements:
- ucsmsdk
author:
- David Soper (@dsoper2)
- CiscoUcs (@CiscoUcs)
version_added: '2.8'
'''

EXAMPLES = r'''
- name: Configure Network Control Policy
  ucs_managed_objects:
    hostname: 172.16.143.150
    username: admin
    password: password
    objects:
    - module: ucsmsdk.mometa.nwctrl.NwctrlDefinition
      class: NwctrlDefinition
      properties:
        parent_mo_or_dn: org-root
        cdp: enabled
        descr: ''
        lldp_receive: enabled
        lldp_transmit: enabled
        name: Enable-CDP-LLDP

- name: Remove Network Control Policy
  ucs_managed_objects:
    hostname: 172.16.143.150
    username: admin
    password: password
    objects:
    - module: ucsmsdk.mometa.nwctrl.NwctrlDefinition
      class: NwctrlDefinition
      properties:
        parent_mo_or_dn: org-root
        name: Enable-CDP-LLDP
    state: absent

- name: Configure Boot Policy Using JSON objects list with children
  ucs_managed_objects:
    hostname: 172.16.143.150
    username: admin
    password: password
    objects:
    - {
          "module": "ucsmsdk.mometa.lsboot.LsbootPolicy",
          "class": "LsbootPolicy",
          "properties": {
              "parent_mo_or_dn": "org-root",
              "name": "Python_SDS",
              "enforce_vnic_name": "yes",
              "boot_mode": "legacy",
              "reboot_on_update": "no"
          },
          "children": [
              {
                  "module": "ucsmsdk.mometa.lsboot.LsbootVirtualMedia",
                  "class": "LsbootVirtualMedia",
                  "properties": {
                      "access": "read-only-local",
                      "lun_id": "0",
                      "order": "2"
                  }
              },
              {
                  "module": "ucsmsdk.mometa.lsboot.LsbootStorage",
                  "class": "LsbootStorage",
                  "properties": {
                      "order": "1"
                  },
                  "children": [
                      {
                          "module": "ucsmsdk.mometa.lsboot.LsbootLocalStorage",
                          "class": "LsbootLocalStorage",
                          "properties": {},
                          "children": [
                              {
                                  "module": "ucsmsdk.mometa.lsboot.LsbootDefaultLocalImage",
                                  "class": "LsbootDefaultLocalImage",
                                  "properties": {
                                      "order": "1"
                                  }
                              }
                          ]
                      }
                  ]
              }
          ]
      }

- name: Remove Boot Policy Using JSON objects list
  ucs_managed_objects:
    hostname: 172.16.143.150
    username: admin
    password: password
    objects:
    - {
          "module": "ucsmsdk.mometa.lsboot.LsbootPolicy",
          "class": "LsbootPolicy",
          "properties": {
              "parent_mo_or_dn": "org-root",
              "name": "Python_SDS"
          }
      }
    state: absent


'''

RETURN = r'''
#
'''

import traceback

IMPORT_IMP_ERR = None
try:
    from importlib import import_module
    HAS_IMPORT_MODULE = True
except Exception:
    IMPORT_IMP_ERR = traceback.format_exc()
    HAS_IMPORT_MODULE = False

from copy import deepcopy
import json
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def traverse_objects(module, ucs, managed_object, mo=''):
    props_match = False

    mo_module = import_module(managed_object['module'])
    mo_class = getattr(mo_module, managed_object['class'])

    if not managed_object['properties'].get('parent_mo_or_dn'):
        managed_object['properties']['parent_mo_or_dn'] = mo

    mo = mo_class(**managed_object['properties'])

    existing_mo = ucs.login_handle.query_dn(mo.dn)

    if module.params['state'] == 'absent':
        # mo must exist, but all properties do not have to match
        if existing_mo:
            if not module.check_mode:
                ucs.login_handle.remove_mo(existing_mo)
                ucs.login_handle.commit()
            ucs.result['changed'] = True
    else:
        if existing_mo:
            # check mo props
            kwargs = dict(managed_object['properties'])
            # remove parent info and passwords because those aren't presented in the actual props
            kwargs.pop('parent_mo_or_dn', None)
            kwargs.pop('pwd', None)
            kwargs.pop('password', None)
            if existing_mo.check_prop_match(**kwargs):
                props_match = True

        if not props_match:
            if not module.check_mode:
                try:
                    ucs.login_handle.add_mo(mo, modify_present=True)
                    ucs.login_handle.commit()
                except Exception as e:
                    ucs.result['err'] = True
                    ucs.result['msg'] = "setup error: %s " % str(e)

            ucs.result['changed'] = True

    if managed_object.get('children'):
        for child in managed_object['children']:
            # explicit deep copy of child object since traverse_objects may modify parent mo information
            copy_of_child = deepcopy(child)
            traverse_objects(module, ucs, copy_of_child, mo)


def main():
    object_dict = dict(
        module=dict(type='str', required=True),
        class_name=dict(type='str', aliases=['class'], required=True),
        properties=dict(type='dict', required=True),
        children=dict(type='list'),
    )
    argument_spec = ucs_argument_spec
    argument_spec.update(
        objects=dict(type='list', elements='dict', options=object_dict, required=True),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )

    if not HAS_IMPORT_MODULE:
        module.fail_json(msg=missing_required_lib('importlib'), exception=IMPORT_IMP_ERR)
    ucs = UCSModule(module)

    ucs.result['err'] = False
    # note that all objects specified in the object list report a single result (including a single changed).
    ucs.result['changed'] = False

    for managed_object in module.params['objects']:
        traverse_objects(module, ucs, managed_object)

    if ucs.result['err']:
        module.fail_json(**ucs.result)
    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()
