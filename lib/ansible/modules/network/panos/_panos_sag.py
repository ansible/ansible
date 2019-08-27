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

DOCUMENTATION = '''
---
module: panos_sag
short_description: Create a static address group.
description:
    - Create a static address group object in the firewall used for policy rules.
author: "Vinay Venkataraghavan (@vinayvenkat)"
version_added: "2.4"
requirements:
    - pan-python can be obtained from PyPI U(https://pypi.org/project/pan-python/)
    - pandevice can be obtained from PyPI U(https://pypi.org/project/pandevice/)
    - xmltodict can be obtained from PyPI U(https://pypi.org/project/xmltodict/)
deprecated:
    alternative: Use U(https://galaxy.ansible.com/PaloAltoNetworks/paloaltonetworks) instead.
    removed_in: "2.12"
    why: Consolidating code base.
options:
    api_key:
        description:
            - API key that can be used instead of I(username)/I(password) credentials.
    sag_name:
        description:
            - name of the dynamic address group
        required: true
    sag_match_filter:
        description:
            - Static filter user by the address group
        type: list
    devicegroup:
        description: >
            - The name of the Panorama device group. The group must exist on Panorama. If device group is not defined
            it is assumed that we are contacting a firewall.
    description:
        description:
            - The purpose / objective of the static Address Group
    tags:
        description:
            - Tags to be associated with the address group
    commit:
        description:
            - commit if changed
        type: bool
        default: 'yes'
    operation:
        description:
            - The operation to perform Supported values are I(add)/I(list)/I(delete).
        required: true
        choices:
            - add
            - list
            - delete
extends_documentation_fragment: panos
'''

EXAMPLES = '''
- name: sag
  panos_sag:
    ip_address: "192.168.1.1"
    password: "admin"
    sag_name: "sag-1"
    static_value: ['test-addresses', ]
    description: "A description for the static address group"
    tags: ["tags to be associated with the group", ]
'''

RETURN = '''
# Default return values
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

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


def find_object(device, dev_group, obj_name, obj_type):
    # Get the firewall objects
    obj_type.refreshall(device)
    if isinstance(device, firewall.Firewall):
        addr = device.find(obj_name, obj_type)
        return addr
    elif isinstance(device, panorama.Panorama):
        addr = device.find(obj_name, obj_type)
        if addr is None:
            if dev_group:
                device.add(dev_group)
                obj_type.refreshall(dev_group)
                addr = dev_group.find(obj_name, obj_type)
        return addr
    else:
        return False


def create_address_group_object(**kwargs):
    """
    Create an Address object

    :param kwargs: key word arguments to instantiate AddressGroup object
    @return False or ```objects.AddressObject```
    """
    ad_object = objects.AddressGroup(
        name=kwargs['address_gp_name'],
        static_value=kwargs['sag_match_filter'],
        description=kwargs['description'],
        tag=kwargs['tag_name']
    )
    if ad_object.static_value or ad_object.dynamic_value:
        return ad_object
    else:
        return None


def add_address_group(device, dev_group, ag_object):
    """
    Create a new dynamic address group object on the
    PAN FW.

    :param device: Firewall Handle
    :param dev_group: Panorama device group
    :param ag_object: Address group object
    """

    if dev_group:
        dev_group.add(ag_object)
    else:
        device.add(ag_object)

    exc = None
    try:
        ag_object.create()
    except Exception as exc:
        return False, exc

    return True, exc


def delete_address_group(device, dev_group, obj_name):
    """

    :param device:
    :param dev_group:
    :param obj_name:
    :return:
    """
    static_obj = find_object(device, dev_group, obj_name, objects.AddressGroup)
    # If found, delete it

    if static_obj:
        try:
            static_obj.delete()
        except Exception as exc:
            return False, exc
        return True, None
    else:
        return False, None


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True),
        username=dict(default='admin'),
        api_key=dict(no_log=True),
        sag_match_filter=dict(type='list', required=False),
        sag_name=dict(required=True),
        commit=dict(type='bool', default=True),
        devicegroup=dict(default=None),
        description=dict(default=None),
        tags=dict(type='list', default=[]),
        operation=dict(type='str', required=True, choices=['add', 'list', 'delete'])
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,
                           required_one_of=[['api_key', 'password']])
    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']
    api_key = module.params['api_key']
    operation = module.params['operation']

    ag_object = create_address_group_object(address_gp_name=module.params.get('sag_name', None),
                                            sag_match_filter=module.params.get('sag_match_filter', None),
                                            description=module.params.get('description', None),
                                            tag_name=module.params.get('tags', None)
                                            )
    commit = module.params['commit']

    devicegroup = module.params['devicegroup']
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

    if operation == 'add':
        result, exc = add_address_group(device, dev_group, ag_object)

        if result and commit:
            try:
                device.commit(sync=True)
            except Exception as exc:
                module.fail_json(msg=to_native(exc))

    elif operation == 'delete':
        obj_name = module.params.get('sag_name', None)
        result, exc = delete_address_group(device, dev_group, obj_name)
        if not result and exc:
            module.fail_json(msg=exc.message)
        elif not result:
            module.fail_json(msg="Specified object not found.")
    else:
        module.fail_json(changed=False, msg="Unsupported option.")

    module.exit_json(changed=True, msg="Address Group Operation Completed.")


if __name__ == '__main__':
    main()
