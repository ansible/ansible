#!/usr/bin/python
# (c) 2016, Tomas Karasek <tom.to.the.k@gmail.com>
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

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: packet_ip_subnet

short_description: Assign IP subnet to a bare metal server.

description:
    - Assign or unassign IPv4 or IPv6 subnets to or from a device in the Packet host.
    - IPv4 subnets must come from already reserved block.
    - IPv6 subnets must come from publicly routable /56 block from your project.
    - See U(https://help.packet.net/technical/networking/how-do-i-configure-additional-elastic-ips-on-my-server) for more info on IP block reservation.

version_added: 2.5

author: Tomas Karasek <tom.to.the.k@gmail.com>

options:
  auth_token:
    description:
      - Packet api token. You can also supply it in env var C(PACKET_API_TOKEN).
  hostname:
    description:
      - A hostname of a device to/from which to assing/remove a subnet.
    required: False
  device_id:
    description:
      - UUID of a device to/from which to assing/remove a subnet.
    required: False
  cidr:
    description:
      - IPv4 or IPv6 subnet which you want to manage. It must come from a reserved block for your project in the Packet Host.
    aliases: [name]
  state:
    description:
      - Desired state of the IP subnet on the specified device.
      - With state == C(present), you must specify either hostname or device_id. Subnet with given CIDR will then be assigned to the specified device.
      - With state == C(absent), you can specify either hostname or device_id. The subnet will be removed from specified devices.
      - If you leave both hostname and device_id empty, the subnet will be removed from any device it's assigned to.
    choices: [present, absent]
    default: 'present'

requirements:
     - "packet-python >= 1.35"
     - "python >= 2.6"
'''

EXAMPLES = '''
# All the examples assume that you have your Packet api token in env var PACKET_API_TOKEN.
# You can also pass it to the auth_token parameter of the module instead.

- name: create 1 device and assign an arbitrary public IPv4 subnet to it
  hosts: localhost
  tasks:

  - packet_device:
      project_id: 89b497ee-5afc-420a-8fb5-56984898f4df
      hostnames: myserver
      operating_system: ubuntu_16_04
      plan: baremetal_0
      facility: sjc1
      state: active

# Pick an IPv4 address from a block allocated to your project.

  - packet_ip_subnet:
      project_id: 89b497ee-5afc-420a-8fb5-56984898f4df
      hostname: myserver
      cidr: "147.75.201.78/32"

# Release IP address 147.75.201.78

- name: unassign IP address from any device in your project
  hosts: localhost
  tasks:
  - packet_ip_subnet:
      project_id: 89b497ee-5afc-420a-8fb5-56984898f4df
      cidr: "147.75.201.78/32"
      state: absent
'''

RETURN = '''
changed:
  description: True if an IP address assignments were altered in any way (created or removed).
  type: bool
  sample: True
  returned: success
device_id:
  type: string
  description: UUID of the device associated with the specified IP address.
  returned: success
subnet:
  description: Dict with data about the handled IP subnet.
  type: dictionary
  sample:
    address: 147.75.90.241
    address_family: 4
    assigned_to: { href : /devices/61f9aa5e-0530-47f5-97c2-113828e61ed0 }
    cidr: 31
    created_at: '2017-08-07T15:15:30Z'
    enabled: True
    gateway: 147.75.90.240
    href: /ips/31eda960-0a16-4c0f-b196-f3dc4928529f
    id: 1eda960-0a16-4c0f-b196-f3dc4928529f
    manageable: True
    management: True
    netmask: 255.255.255.254
    network: 147.75.90.240
    public: True
  returned: success
'''


import os
import time
import uuid
import re

from ansible.module_utils.basic import AnsibleModule

HAS_PACKET_SDK = True

try:
    import packet
except ImportError:
    HAS_PACKET_SDK = False


NAME_RE = '({0}|{0}{1}*{0})'.format('[a-zA-Z0-9]', '[a-zA-Z0-9\-]')
HOSTNAME_RE = '({0}\.)*{0}$'.format(NAME_RE)
MAX_DEVICES = 100


PACKET_API_TOKEN_ENV_VAR = "PACKET_API_TOKEN"


ALLOWED_STATES = ['absent', 'present']


def is_valid_hostname(hostname):
    return re.match(HOSTNAME_RE, hostname) is not None


def is_valid_uuid(myuuid):
    try:
        val = uuid.UUID(myuuid, version=4)
    except ValueError:
        return False
    return str(val) == myuuid


def get_existing_devices(module, packet_conn):
    project_id = module.params.get('project_id')
    return packet_conn.list_devices(
        project_id, params={'per_page': MAX_DEVICES})


def get_specified_device_identifiers(module):
    if module.params.get('device_id'):
        _d_id = module.params.get('device_id')
        if not is_valid_uuid(_d_id):
            raise Exception("Device ID '%s' does not seem to be valid" % _d_id)
        return {'device_id': _d_id, 'hostname': None}
    elif module.params.get('hostname'):
        _hn = module.params.get('hostname')
        if not is_valid_hostname(_hn):
            raise Exception("Hostname '%s' does not seem to be valid" % _hn)
        return {'hostname': _hn, 'device_id': None}
    else:
        return {'hostname': None, 'device_id': None}


def parse_subnet_cidr(cidr):
    if "/" not in cidr:
        raise Exception("CIDR expression in wrong format, must be address/prefix_len")
    addr, prefixlen = cidr.split("/")
    try:
        prefixlen = int(prefixlen)
    except ValueError:
        raise("Wrong prefix length in CIDR expression %s" % cidr)
    return addr, prefixlen


def act_on_assignment(target_state, module, packet_conn):
    return_dict = {'changed': False}
    subnet_address, subnet_prefix = module.params.get("cidr").split("/")

    specified_cidr = module.params.get("cidr")
    address, prefixlen = parse_subnet_cidr(specified_cidr)
    project_id = module.params.get('project_id')
    if not is_valid_uuid(project_id):
        raise Exception("Project ID %s does not seem to be valid" % project_id)

    specified_identifier = get_specified_device_identifiers(module)

    if (specified_identifier['hostname'] is None) and (
            specified_identifier['device_id'] is None):
        if target_state == 'absent':
            # The special case to release the IP from any assignment
            for d in get_existing_devices(module, packet_conn):
                for ia in d.ip_addresses:
                    if address == ia['address'] and prefixlen == ia['cidr']:
                        packet_conn.call_api(ia['href'], "DELETE")
                        return_dict['changed'] = True
                        return_dict['subnet'] = ia
                        return_dict['device_id'] = d.id
                        return return_dict
        raise Exception("If you assign an address, you must specify either "
                        "target device ID or target unique hostname.")
    if specified_identifier['device_id'] is not None:
        device = packet_conn.get_device(specified_identifier['device_id'])
    else:
        all_devices = get_existing_devices(module, packet_conn)
        hn = specified_identifier['hostname']
        matching_devices = [d for d in all_devices if d.hostname == hn]
        if len(matching_devices) > 1:
            raise Exception(
                "There are more than one devices matching given hostname %s" %
                hn)
        if len(matching_devices) == 0:
            raise Exception(
                "There is no device matching given hostname %s" %
                hn)
        device = matching_devices[0]
    return_dict['device_id'] = device.id
    assignment_dicts = [i for i in device.ip_addresses
                        if i['address'] == address and i['cidr'] == prefixlen]
    if len(assignment_dicts) > 1:
        raise Exception("IP address %s is assigned more than once for device %s"
                        % (specified_cidr, device.hostname))
    if target_state == "absent":
        if len(assignment_dicts) == 1:
            packet_conn.call_api(assignment_dicts[0]['href'], "DELETE")
            return_dict['subnet'] = assignment_dicts[0]
            return_dict['changed'] = True
    elif target_state == "present":
        if len(assignment_dicts) == 0:
            new_assignment = packet_conn.call_api("devices/%s/ips" %
                                                  device.id, "POST", {"address": "%s" % specified_cidr})
            return_dict['changed'] = True
            return_dict['subnet'] = new_assignment
    return return_dict


def main():
    module = AnsibleModule(
        argument_spec=dict(
            auth_token=dict(default=os.environ.get(PACKET_API_TOKEN_ENV_VAR),
                            no_log=True),
            device_id=dict(),
            hostname=dict(),
            project_id=dict(required=True),
            cidr=dict(required=True, aliases=['name']),
            state=dict(choices=ALLOWED_STATES, default='present'),
        ),
        mutually_exclusive=[('hostname', 'device_id')]
    )

    if not HAS_PACKET_SDK:
        module.fail_json(msg='packet required for this module')

    if not module.params.get('auth_token'):
        _fail_msg = ("if Packet API token is not in environment variable %s, "
                     "the auth_token parameter is required" %
                     PACKET_API_TOKEN_ENV_VAR)
        module.fail_json(msg=_fail_msg)

    auth_token = module.params.get('auth_token')

    packet_conn = packet.Manager(auth_token=auth_token)

    state = module.params.get('state')

    try:
        module.exit_json(**act_on_assignment(state, module, packet_conn))
    except Exception as e:
        module.fail_json(
            msg='failed to put subnet to state %s, error: %s' %
            (state, str(e)))


if __name__ == '__main__':
    main()
