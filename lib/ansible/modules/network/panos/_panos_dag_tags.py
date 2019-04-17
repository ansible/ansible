#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#  limitations under the License.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: panos_dag_tags
short_description: Create tags for DAG's on PAN-OS devices.
description:
    - Create the ip address to tag associations. Tags will in turn be used to create DAG's
author: "Vinay Venkataraghavan (@vinayvenkat)"
version_added: "2.5"
requirements:
    - pan-python can be obtained from PyPI U(https://pypi.org/project/pan-python/)
    - pandevice can be obtained from PyPI U(https://pypi.org/project/pandevice/)
deprecated:
    alternative: Use U(https://galaxy.ansible.com/PaloAltoNetworks/paloaltonetworks) instead.
    removed_in: "2.12"
    why: Consolidating code base.
notes:
    - Checkmode is not supported.
    - Panorama is not supported.
options:
    api_key:
        description:
            - API key that can be used instead of I(username)/I(password) credentials.
    description:
        description:
            - The purpose / objective of the static Address Group
    commit:
        description:
            - commit if changed
        default: true
        type: bool
    devicegroup:
        description: >
            - Device groups are used for the Panorama interaction with Firewall(s). The group must exists on Panorama.
            If device group is not define we assume that we are contacting Firewall.
    operation:
        description:
            - The action to be taken. Supported values are I(add)/I(update)/I(find)/I(delete).
    tag_names:
        description:
            - The list of the tags that will be added or removed from the IP address.
    ip_to_register:
        description:
            - IP that will be registered with the given tag names.
extends_documentation_fragment: panos
'''

EXAMPLES = '''
- name: Create the tags to map IP addresses
  panos_dag_tags:
    ip_address: "{{ ip_address }}"
    password: "{{ password }}"
    ip_to_register: "{{ ip_to_register }}"
    tag_names: "{{ tag_names }}"
    description: "Tags to allow certain IP's to access various SaaS Applications"
    operation: 'add'
  tags: "adddagip"

- name: List the IP address to tag mapping
  panos_dag_tags:
    ip_address: "{{ ip_address }}"
    password: "{{ password }}"
    tag_names: "{{ tag_names }}"
    description: "List the IP address to tag mapping"
    operation: 'list'
  tags: "listdagip"

- name: Unregister an IP address from a tag mapping
  panos_dag_tags:
    ip_address: "{{ ip_address }}"
    password: "{{ password }}"
    ip_to_register: "{{ ip_to_register }}"
    tag_names: "{{ tag_names }}"
    description: "Unregister IP address from tag mappings"
    operation: 'delete'
  tags: "deletedagip"
'''

RETURN = '''
# Default return values
'''

try:
    from pandevice import base
    from pandevice import firewall
    from pandevice import panorama
    from pandevice import objects

    from pan.xapi import PanXapiError

    HAS_LIB = True
except ImportError:
    HAS_LIB = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def get_devicegroup(device, devicegroup):
    dg_list = device.refresh_devices()
    for group in dg_list:
        if isinstance(group, panorama.DeviceGroup):
            if group.name == devicegroup:
                return group
    return False


def register_ip_to_tag_map(device, ip_addresses, tag):
    exc = None
    try:
        device.userid.register(ip_addresses, tag)
    except PanXapiError as exc:
        return False, exc

    return True, exc


def get_all_address_group_mapping(device):
    exc = None
    ret = None
    try:
        ret = device.userid.get_registered_ip()
    except PanXapiError as exc:
        return False, exc

    return ret, exc


def delete_address_from_mapping(device, ip_address, tags):
    exc = None
    try:
        ret = device.userid.unregister(ip_address, tags)
    except PanXapiError as exc:
        return False, exc

    return True, exc


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        api_key=dict(no_log=True),
        devicegroup=dict(default=None),
        description=dict(default=None),
        ip_to_register=dict(type='str', required=False),
        tag_names=dict(type='list', required=True),
        commit=dict(type='bool', default=True),
        operation=dict(type='str', required=True)
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']
    api_key = module.params['api_key']
    commit = module.params['commit']
    devicegroup = module.params['devicegroup']
    operation = module.params['operation']

    # Create the device with the appropriate pandevice type
    device = base.PanDevice.create_from_device(ip_address, username, password, api_key=api_key)

    # If Panorama, validate the devicegroup
    dev_group = None
    if devicegroup and isinstance(device, panorama.Panorama):
        dev_group = get_devicegroup(device, devicegroup)
        if dev_group:
            device.add(dev_group)
        else:
            module.fail_json(msg='\'%s\' device group not found in Panorama. Is the name correct?' % devicegroup)

    result = None
    if operation == 'add':
        result, exc = register_ip_to_tag_map(device,
                                             ip_addresses=module.params.get('ip_to_register', None),
                                             tag=module.params.get('tag_names', None)
                                             )
    elif operation == 'list':
        result, exc = get_all_address_group_mapping(device)
    elif operation == 'delete':
        result, exc = delete_address_from_mapping(device,
                                                  ip_address=module.params.get('ip_to_register', None),
                                                  tags=module.params.get('tag_names', [])
                                                  )
    else:
        module.fail_json(msg="Unsupported option")

    if not result:
        module.fail_json(msg=exc.message)

    if commit:
        try:
            device.commit(sync=True)
        except PanXapiError as exc:
            module.fail_json(msg=to_native(exc))

    module.exit_json(changed=True, msg=result)


if __name__ == "__main__":
    main()
