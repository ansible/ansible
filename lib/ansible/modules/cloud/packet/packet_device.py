#!/usr/bin/python
# (c) 2016, Tomas Karasek <tom.to.the.k@gmail.com>
# (c) 2016, Matt Baldwin <baldwin@stackpointcloud.com>
# (c) 2016, Thibaud Morel l'Horset <teebes@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: packet_device

short_description: Manage a bare metal server in the Packet Host.

description:
    - Manage a bare metal server in the Packet Host (a "device" in the API terms).
    - When the machine is created it can optionally wait for public IP address, or for active state.
    - This module has a dependency on packet >= 1.0.
    - API is documented at U(https://www.packet.net/developers/api/devices).

version_added: "2.3"

author:
    - Tomas Karasek (@t0mk) <tom.to.the.k@gmail.com>
    - Matt Baldwin (@baldwinSPC) <baldwin@stackpointcloud.com>
    - Thibaud Morel l'Horset (@teebes) <teebes@gmail.com>

options:
  auth_token:
    description:
      - Packet api token. You can also supply it in env var C(PACKET_API_TOKEN).

  count:
    description:
      - The number of devices to create. Count number can be included in hostname via the %d string formatter.
    default: 1

  count_offset:
    description:
      - From which number to start the count.
    default: 1

  device_ids:
    description:
      - List of device IDs on which to operate.

  facility:
    description:
      - Facility slug for device creation. See Packet API for current list - U(https://www.packet.net/developers/api/facilities/).

  features:
    description:
      - Dict with "features" for device creation. See Packet API docs for details.

  hostnames:
    description:
      - A hostname of a device, or a list of hostnames.
      - If given string or one-item list, you can use the C("%d") Python string format to expand numbers from I(count).
      - If only one hostname, it might be expanded to list if I(count)>1.
    aliases: [name]

  locked:
    description:
      - Whether to lock a created device.
    default: false
    version_added: "2.4"
    aliases: [lock]
    type: bool

  operating_system:
    description:
      - OS slug for device creation. See Packet API for current list - U(https://www.packet.net/developers/api/operatingsystems/).

  plan:
    description:
      - Plan slug for device creation. See Packet API for current list - U(https://www.packet.net/developers/api/plans/).

  project_id:
    description:
      - ID of project of the device.
    required: true

  state:
    description:
      - Desired state of the device.
      - If set to C(present) (the default), the module call will return immediately after the device-creating HTTP request successfully returns.
      - If set to C(active), the module call will block until all the specified devices are in state active due to the Packet API, or until I(wait_timeout).
    choices: [present, absent, active, inactive, rebooted]
    default: present

  user_data:
    description:
      - Userdata blob made available to the machine

  wait_for_public_IPv:
    description:
      - Whether to wait for the instance to be assigned a public IPv4/IPv6 address.
      - If set to 4, it will wait until IPv4 is assigned to the instance.
      - If set to 6, wait until public IPv6 is assigned to the instance.
    choices: [4,6]
    version_added: "2.4"

  wait_timeout:
    description:
      - How long (seconds) to wait either for automatic IP address assignment, or for the device to reach the C(active) I(state).
      - If I(wait_for_public_IPv) is set and I(state) is C(active), the module will wait for both events consequently, applying the timeout twice.
    default: 900
  ipxe_script_url:
    description:
      - URL of custom iPXE script for provisioning.
      - More about custom iPXE for Packet devices at U(https://help.packet.net/technical/infrastructure/custom-ipxe).
    version_added: "2.4"
  always_pxe:
    description:
      - Persist PXE as the first boot option.
      - Normally, the PXE process happens only on the first boot. Set this arg to have your device continuously boot to iPXE.
    default: false
    version_added: "2.4"
    type: bool


requirements:
     - "packet-python >= 1.35"

notes:
     - Doesn't support check mode.

'''

EXAMPLES = '''
# All the examples assume that you have your Packet api token in env var PACKET_API_TOKEN.
# You can also pass it to the auth_token parameter of the module instead.

# Creating devices

- name: create 1 device
  hosts: localhost
  tasks:
  - packet_device:
      project_id: 89b497ee-5afc-420a-8fb5-56984898f4df
      hostnames: myserver
      operating_system: ubuntu_16_04
      plan: baremetal_0
      facility: sjc1

# Create the same device and wait until it is in state "active", (when it's
# ready for other API operations). Fail if the devices in not "active" in
# 10 minutes.

- name: create device and wait up to 10 minutes for active state
  hosts: localhost
  tasks:
  - packet_device:
      project_id: 89b497ee-5afc-420a-8fb5-56984898f4df
      hostnames: myserver
      operating_system: ubuntu_16_04
      plan: baremetal_0
      facility: sjc1
      state: active
      wait_timeout: 600

- name: create 3 ubuntu devices called server-01, server-02 and server-03
  hosts: localhost
  tasks:
  - packet_device:
      project_id: 89b497ee-5afc-420a-8fb5-56984898f4df
      hostnames: server-%02d
      count: 3
      operating_system: ubuntu_16_04
      plan: baremetal_0
      facility: sjc1

- name: Create 3 coreos devices with userdata, wait until they get IPs and then wait for SSH
  hosts: localhost
  tasks:
  - name: create 3 devices and register their facts
    packet_device:
      hostnames: [coreos-one, coreos-two, coreos-three]
      operating_system: coreos_stable
      plan: baremetal_0
      facility: ewr1
      locked: true
      project_id: 89b497ee-5afc-420a-8fb5-56984898f4df
      wait_for_public_IPv: 4
      user_data: |
        #cloud-config
        ssh_authorized_keys:
          - {{ lookup('file', 'my_packet_sshkey') }}
        coreos:
          etcd:
            discovery: https://discovery.etcd.io/6a28e078895c5ec737174db2419bb2f3
            addr: $private_ipv4:4001
            peer-addr: $private_ipv4:7001
          fleet:
            public-ip: $private_ipv4
          units:
            - name: etcd.service
              command: start
            - name: fleet.service
              command: start
    register: newhosts

  - name: wait for ssh
    wait_for:
      delay: 1
      host: "{{ item.public_ipv4 }}"
      port: 22
      state: started
      timeout: 500
    with_items: "{{ newhosts.devices }}"


# Other states of devices

- name: remove 3 devices by uuid
  hosts: localhost
  tasks:
  - packet_device:
      project_id: 89b497ee-5afc-420a-8fb5-56984898f4df
      state: absent
      device_ids:
        - 1fb4faf8-a638-4ac7-8f47-86fe514c30d8
        - 2eb4faf8-a638-4ac7-8f47-86fe514c3043
        - 6bb4faf8-a638-4ac7-8f47-86fe514c301f
'''

RETURN = '''
changed:
    description: True if a device was altered in any way (created, modified or removed)
    type: bool
    sample: True
    returned: success

devices:
    description: Information about each device that was processed
    type: list
    sample: '[{"hostname": "my-server.com", "id": "2a5122b9-c323-4d5c-b53c-9ad3f54273e7",
               "public_ipv4": "147.229.15.12", "private-ipv4": "10.0.15.12",
               "tags": [], "locked": false, "state": "provisioning",
               "public_ipv6": ""2604:1380:2:5200::3"}]'
    returned: success
'''  # NOQA


import os
import re
import time
import uuid
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

HAS_PACKET_SDK = True
try:
    import packet
except ImportError:
    HAS_PACKET_SDK = False

from ansible.module_utils.basic import AnsibleModule


NAME_RE = r'({0}|{0}{1}*{0})'.format(r'[a-zA-Z0-9]', r'[a-zA-Z0-9\-]')
HOSTNAME_RE = r'({0}\.)*{0}$'.format(NAME_RE)
MAX_DEVICES = 100

PACKET_DEVICE_STATES = (
    'queued',
    'provisioning',
    'failed',
    'powering_on',
    'active',
    'powering_off',
    'inactive',
    'rebooting',
)

PACKET_API_TOKEN_ENV_VAR = "PACKET_API_TOKEN"


ALLOWED_STATES = ['absent', 'active', 'inactive', 'rebooted', 'present']


def serialize_device(device):
    """
    Standard representation for a device as returned by various tasks::

        {
            'id': 'device_id'
            'hostname': 'device_hostname',
            'tags': [],
            'locked': false,
            'state': 'provisioning',
            'ip_addresses': [
                {
                    "address": "147.75.194.227",
                    "address_family": 4,
                    "public": true
                },
                {
                    "address": "2604:1380:2:5200::3",
                    "address_family": 6,
                    "public": true
                },
                {
                    "address": "10.100.11.129",
                    "address_family": 4,
                    "public": false
                }
            ],
            "private_ipv4": "10.100.11.129",
            "public_ipv4": "147.75.194.227",
            "public_ipv6": "2604:1380:2:5200::3",
        }

    """
    device_data = {}
    device_data['id'] = device.id
    device_data['hostname'] = device.hostname
    device_data['tags'] = device.tags
    device_data['locked'] = device.locked
    device_data['state'] = device.state
    device_data['ip_addresses'] = [
        {
            'address': addr_data['address'],
            'address_family': addr_data['address_family'],
            'public': addr_data['public'],
        }
        for addr_data in device.ip_addresses
    ]
    # Also include each IPs as a key for easier lookup in roles.
    # Key names:
    # - public_ipv4
    # - public_ipv6
    # - private_ipv4
    # - private_ipv6 (if there is one)
    for ipdata in device_data['ip_addresses']:
        if ipdata['public']:
            if ipdata['address_family'] == 6:
                device_data['public_ipv6'] = ipdata['address']
            elif ipdata['address_family'] == 4:
                device_data['public_ipv4'] = ipdata['address']
        elif not ipdata['public']:
            if ipdata['address_family'] == 6:
                # Packet doesn't give public ipv6 yet, but maybe one
                # day they will
                device_data['private_ipv6'] = ipdata['address']
            elif ipdata['address_family'] == 4:
                device_data['private_ipv4'] = ipdata['address']
    return device_data


def is_valid_hostname(hostname):
    return re.match(HOSTNAME_RE, hostname) is not None


def is_valid_uuid(myuuid):
    try:
        val = uuid.UUID(myuuid, version=4)
    except ValueError:
        return False
    return str(val) == myuuid


def listify_string_name_or_id(s):
    if ',' in s:
        return s.split(',')
    else:
        return [s]


def get_hostname_list(module):
    # hostname is a list-typed param, so I guess it should return list
    # (and it does, in Ansible 2.2.1) but in order to be defensive,
    # I keep here the code to convert an eventual string to list
    hostnames = module.params.get('hostnames')
    count = module.params.get('count')
    count_offset = module.params.get('count_offset')
    if isinstance(hostnames, str):
        hostnames = listify_string_name_or_id(hostnames)
    if not isinstance(hostnames, list):
        raise Exception("name %s is not convertible to list" % hostnames)

    # at this point, hostnames is a list
    hostnames = [h.strip() for h in hostnames]

    if (len(hostnames) > 1) and (count > 1):
        _msg = ("If you set count>1, you should only specify one hostname "
                "with the %d formatter, not a list of hostnames.")
        raise Exception(_msg)

    if (len(hostnames) == 1) and (count > 0):
        hostname_spec = hostnames[0]
        count_range = range(count_offset, count_offset + count)
        if re.search(r"%\d{0,2}d", hostname_spec):
            hostnames = [hostname_spec % i for i in count_range]
        elif count > 1:
            hostname_spec = '%s%%02d' % hostname_spec
            hostnames = [hostname_spec % i for i in count_range]

    for hn in hostnames:
        if not is_valid_hostname(hn):
            raise Exception("Hostname '%s' does not seem to be valid" % hn)

    if len(hostnames) > MAX_DEVICES:
        raise Exception("You specified too many hostnames, max is %d" %
                        MAX_DEVICES)
    return hostnames


def get_device_id_list(module):
    device_ids = module.params.get('device_ids')

    if isinstance(device_ids, str):
        device_ids = listify_string_name_or_id(device_ids)

    device_ids = [di.strip() for di in device_ids]

    for di in device_ids:
        if not is_valid_uuid(di):
            raise Exception("Device ID '%s' does not seem to be valid" % di)

    if len(device_ids) > MAX_DEVICES:
        raise Exception("You specified too many devices, max is %d" %
                        MAX_DEVICES)
    return device_ids


def create_single_device(module, packet_conn, hostname):

    for param in ('hostnames', 'operating_system', 'plan'):
        if not module.params.get(param):
            raise Exception("%s parameter is required for new device."
                            % param)
    project_id = module.params.get('project_id')
    plan = module.params.get('plan')
    user_data = module.params.get('user_data')
    facility = module.params.get('facility')
    operating_system = module.params.get('operating_system')
    locked = module.params.get('locked')
    ipxe_script_url = module.params.get('ipxe_script_url')
    always_pxe = module.params.get('always_pxe')
    device = packet_conn.create_device(
        project_id=project_id,
        hostname=hostname,
        plan=plan,
        facility=facility,
        operating_system=operating_system,
        userdata=user_data,
        locked=locked)
    return device


def refresh_device_list(module, packet_conn, devices):
    device_ids = [d.id for d in devices]
    new_device_list = get_existing_devices(module, packet_conn)
    return [d for d in new_device_list if d.id in device_ids]


def wait_for_devices_active(module, packet_conn, watched_devices):
    wait_timeout = module.params.get('wait_timeout')
    wait_timeout = time.time() + wait_timeout
    refreshed = watched_devices
    while wait_timeout > time.time():
        refreshed = refresh_device_list(module, packet_conn, watched_devices)
        if all(d.state == 'active' for d in refreshed):
            return refreshed
        time.sleep(5)
    raise Exception("Waiting for state \"active\" timed out for devices: %s"
                    % [d.hostname for d in refreshed if d.state != "active"])


def wait_for_public_IPv(module, packet_conn, created_devices):

    def has_public_ip(addr_list, ip_v):
        return any([a['public'] and a['address_family'] == ip_v and
                    a['address'] for a in addr_list])

    def all_have_public_ip(ds, ip_v):
        return all([has_public_ip(d.ip_addresses, ip_v) for d in ds])

    address_family = module.params.get('wait_for_public_IPv')

    wait_timeout = module.params.get('wait_timeout')
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time():
        refreshed = refresh_device_list(module, packet_conn, created_devices)
        if all_have_public_ip(refreshed, address_family):
            return refreshed
        time.sleep(5)

    raise Exception("Waiting for IPv%d address timed out. Hostnames: %s"
                    % (address_family, [d.hostname for d in created_devices]))


def get_existing_devices(module, packet_conn):
    project_id = module.params.get('project_id')
    return packet_conn.list_devices(
        project_id, params={
            'per_page': MAX_DEVICES})


def get_specified_device_identifiers(module):
    if module.params.get('device_ids'):
        device_id_list = get_device_id_list(module)
        return {'ids': device_id_list, 'hostnames': []}
    elif module.params.get('hostnames'):
        hostname_list = get_hostname_list(module)
        return {'hostnames': hostname_list, 'ids': []}


def act_on_devices(module, packet_conn, target_state):
    specified_identifiers = get_specified_device_identifiers(module)
    existing_devices = get_existing_devices(module, packet_conn)
    changed = False
    create_hostnames = []
    if target_state in ['present', 'active', 'rebooted']:
        # states where we might create non-existing specified devices
        existing_devices_names = [ed.hostname for ed in existing_devices]
        create_hostnames = [hn for hn in specified_identifiers['hostnames']
                            if hn not in existing_devices_names]

    process_devices = [d for d in existing_devices
                       if (d.id in specified_identifiers['ids']) or
                       (d.hostname in specified_identifiers['hostnames'])]

    if target_state != 'present':
        _absent_state_map = {}
        for s in PACKET_DEVICE_STATES:
            _absent_state_map[s] = packet.Device.delete

        state_map = {
            'absent': _absent_state_map,
            'active': {'inactive': packet.Device.power_on,
                       'provisioning': None, 'rebooting': None
                       },
            'inactive': {'active': packet.Device.power_off},
            'rebooted': {'active': packet.Device.reboot,
                         'inactive': packet.Device.power_on,
                         'provisioning': None, 'rebooting': None
                         },
        }

        # First do non-creation actions, it might be faster
        for d in process_devices:
            if d.state == target_state:
                continue
            if d.state in state_map[target_state]:
                api_operation = state_map[target_state].get(d.state)
                if api_operation is not None:
                    api_operation(d)
                    changed = True
            else:
                _msg = (
                    "I don't know how to process existing device %s from state %s "
                    "to state %s" %
                    (d.hostname, d.state, target_state))
                raise Exception(_msg)

    # At last create missing devices
    created_devices = []
    if create_hostnames:
        created_devices = [create_single_device(module, packet_conn, n)
                           for n in create_hostnames]
        if module.params.get('wait_for_public_IPv'):
            created_devices = wait_for_public_IPv(
                module, packet_conn, created_devices)
        changed = True

    processed_devices = created_devices + process_devices
    if target_state == 'active':
        processed_devices = wait_for_devices_active(
            module, packet_conn, processed_devices)

    return {
        'changed': changed,
        'devices': [serialize_device(d) for d in processed_devices]
    }


def main():
    module = AnsibleModule(
        argument_spec=dict(
            auth_token=dict(default=os.environ.get(PACKET_API_TOKEN_ENV_VAR),
                            no_log=True),
            count=dict(type='int', default=1),
            count_offset=dict(type='int', default=1),
            device_ids=dict(type='list'),
            facility=dict(),
            features=dict(type='dict'),
            hostnames=dict(type='list', aliases=['name']),
            locked=dict(type='bool', default=False, aliases=['lock']),
            operating_system=dict(),
            plan=dict(),
            project_id=dict(required=True),
            state=dict(choices=ALLOWED_STATES, default='present'),
            user_data=dict(default=None),
            wait_for_public_IPv=dict(type='int', choices=[4, 6]),
            wait_timeout=dict(type='int', default=900),
            ipxe_script_url=dict(default=''),
            always_pxe=dict(type='bool', default=False),
        ),
        required_one_of=[('device_ids', 'hostnames',)],
        mutually_exclusive=[
            ('always_pxe', 'operating_system'),
            ('ipxe_script_url', 'operating_system'),
            ('hostnames', 'device_ids'),
            ('count', 'device_ids'),
            ('count_offset', 'device_ids'),
        ]
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
        module.exit_json(**act_on_devices(module, packet_conn, state))
    except Exception as e:
        module.fail_json(msg='failed to set device state %s, error: %s' %
                         (state, to_native(e)), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
