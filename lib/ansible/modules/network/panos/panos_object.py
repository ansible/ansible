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
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: panos_object
short_description: create/read/update/delete object in PAN-OS or Panorama
description:
    - Policy objects form the match criteria for policy rules and many other functions in PAN-OS. These may include
      address object, address groups, service objects, service groups, and tag.
author: "Bob Hagen (@rnh556)"
version_added: "2.4"
requirements:
    - pan-python can be obtained from PyPi U(https://pypi.org/project/pan-python/)
    - pandevice can be obtained from PyPi U(https://pypi.org/project/pandevice/)
notes:
    - Checkmode is not supported.
    - Panorama is supported.
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device or Panorama management console being configured.
        required: true
    username:
        description:
            - Username credentials to use for authentication.
        default: "admin"
    password:
        description:
            - Password credentials to use for authentication.
        required: true
    api_key:
        description:
            - API key that can be used instead of I(username)/I(password) credentials.
    operation:
        description:
            - The operation to be performed.  Supported values are I(add)/I(delete)/I(find).
        required: true
    addressobject:
        description:
            - The name of the address object.
    address:
        description:
            - The IP address of the host or network in CIDR notation.
    address_type:
        description:
            - The type of address object definition.  Valid types are I(ip-netmask) and I(ip-range).
    addressgroup:
        description:
            - A static group of address objects or dynamic address group.
    static_value:
        description:
            - A group of address objects to be used in an addressgroup definition.
    dynamic_value:
        description:
            - The filter match criteria to be used in a dynamic addressgroup definition.
    serviceobject:
        description:
            - The name of the service object.
    source_port:
        description:
            - The source port to be used in a service object definition.
    destination_port:
        description:
            - The destination port to be used in a service object definition.
    protocol:
        description:
            - The IP protocol to be used in a service object definition.  Valid values are I(tcp) or I(udp).
    servicegroup:
        description:
            - A group of service objects.
    services:
        description:
            - The group of service objects used in a servicegroup definition.
    description:
        description:
            - The description of the object.
    tag_name:
        description:
            - The name of an object or rule tag.
    color:
        description: >
            - The color of the tag object.  Valid values are I(red, green, blue, yellow, copper, orange, purple, gray,
            light green, cyan, light gray, blue gray, lime, black, gold, and brown).
    devicegroup:
        description: >
            - The name of the Panorama device group. The group must exist on Panorama. If device group is not defined it
            is assumed that we are contacting a firewall.
'''

EXAMPLES = '''
- name: search for shared address object
  panos_object:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    operation: 'find'
    address: 'DevNet'

- name: create an address group in devicegroup using API key
  panos_object:
    ip_address: '{{ ip_address }}'
    api_key: '{{ api_key }}'
    operation: 'add'
    addressgroup: 'Prod_DB_Svrs'
    static_value: ['prod-db1', 'prod-db2', 'prod-db3']
    description: 'Production DMZ database servers'
    tag_name: 'DMZ'
    devicegroup: 'DMZ Firewalls'

- name: create a global service for TCP 3306
  panos_object:
    ip_address: '{{ ip_address }}'
    api_key: '{{ api_key }}'
    operation: 'add'
    serviceobject: 'mysql-3306'
    destination_port: '3306'
    protocol: 'tcp'
    description: 'MySQL on tcp/3306'

- name: create a global tag
  panos_object:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    operation: 'add'
    tag_name: 'ProjectX'
    color: 'yellow'
    description: 'Associated with Project X'

- name: delete an address object from a devicegroup using API key
  panos_object:
    ip_address: '{{ ip_address }}'
    api_key: '{{ api_key }}'
    operation: 'delete'
    addressobject: 'Win2K test'
'''

RETURN = '''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

try:
    import pan.xapi
    from pan.xapi import PanXapiError
    import pandevice
    from pandevice import base
    from pandevice import firewall
    from pandevice import panorama
    from pandevice import objects
    import xmltodict
    import json

    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def get_devicegroup(device, devicegroup):
    dg_list = device.refresh_devices()
    for group in dg_list:
        if isinstance(group, pandevice.panorama.DeviceGroup):
            if group.name == devicegroup:
                return group
    return False


def find_object(device, dev_group, obj_name, obj_type):
    # Get the firewall objects
    obj_type.refreshall(device)
    if isinstance(device, pandevice.firewall.Firewall):
        addr = device.find(obj_name, obj_type)
        return addr
    elif isinstance(device, pandevice.panorama.Panorama):
        addr = device.find(obj_name, obj_type)
        if addr is None:
            if dev_group:
                device.add(dev_group)
                obj_type.refreshall(dev_group)
                addr = dev_group.find(obj_name, obj_type)
        return addr
    else:
        return False


def create_object(**kwargs):
    if kwargs['addressobject']:
        newobject = objects.AddressObject(
            name=kwargs['addressobject'],
            value=kwargs['address'],
            type=kwargs['address_type'],
            description=kwargs['description'],
            tag=kwargs['tag_name']
        )
        if newobject.type and newobject.value:
            return newobject
        else:
            return False
    elif kwargs['addressgroup']:
        newobject = objects.AddressGroup(
            name=kwargs['addressgroup'],
            static_value=kwargs['static_value'],
            dynamic_value=kwargs['dynamic_value'],
            description=kwargs['description'],
            tag=kwargs['tag_name']
        )
        if newobject.static_value or newobject.dynamic_value:
            return newobject
        else:
            return False
    elif kwargs['serviceobject']:
        newobject = objects.ServiceObject(
            name=kwargs['serviceobject'],
            protocol=kwargs['protocol'],
            source_port=kwargs['source_port'],
            destination_port=kwargs['destination_port'],
            tag=kwargs['tag_name']
        )
        if newobject.protocol and newobject.destination_port:
            return newobject
        else:
            return False
    elif kwargs['servicegroup']:
        newobject = objects.ServiceGroup(
            name=kwargs['servicegroup'],
            value=kwargs['services'],
            tag=kwargs['tag_name']
        )
        if newobject.value:
            return newobject
        else:
            return False
    elif kwargs['tag_name']:
        newobject = objects.Tag(
            name=kwargs['tag_name'],
            color=kwargs['color'],
            comments=kwargs['description']
        )
        if newobject.name:
            return newobject
        else:
            return False
    else:
        return False


def add_object(device, dev_group, new_object):
    if dev_group:
        dev_group.add(new_object)
    else:
        device.add(new_object)
    new_object.create()
    return True


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(no_log=True),
        username=dict(default='admin'),
        api_key=dict(no_log=True),
        operation=dict(required=True, choices=['add', 'update', 'delete', 'find']),
        addressobject=dict(default=None),
        addressgroup=dict(default=None),
        serviceobject=dict(default=None),
        servicegroup=dict(default=None),
        address=dict(default=None),
        address_type=dict(default='ip-netmask', choices=['ip-netmask', 'ip-range', 'fqdn']),
        static_value=dict(type='list', default=None),
        dynamic_value=dict(default=None),
        protocol=dict(default=None, choices=['tcp', 'udp']),
        source_port=dict(default=None),
        destination_port=dict(default=None),
        services=dict(type='list', default=None),
        description=dict(default=None),
        tag_name=dict(default=None),
        color=dict(default=None, choices=['red', 'green', 'blue', 'yellow', 'copper', 'orange', 'purple',
                                          'gray', 'light green', 'cyan', 'light gray', 'blue gray',
                                          'lime', 'black', 'gold', 'brown']),
        devicegroup=dict(default=None)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,
                           required_one_of=[['api_key', 'password']],
                           mutually_exclusive=[['addressobject', 'addressgroup',
                                                'serviceobject', 'servicegroup',
                                                'tag_name']]
                           )
    if not HAS_LIB:
        module.fail_json(msg='Missing required libraries.')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']
    api_key = module.params['api_key']
    operation = module.params['operation']
    addressobject = module.params['addressobject']
    addressgroup = module.params['addressgroup']
    serviceobject = module.params['serviceobject']
    servicegroup = module.params['servicegroup']
    address = module.params['address']
    address_type = module.params['address_type']
    static_value = module.params['static_value']
    dynamic_value = module.params['dynamic_value']
    protocol = module.params['protocol']
    source_port = module.params['source_port']
    destination_port = module.params['destination_port']
    services = module.params['services']
    description = module.params['description']
    tag_name = module.params['tag_name']
    color = module.params['color']
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

    # What type of object are we talking about?
    if addressobject:
        obj_name = addressobject
        obj_type = objects.AddressObject
    elif addressgroup:
        obj_name = addressgroup
        obj_type = objects.AddressGroup
    elif serviceobject:
        obj_name = serviceobject
        obj_type = objects.ServiceObject
    elif servicegroup:
        obj_name = servicegroup
        obj_type = objects.ServiceGroup
    elif tag_name:
        obj_name = tag_name
        obj_type = objects.Tag
    else:
        module.fail_json(msg='No object type defined!')

    # Which operation shall we perform on the object?
    if operation == "find":
        # Search for the object
        match = find_object(device, dev_group, obj_name, obj_type)

        # If found, format and return the result
        if match:
            match_dict = xmltodict.parse(match.element_str())
            module.exit_json(
                stdout_lines=json.dumps(match_dict, indent=2),
                msg='Object matched'
            )
        else:
            module.fail_json(msg='Object \'%s\' not found. Is the name correct?' % obj_name)
    elif operation == "delete":
        # Search for the object
        match = find_object(device, dev_group, obj_name, obj_type)

        # If found, delete it
        if match:
            try:
                match.delete()
            except PanXapiError as exc:
                module.fail_json(msg=to_native(exc))

            module.exit_json(changed=True, msg='Object \'%s\' successfully deleted' % obj_name)
        else:
            module.fail_json(msg='Object \'%s\' not found. Is the name correct?' % obj_name)
    elif operation == "add":
        # Search for the object. Fail if found.
        match = find_object(device, dev_group, obj_name, obj_type)
        if match:
            module.fail_json(msg='Object \'%s\' already exists. Use operation: \'update\' to change it.' % obj_name)
        else:
            try:
                new_object = create_object(
                    addressobject=addressobject,
                    addressgroup=addressgroup,
                    serviceobject=serviceobject,
                    servicegroup=servicegroup,
                    address=address,
                    address_type=address_type,
                    static_value=static_value,
                    dynamic_value=dynamic_value,
                    protocol=protocol,
                    source_port=source_port,
                    destination_port=destination_port,
                    services=services,
                    description=description,
                    tag_name=tag_name,
                    color=color
                )
                changed = add_object(device, dev_group, new_object)
            except PanXapiError as exc:
                module.fail_json(msg=to_native(exc))
        module.exit_json(changed=changed, msg='Object \'%s\' successfully added' % obj_name)
    elif operation == "update":
        # Search for the object. Update if found.
        match = find_object(device, dev_group, obj_name, obj_type)
        if match:
            try:
                new_object = create_object(
                    addressobject=addressobject,
                    addressgroup=addressgroup,
                    serviceobject=serviceobject,
                    servicegroup=servicegroup,
                    address=address,
                    address_type=address_type,
                    static_value=static_value,
                    dynamic_value=dynamic_value,
                    protocol=protocol,
                    source_port=source_port,
                    destination_port=destination_port,
                    services=services,
                    description=description,
                    tag_name=tag_name,
                    color=color
                )
                changed = add_object(device, dev_group, new_object)
            except PanXapiError as exc:
                module.fail_json(msg=to_native(exc))
            module.exit_json(changed=changed, msg='Object \'%s\' successfully updated.' % obj_name)
        else:
            module.fail_json(msg='Object \'%s\' does not exist. Use operation: \'add\' to add it.' % obj_name)


if __name__ == '__main__':
    main()
