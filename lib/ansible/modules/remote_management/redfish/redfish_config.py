#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018 Dell EMC Inc.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: redfish_config
version_added: "2.7"
short_description: Manages Out-Of-Band controllers using Redfish APIs
description:
  - Builds Redfish URIs locally and sends them to remote OOB controllers to
    set or update a configuration attribute.
  - Manages BIOS configuration settings.
  - Manages OOB controller configuration settings.
options:
  category:
    required: true
    description:
      - Category to execute on OOB controller
    type: str
  command:
    required: true
    description:
      - List of commands to execute on OOB controller
    type: list
  baseuri:
    required: true
    description:
      - Base URI of OOB controller
    type: str
  username:
    required: true
    description:
      - User for authentication with OOB controller
    type: str
    version_added: "2.8"
  password:
    required: true
    description:
      - Password for authentication with OOB controller
    type: str
  bios_attribute_name:
    required: false
    description:
      - name of BIOS attr to update (deprecated - use bios_attributes instead)
    default: 'null'
    type: str
    version_added: "2.8"
  bios_attribute_value:
    required: false
    description:
      - value of BIOS attr to update (deprecated - use bios_attributes instead)
    default: 'null'
    type: str
    version_added: "2.8"
  bios_attributes:
    required: false
    description:
      - dictionary of BIOS attributes to update
    default: {}
    type: dict
    version_added: "2.10"
  timeout:
    description:
      - Timeout in seconds for URL requests to OOB controller
    default: 10
    type: int
    version_added: "2.8"
  boot_order:
    required: false
    description:
      - list of BootOptionReference strings specifying the BootOrder
    default: []
    type: list
    version_added: "2.10"
  network_protocols:
    required: false
    description:
      -  setting dict of manager services to update
    type: dict
    version_added: "2.10"
  resource_id:
    required: false
    description:
      - The ID of the System, Manager or Chassis to modify
    type: str
    version_added: "2.10"
  nic_addr:
    required: false
    description:
      - EthernetInterface Address string on OOB controller
    default: 'null'
    type: str
    version_added: '2.10'
  nic_config:
    required: false
    description:
      - setting dict of EthernetInterface on OOB controller
    type: dict
    version_added: '2.10'

author: "Jose Delarosa (@jose-delarosa)"
'''

EXAMPLES = '''
  - name: Set BootMode to UEFI
    redfish_config:
      category: Systems
      command: SetBiosAttributes
      resource_id: 437XR1138R2
      bios_attributes:
        BootMode: "Uefi"
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Set multiple BootMode attributes
    redfish_config:
      category: Systems
      command: SetBiosAttributes
      resource_id: 437XR1138R2
      bios_attributes:
        BootMode: "Bios"
        OneTimeBootMode: "Enabled"
        BootSeqRetry: "Enabled"
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Enable PXE Boot for NIC1 using deprecated options
    redfish_config:
      category: Systems
      command: SetBiosAttributes
      resource_id: 437XR1138R2
      bios_attribute_name: PxeDev1EnDis
      bios_attribute_value: Enabled
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Set BIOS default settings with a timeout of 20 seconds
    redfish_config:
      category: Systems
      command: SetBiosDefaultSettings
      resource_id: 437XR1138R2
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
      timeout: 20

  - name: Set boot order
    redfish_config:
      category: Systems
      command: SetBootOrder
      boot_order:
        - Boot0002
        - Boot0001
        - Boot0000
        - Boot0003
        - Boot0004
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Set boot order to the default
    redfish_config:
      category: Systems
      command: SetDefaultBootOrder
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Set Manager Network Protocols
    redfish_config:
      category: Manager
      command: SetNetworkProtocols
      network_protocols:
        SNMP:
          ProtocolEnabled: True
          Port: 161
        HTTP:
          ProtocolEnabled: False
          Port: 8080
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Set Manager NIC
    redfish_config:
      category: Manager
      command: SetManagerNic
      nic_config:
        DHCPv4:
          DHCPEnabled: False
        IPv4StaticAddresses:
          Address: 192.168.1.3
          Gateway: 192.168.1.1
          SubnetMask: 255.255.255.0
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
'''

RETURN = '''
msg:
    description: Message with action result or error description
    returned: always
    type: str
    sample: "Action was successful"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.redfish_utils import RedfishUtils
