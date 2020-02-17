#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Paul Knight <paul.knight@delaware.gov>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_appliance_health_info
short_description: Gathers info about health of the VCSA.
description:
- This module can be used to gather information about VCSA health.
- This module is based on REST API and uses httpapi connection plugin for persistent connection.
- The Appliance API works against the VCSA and uses the "administrator@vsphere.local" user.
version_added: '2.10'
author:
- Paul Knight (@n3pjk)
notes:
- Tested on vSphere 6.7
requirements:
- python >= 2.6
options:
  subsystem:
    description:
    - A subsystem of the VCSA.
    required: false
    choices: ['applmgmt', 'databasestorage', 'lastcheck', 'load', 'mem', 'softwarepackages', 'storage', 'swap', 'system']
    type: str
  asset:
    description:
    - A VCSA asset that has associated health metrics.
    - Valid choices have yet to be determined at this time.
    required: false
    type: str
extends_documentation_fragment: VmwareRestModule.documentation
'''

EXAMPLES = r'''
- hosts: all
  connection: httpapi
  gather_facts: false
  vars:
    ansible_network_os: vmware
    ansible_host: vcenter.my.domain
    ansible_user: administrator@vsphere.local
    ansible_httpapi_password: "SomePassword"
    ansible_httpapi_use_ssl: yes
    ansible_httpapi_validate_certs: false
  tasks:

    - name: Get all health attribute information
      vmware_appliance_health_info:

    - name: Get system health information
      vmware_appliance_health_info:
        subsystem: system
'''

RETURN = r'''
attribute:
    description: facts about the specified health attribute
    returned: always
    type: dict
    sample: {
        "value": true
    }
'''

from ansible.module_utils.vmware_httpapi.VmwareRestModule import API, VmwareRestModule


SLUG = dict(
    applmgmt='/health/applmgmt',
    databasestorage='/health/database-storage',
    load='/health/load',
    mem='/health/mem',
    softwarepackages='/health/software-packages',
    storage='/health/storage',
    swap='/health/swap',
    system='/health/system',
    lastcheck='/health/system/lastcheck',
)


def get_subsystem(module, subsystem):
    try:
        url = API['appliance']['base'] + SLUG[subsystem]
    except KeyError:
        module.fail(msg='[%s] is not a valid subsystem. '
                    'Please specify correct subsystem, valid choices are '
                    '[%s].' % (subsystem, ", ".join(list(SLUG.keys()))))

    module.get(url=url, key=subsystem)


def main():
    argument_spec = VmwareRestModule.create_argument_spec()
    argument_spec.update(
        subsystem=dict(
            type='str',
            required=False,
            choices=[
                'applmgmt',
                'databasestorage',
                'lastcheck',
                'load',
                'mem',
                'softwarepackages',
                'storage',
                'swap',
                'system',
            ],
        ),
        asset=dict(type='str', required=False),
    )

    module = VmwareRestModule(argument_spec=argument_spec,
                              supports_check_mode=True,
                              is_multipart=True,
                              use_object_handler=True)
    subsystem = module.params['subsystem']
    asset = module.params['asset']

    if asset is not None:
        url = (API['appliance']['base']
               + ('/health/%s/messages' % asset))

        module.get(url=url, key=asset)
    elif subsystem is None:
        subsystem = SLUG.keys()
        for sys in subsystem:
            get_subsystem(module, sys)
    else:
        get_subsystem(module, subsystem)

    module.exit()


if __name__ == '__main__':
    main()
