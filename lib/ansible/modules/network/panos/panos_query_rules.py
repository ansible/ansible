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
module: panos_query_rules
short_description: PANOS module that allows search for security rules in PANW NGFW devices.
description: >
    - Security policies allow you to enforce rules and take action, and can be as general or specific as needed. The
    policy rules are compared against the incoming traffic in sequence, and because the first rule that matches the
    traffic is applied, the more specific rules must precede the more general ones.
author: "Bob Hagen (@rnh556)"
version_added: "2.5"
requirements:
    - pan-python can be obtained from PyPi U(https://pypi.org/project/pan-python/)
    - pandevice can be obtained from PyPi U(https://pypi.org/project/pandevice/)
    - xmltodict can be obtains from PyPi U(https://pypi.org/project/xmltodict/)
notes:
    - Checkmode is not supported.
    - Panorama is supported.
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS firewall or Panorama management console being queried.
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
    application:
        description:
            - Name of the application or application group to be queried.
    source_zone:
        description:
            - Name of the source security zone to be queried.
    source_ip:
        description:
            - The source IP address to be queried.
    source_port:
        description:
            - The source port to be queried.
    destination_zone:
        description:
            - Name of the destination security zone to be queried.
    destination_ip:
        description:
            - The destination IP address to be queried.
    destination_port:
        description:
            - The destination port to be queried.
    protocol:
        description:
            - The protocol used to be queried.  Must be either I(tcp) or I(udp).
    tag_name:
        description:
            - Name of the rule tag to be queried.
    devicegroup:
        description:
            - The Panorama device group in which to conduct the query.
'''

EXAMPLES = '''
- name: search for rules with tcp/3306
  panos_query_rules:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    source_zone: 'DevNet'
    destination_zone: 'DevVPC'
    destination_port: '3306'
    protocol: 'tcp'

- name: search devicegroup for inbound rules to dmz host
  panos_query_rules:
    ip_address: '{{ ip_address }}'
    api_key: '{{ api_key }}'
    destination_zone: 'DMZ'
    destination_ip: '10.100.42.18'
    address: 'DeviceGroupA'

- name: search for rules containing a specified rule tag
  panos_query_rules:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    tag_name: 'ProjectX'
'''

RETURN = '''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule

try:
    import pan.xapi
    from pan.xapi import PanXapiError
    import pandevice
    from pandevice import base
    from pandevice import firewall
    from pandevice import panorama
    from pandevice import objects
    from pandevice import policies
    import ipaddress
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


def get_rulebase(device, devicegroup):
    # Build the rulebase
    if isinstance(device, firewall.Firewall):
        rulebase = policies.Rulebase()
        device.add(rulebase)
    elif isinstance(device, panorama.Panorama):
        dg = panorama.DeviceGroup(devicegroup)
        device.add(dg)
        rulebase = policies.PreRulebase()
        dg.add(rulebase)
    else:
        return False
    policies.SecurityRule.refreshall(rulebase)
    return rulebase


def get_object(device, dev_group, obj_name):
    # Search global address objects
    match = device.find(obj_name, objects.AddressObject)
    if match:
        return match

    # Search global address groups
    match = device.find(obj_name, objects.AddressGroup)
    if match:
        return match

    # Search Panorama device group
    if isinstance(device, pandevice.panorama.Panorama):
        # Search device group address objects
        match = dev_group.find(obj_name, objects.AddressObject)
        if match:
            return match

        # Search device group address groups
        match = dev_group.find(obj_name, objects.AddressGroup)
        if match:
            return match
    return False


def addr_in_obj(addr, obj):
    ip = ipaddress.ip_address(addr)
    # Process address objects
    if isinstance(obj, objects.AddressObject):
        if obj.type == 'ip-netmask':
            net = ipaddress.ip_network(obj.value)
            if ip in net:
                return True
        if obj.type == 'ip-range':
            ip_range = obj.value.split('-')
            lower = ipaddress.ip_address(ip_range[0])
            upper = ipaddress.ip_address(ip_range[1])
            if lower < ip < upper:
                return True
    return False


def get_services(device, dev_group, svc_list, obj_list):
    for svc in svc_list:

        # Search global address objects
        global_obj_match = device.find(svc, objects.ServiceObject)
        if global_obj_match:
            obj_list.append(global_obj_match)

        # Search global address groups
        global_grp_match = device.find(svc, objects.ServiceGroup)
        if global_grp_match:
            get_services(device, dev_group, global_grp_match.value, obj_list)

        # Search Panorama device group
        if isinstance(device, pandevice.panorama.Panorama):

            # Search device group address objects
            dg_obj_match = dev_group.find(svc, objects.ServiceObject)
            if dg_obj_match:
                obj_list.append(dg_obj_match)

            # Search device group address groups
            dg_grp_match = dev_group.find(svc, objects.ServiceGroup)
            if dg_grp_match:
                get_services(device, dev_group, dg_grp_match.value, obj_list)

    return obj_list


def port_in_svc(orientation, port, protocol, obj):
    # Process address objects
    if orientation is 'source':
        for x in obj.source_port.split(','):
            if '-' in x:
                port_range = x.split('-')
                lower = int(port_range[0])
                upper = int(port_range[1])
                if (lower <= int(port) <= upper) and (obj.protocol == protocol):
                    return True
            else:
                if port == x and obj.protocol == protocol:
                    return True
    elif orientation is 'destination':
        for x in obj.destination_port.split(','):
            if '-' in x:
                port_range = x.split('-')
                lower = int(port_range[0])
                upper = int(port_range[1])
                if (lower <= int(port) <= upper) and (obj.protocol == protocol):
                    return True
            else:
                if port == x and obj.protocol == protocol:
                    return True
    return False


def get_tag(device, dev_group, tag_name):
    # Search global address objects
    match = device.find(tag_name, objects.Tag)
    if match:
        return match
    # Search Panorama device group
    if isinstance(device, panorama.Panorama):
        # Search device group address objects
        match = dev_group.find(tag_name, objects.Tag)
        if match:
            return match
    return False


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(no_log=True),
        username=dict(default='admin'),
        api_key=dict(no_log=True),
        application=dict(default=None),
        source_zone=dict(default=None),
        destination_zone=dict(default=None),
        source_ip=dict(default=None),
        destination_ip=dict(default=None),
        source_port=dict(default=None),
        destination_port=dict(default=None),
        protocol=dict(default=None, choices=['tcp', 'udp']),
        tag_name=dict(default=None),
        devicegroup=dict(default=None)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,
                           required_one_of=[['api_key', 'password']]
                           )
    if not HAS_LIB:
        module.fail_json(msg='Missing required libraries.')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']
    api_key = module.params['api_key']
    application = module.params['application']
    source_zone = module.params['source_zone']
    source_ip = module.params['source_ip']
    source_port = module.params['source_port']
    destination_zone = module.params['destination_zone']
    destination_ip = module.params['destination_ip']
    destination_port = module.params['destination_port']
    protocol = module.params['protocol']
    tag_name = module.params['tag_name']
    devicegroup = module.params['devicegroup']

    # Create the device with the appropriate pandevice type
    device = base.PanDevice.create_from_device(ip_address, username, password, api_key=api_key)

    # Grab the global objects
    objects.AddressObject.refreshall(device)
    objects.AddressGroup.refreshall(device)
    objects.ServiceObject.refreshall(device)
    objects.ServiceGroup.refreshall(device)
    objects.Tag.refreshall(device)

    # If Panorama, validate the devicegroup and grab the devicegroup objects
    dev_group = None
    if devicegroup and isinstance(device, panorama.Panorama):
        dev_group = get_devicegroup(device, devicegroup)
        if dev_group:
            device.add(dev_group)
            objects.AddressObject.refreshall(dev_group)
            objects.AddressGroup.refreshall(dev_group)
            objects.ServiceObject.refreshall(dev_group)
            objects.ServiceGroup.refreshall(dev_group)
            objects.Tag.refreshall(dev_group)
        else:
            module.fail_json(
                failed=1,
                msg='\'%s\' device group not found in Panorama. Is the name correct?' % devicegroup
            )

    # Build the rulebase and produce list
    rulebase = get_rulebase(device, dev_group)
    rulelist = rulebase.children
    hitbase = policies.Rulebase()
    loose_match = True

    # Process each rule
    for rule in rulelist:
        hitlist = []

        if source_zone:
            source_zone_match = False
            if loose_match and 'any' in rule.fromzone:
                source_zone_match = True
            else:
                for object_string in rule.fromzone:
                    if object_string == source_zone:
                        source_zone_match = True
            hitlist.append(source_zone_match)

        if destination_zone:
            destination_zone_match = False
            if loose_match and 'any' in rule.tozone:
                destination_zone_match = True
            else:
                for object_string in rule.tozone:
                    if object_string == destination_zone:
                        destination_zone_match = True
            hitlist.append(destination_zone_match)

        if source_ip:
            source_ip_match = False
            if loose_match and 'any' in rule.source:
                source_ip_match = True
            else:
                for object_string in rule.source:
                    # Get a valid AddressObject or AddressGroup
                    obj = get_object(device, dev_group, object_string)
                    # Otherwise the object_string is not an object and should be handled differently
                    if obj is False:
                        if '-' in object_string:
                            obj = ipaddress.ip_address(source_ip)
                            source_range = object_string.split('-')
                            source_lower = ipaddress.ip_address(source_range[0])
                            source_upper = ipaddress.ip_address(source_range[1])
                            if source_lower <= obj <= source_upper:
                                source_ip_match = True
                        else:
                            if source_ip == object_string:
                                source_ip_match = True
                    if isinstance(obj, objects.AddressObject) and addr_in_obj(source_ip, obj):
                        source_ip_match = True
                    elif isinstance(obj, objects.AddressGroup) and obj.static_value:
                        for member_string in obj.static_value:
                            member = get_object(device, dev_group, member_string)
                            if addr_in_obj(source_ip, member):
                                source_ip_match = True
            hitlist.append(source_ip_match)

        if destination_ip:
            destination_ip_match = False
            if loose_match and 'any' in rule.destination:
                destination_ip_match = True
            else:
                for object_string in rule.destination:
                    # Get a valid AddressObject or AddressGroup
                    obj = get_object(device, dev_group, object_string)
                    # Otherwise the object_string is not an object and should be handled differently
                    if obj is False:
                        if '-' in object_string:
                            obj = ipaddress.ip_address(destination_ip)
                            destination_range = object_string.split('-')
                            destination_lower = ipaddress.ip_address(destination_range[0])
                            destination_upper = ipaddress.ip_address(destination_range[1])
                            if destination_lower <= obj <= destination_upper:
                                destination_ip_match = True
                        else:
                            if destination_ip == object_string:
                                destination_ip_match = True
                    if isinstance(obj, objects.AddressObject) and addr_in_obj(destination_ip, obj):
                        destination_ip_match = True
                    elif isinstance(obj, objects.AddressGroup) and obj.static_value:
                        for member_string in obj.static_value:
                            member = get_object(device, dev_group, member_string)
                            if addr_in_obj(destination_ip, member):
                                destination_ip_match = True
            hitlist.append(destination_ip_match)

        if source_port:
            source_port_match = False
            orientation = 'source'
            if loose_match and (rule.service[0] == 'any'):
                source_port_match = True
            elif rule.service[0] == 'application-default':
                source_port_match = False  # Fix this once apps are supported
            else:
                service_list = []
                service_list = get_services(device, dev_group, rule.service, service_list)
                for obj in service_list:
                    if port_in_svc(orientation, source_port, protocol, obj):
                        source_port_match = True
                        break
            hitlist.append(source_port_match)

        if destination_port:
            destination_port_match = False
            orientation = 'destination'
            if loose_match and (rule.service[0] == 'any'):
                destination_port_match = True
            elif rule.service[0] == 'application-default':
                destination_port_match = False  # Fix this once apps are supported
            else:
                service_list = []
                service_list = get_services(device, dev_group, rule.service, service_list)
                for obj in service_list:
                    if port_in_svc(orientation, destination_port, protocol, obj):
                        destination_port_match = True
                        break
            hitlist.append(destination_port_match)

        if tag_name:
            tag_match = False
            if rule.tag:
                for object_string in rule.tag:
                    obj = get_tag(device, dev_group, object_string)
                    if obj and (obj.name == tag_name):
                        tag_match = True
            hitlist.append(tag_match)

        # Add to hit rulebase
        if False not in hitlist:
            hitbase.add(rule)

    # Dump the hit rulebase
    if hitbase.children:
        output_string = xmltodict.parse(hitbase.element_str())
        module.exit_json(
            stdout_lines=json.dumps(output_string, indent=2),
            msg='%s of %s rules matched' % (hitbase.children.__len__(), rulebase.children.__len__())
        )
    else:
        module.fail_json(msg='No matching rules found.')


if __name__ == '__main__':
    main()