from ansible.module_utils._text import to_native


# More will be added as module features are expanded
CATEGORY_COMMANDS_ALL = {
    "Systems": ["SetBiosDefaultSettings", "SetBiosAttributes", "SetBootOrder",
                "SetDefaultBootOrder"],
    "Manager": ["SetNetworkProtocols", "SetManagerNic"]
}


def main():
    result = {}
    module = AnsibleModule(
        argument_spec=dict(
            category=dict(required=True),
            command=dict(required=True, type='list'),
            baseuri=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            bios_attribute_name=dict(default='null'),
            bios_attribute_value=dict(default='null'),
            bios_attributes=dict(type='dict', default={}),
            timeout=dict(type='int', default=10),
            boot_order=dict(type='list', elements='str', default=[]),
            network_protocols=dict(
                type='dict',
                default={}
            ),
            resource_id=dict(),
            nic_addr=dict(default='null'),
            nic_config=dict(
                type='dict',
                default={}
            )
        ),
        supports_check_mode=False
    )

    category = module.params['category']
    command_list = module.params['command']

    # admin credentials used for authentication
    creds = {'user': module.params['username'],
             'pswd': module.params['password']}

    # timeout
    timeout = module.params['timeout']

    # BIOS attributes to update
    bios_attributes = module.params['bios_attributes']
    if module.params['bios_attribute_name'] != 'null':
        bios_attributes[module.params['bios_attribute_name']] = module.params[
            'bios_attribute_value']
        module.deprecate(msg='The bios_attribute_name/bios_attribute_value '
                         'options are deprecated. Use bios_attributes instead',
                         version='2.14')

    # boot order
    boot_order = module.params['boot_order']

    # System, Manager or Chassis ID to modify
    resource_id = module.params['resource_id']

    # manager nic
    nic_addr = module.params['nic_addr']
    nic_config = module.params['nic_config']

    # Build root URI
    root_uri = "https://" + module.params['baseuri']
    rf_utils = RedfishUtils(creds, root_uri, timeout, module,
                            resource_id=resource_id, data_modification=True)

    # Check that Category is valid
    if category not in CATEGORY_COMMANDS_ALL:
        module.fail_json(msg=to_native("Invalid Category '%s'. Valid Categories = %s" % (category, CATEGORY_COMMANDS_ALL.keys())))

    # Check that all commands are valid
    for cmd in command_list:
        # Fail if even one command given is invalid
        if cmd not in CATEGORY_COMMANDS_ALL[category]:
            module.fail_json(msg=to_native("Invalid Command '%s'. Valid Commands = %s" % (cmd, CATEGORY_COMMANDS_ALL[category])))

    # Organize by Categories / Commands
    if category == "Systems":
        # execute only if we find a System resource
        result = rf_utils._find_systems_resource()
        if result['ret'] is False:
            module.fail_json(msg=to_native(result['msg']))

        for command in command_list:
            if command == "SetBiosDefaultSettings":
                result = rf_utils.set_bios_default_settings()
            elif command == "SetBiosAttributes":
                result = rf_utils.set_bios_attributes(bios_attributes)
            elif command == "SetBootOrder":
                result = rf_utils.set_boot_order(boot_order)
            elif command == "SetDefaultBootOrder":
                result = rf_utils.set_default_boot_order()

    elif category == "Manager":
        # execute only if we find a Manager service resource
        result = rf_utils._find_managers_resource()
        if result['ret'] is False:
            module.fail_json(msg=to_native(result['msg']))

        for command in command_list:
            if command == "SetNetworkProtocols":
                result = rf_utils.set_network_protocols(module.params['network_protocols'])
            elif command == "SetManagerNic":
                result = rf_utils.set_manager_nic(nic_addr, nic_config)

    # Return data back or fail with proper message
    if result['ret'] is True:
        module.exit_json(changed=result['changed'], msg=to_native(result['msg']))
    else:
        module.fail_json(msg=to_native(result['msg']))


if __name__ == '__main__':
    main()
