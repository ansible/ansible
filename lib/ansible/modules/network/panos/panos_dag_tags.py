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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: panos_dag_tags
short_description: Create tags for DAG's on PAN-OS devices.
description:
    - Create the ip address to tag associations. Tags will in turn be used to create DAG's
author: "Vinay Venkataraghavan @vinayvenkat"
version_added: "2.4"
requirements:
    - pan-python
    - pan-device
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device
        required: true
        default: null
    password:
        description:
            - password for authentication
        required: true
        default: null
    api_key:
        description:
            - API key that can be used instead of I(username)/I(password) credentials.
    username:
        description:
            - username for authentication
        required: false
        default: "admin"
    description:
        description:
            - The purpose / objective of the static Address Group
        required: false
        default: null
    commit:
        description:
            - commit if changed
        required: false
        default: true
'''

EXAMPLES = '''
- name: Create the tags to map IP addresses
  panos_dag_tags:
    ip_address: "{{ mgmt_ip }}"
    password: "{{ admin_password }}"
    ip_to_register: "{{ ip_to_register }}"
    tag_names: "{{ tag_names }}"
    description: "Tags to allow certain IP's to access various SaaS Applications"
    operation: 'add'
  tags: "add-dagip"

- name: List the IP address to tag mapping
  panos_dag_tags:
    ip_address: "{{ mgmt_ip }}"
    password: "{{ admin_password }}"
    tag_names: "{{ tag_names }}"
    description: "List the IP address to tag mapping"
    operation: 'list'
  tags: "list-dagip"

- name: Unregister an IP address from a tag mapping
  panos_dag_tags:
    ip_address: "{{ mgmt_ip }}"
    password: "{{ admin_password }}"
    ip_to_register: "{{ ip_to_register }}"
    tag_names: "{{ tag_names }}"
    description: "Unregister IP address from tag mappings"
    operation: 'delete'
  tags: "delete-dagip"
'''

RETURN = '''
# Default return values
'''


from ansible.module_utils.basic import AnsibleModule, get_exception

try:
    from pandevice import base
    from pandevice import firewall
    from pandevice import panorama
    from pandevice import objects

    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def get_devicegroup(device, devicegroup):
    dg_list = device.refresh_devices()
    for group in dg_list:
        if isinstance(group, panorama.DeviceGroup):
            if group.name == devicegroup:
                return group
    return False


def register_ip_to_tag_map(device, ip_addresses, tag):
    """
    :param device:
    :param ip_addresses:
    :param tag:
    :return:
    """

    exc = None
    try:
        device.userid.register(ip_addresses, tag)
    except Exception:
        exc = get_exception()
        return False, exc

    if exc:
        return False, exc
    else:
        return True, exc


def get_all_address_group_mapping(device):
    """
    Retrieve all the tag to IP address mappings
    :param device:
    :return:
    """

    exc = None
    ret = None
    try:
        ret = device.userid.get_registered_ip()
    except Exception:
        exc = get_exception()

    if exc:
        return False, exc
    else:
        return ret, exc


def delete_address_from_mapping(device, ip_address, tags):
    """
    Delete an IP address from a tag mapping.
    :param device:
    :param ip_address:
    :param tags:
    :return:
    """

    exc = None
    try:
        ret = device.userid.unregister(ip_address, tags)
    except Exception:
        exc = get_exception()

    if exc:
        return False, exc
    else:
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

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,
                           required_one_of=[['api_key', 'password']])
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
            module.fail_json(msg="'%s' device group not found in Panorama. Is the name correct?" % devicegroup)

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
        module.fail_json(msg=exc)

    if commit:
        try:
            device.commit(sync=True)
        except Exception:
            exc = get_exception()
            module.fail_json(msg=exc)

    module.exit_json(changed=True, msg=result)


if __name__ == "__main__":
    main()
