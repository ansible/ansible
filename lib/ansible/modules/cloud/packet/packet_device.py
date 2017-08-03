#!/usr/bin/python
# (c) 2016, Tomas Karasek <tom.to.the.k@gmail.com>
# (c) 2016, Matt Baldwin <baldwin@stackpointcloud.com>
# (c) 2016, Thibaud Morel l'Horset <teebes@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: packet_device

short_description: create, destroy, start, stop, and reboot a Packet Host machine.

description:
    - create, destroy, update, start, stop, and reboot a Packet Host machine. When the machine is created it can optionally wait for it to have an
      IP address before returning. This module has a dependency on packet >= 1.0.
    - API is documented at U(https://www.packet.net/help/api/#page:devices,header:devices-devices-post).

version_added: 2.3

author: Tomas Karasek <tom.to.the.k@gmail.com>, Matt Baldwin <baldwin@stackpointcloud.com>, Thibaud Morel l'Horset <teebes@gmail.com>

options:
  auth_token:
    description:
      - Packet api token. You can also supply it in env var C(PACKET_API_TOKEN).

  count:
    description:
      - The number of devices to create. Count number can be included in hostname via the %d string formatter.

  count_offset:
    description:
      - From which number to start the count.

  device_ids:
    description:
      - List of device IDs on which to operate.

  facility:
    description:
      - Facility slug for device creation. As of 2016, it should be one of [ewr1, sjc1, ams1, nrt1].

  features:
    description:
      - Dict with "features" for device creation. See Packet API docs for details.

  hostnames:
    description:
      - A hostname of a device, or a list of hostnames.
      - If given string or one-item list, you can use the C("%d") Python string format to expand numbers from count.
      - If only one hostname, it might be expanded to list if count>1.
    aliases: [name]

  lock:
    description:
      - Whether to lock a created device.
    default: false

  operating_system:
    description:
      - OS slug for device creation. See Packet docs or API for current list.

  plan:
    description:
      - Plan slug for device creation. See Packet docs or API for current list.

  project_id:
    description:
      - ID of project of the device.
    required: true

  state:
    description:
      - Desired state of the device.
    choices: [present, absent, active, inactive, rebooted]
    default: 'present'

  user_data:
    description:
      - Userdata blob made available to the machine
    required: false
    default: None

  wait:
    description:
      - Whether to wait for the instance to be assigned IP address before returning.
    required: false
    default: False
    type: bool

  wait_timeout:
    description:
      - How long to wait for IP address of new devices before quitting. In seconds.
    default: 60

requirements:
     - packet-python
     - "python >= 2.6"
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
    returned: always
devices:
    description: Information about each device that was processed
    type: list
    sample: '[{"hostname": "my-server.com", "id": "server-id", "public-ipv4": "147.229.15.12", "private-ipv4": "10.0.15.12", "public-ipv6": ""2604:1380:2:5200::3"}]'
    returned: always
'''  # NOQA


import os
import re
import time
import uuid

HAS_PACKET_SDK = True
try:
    import packet
except ImportError:
    HAS_PACKET_SDK = False

from ansible.module_utils.basic import AnsibleModule


NAME_RE = '({0}|{0}{1}*{0})'.format('[a-zA-Z0-9]','[a-zA-Z0-9\-]')
HOSTNAME_RE = '({0}\.)*{0}$'.format(NAME_RE)
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
    Standard represenation for a device as returned by various tasks::

        {
            'id': 'device_id'
            'hostname': 'device_hostname',
            'tags': [],
            'locked': false,
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
        return [i for i in s.split(',')]
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
        if re.search("%\d{0,2}d", hostname_spec):
            hostnames = [hostname_spec % i for i in count_range]
        elif count > 1:
            hostname_spec = '%s%%02d' % hostname_spec
            hostnames = [hostname_spec % i for i in count_range]

    for hn in hostnames:
        if not is_valid_hostname(hn):
            raise Exception("Hostname '%s' does not seem to be valid" % hn)

    if len(hostnames) > MAX_DEVICES:
        raise Exception("You specified too many devices, max is %d" %
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
    locked = module.params.get('lock')
    operating_system = module.params.get('operating_system')
    locked = module.params.get('locked')

    device = packet_conn.create_device(
        project_id=project_id,
        hostname=hostname,
        plan=plan,
        facility=facility,
        operating_system=operating_system,
        userdata=user_data,
        locked=locked)
    return device


def wait_for_ips(module, packet_conn, created_devices):

    def has_public_ip(addr_list):
        return any([a['public'] and (len(a['address']) > 0) for a in addr_list])

    def all_have_public_ip(ds):
        return all([has_public_ip(d.ip_addresses) for d in ds])

    def refresh_created_devices(ids_of_created_devices, module, packet_conn):
        new_device_list = get_existing_devices(module, packet_conn)
        return [d for d in new_device_list if d.id in ids_of_created_devices]

    created_ids = [d.id for d in created_devices]
    wait_timeout = module.params.get('wait_timeout')
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time():
        refreshed = refresh_created_devices(created_ids, module,
                                            packet_conn)
        if all_have_public_ip(refreshed):
            return refreshed
        time.sleep(5)

    raise Exception("Waiting for IP assignment timed out. Hostnames: %s"
                     % [d.hostname for d in created_devices])


def get_existing_devices(module, packet_conn):
    project_id = module.params.get('project_id')
    return packet_conn.list_devices(project_id, params={'per_page': MAX_DEVICES})


def get_specified_device_identifiers(module):
    if module.params.get('device_ids'):
        device_id_list = get_device_id_list(module)
        return {'ids': device_id_list, 'hostnames': []}
    elif module.params.get('hostnames'):
        hostname_list = get_hostname_list(module)
        return {'hostnames': hostname_list, 'ids': []}


def act_on_devices(target_state, module, packet_conn):
    specified_identifiers = get_specified_device_identifiers(module)
    existing_devices = get_existing_devices(module, packet_conn)
    changed = False
    create_hostnames = []
    if target_state in ['present', 'active', 'rebooted']:
        # states where we might create non-existing specified devices
        existing_devices_names = [ed.hostname for ed in existing_devices]
        create_hostnames = [hn for hn in specified_identifiers['hostnames']
                            if hn not in existing_devices_names]

    process_devices  = [d for d in existing_devices
                        if (d.id in specified_identifiers['ids']) or
                           (d.hostname in specified_identifiers['hostnames'])]

    if target_state != 'present':
        _absent_state_map = {}
        for s in PACKET_DEVICE_STATES:
            _absent_state_map[s] = packet.Device.delete

        state_map = {
            'absent': _absent_state_map,
            'active': {'inactive': packet.Device.power_on},
            'inactive': {'active': packet.Device.power_off},
            'rebooted': {'active': packet.Device.reboot,
                       'inactive': packet.Device.power_on},
            }

        # First do non-creation actions, it might be faster
        for d in process_devices:
            if d.state in state_map[target_state]:
                api_operation = state_map[target_state].get(d.state)
                try:
                    api_operation(d)
                    changed = True
                except Exception as e:
                    _msg = ("while trying to make device %s, id %s %s, from state %s, "
                            "with api call by %s got error: %s" %
                           (d.hostname, d.id, target_state, d.state, api_operation, e))
                    raise Exception(_msg)
            else:
                _msg = ("I don't know how to process existing device %s from state %s "
                        "to state %s" % (d.hostname, d.state, target_state))
                raise Exception(_msg)

    # At last create missing devices
    created_devices = []
    if create_hostnames:
        created_devices = [create_single_device(module, packet_conn, n)
                           for n in create_hostnames]
        if module.params.get('wait'):
            created_devices = wait_for_ips(module, packet_conn, created_devices)
        changed = True

    processed_devices = created_devices + process_devices

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
            facility=dict(default='ewr1'),
            features=dict(type='dict'),
            hostnames=dict(type='list', aliases=['name']),
            locked=dict(type='bool', default=False),
            operating_system=dict(),
            plan=dict(),
            project_id=dict(required=True),
            state=dict(choices=ALLOWED_STATES, default='present'),
            user_data=dict(default=None),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='int', default=60),

        ),
        required_one_of=[('device_ids','hostnames',)],
        mutually_exclusive=[
            ('hostnames', 'device_ids'),
            ('count', 'device_ids'),
            ('count_offset', 'device_ids'),
            ]
    )

    if not HAS_PACKET_SDK:
        module.fail_json(msg='packet required for this module')

    if not module.params.get('auth_token'):
        _fail_msg = ( "if Packet API token is not in environment variable %s, "
                      "the auth_token parameter is required" %
                       PACKET_API_TOKEN_ENV_VAR)
        module.fail_json(msg=_fail_msg)

    auth_token = module.params.get('auth_token')

    packet_conn = packet.Manager(auth_token=auth_token)

    state = module.params.get('state')

    try:
        module.exit_json(**act_on_devices(state, module, packet_conn))
    except Exception as e:
        module.fail_json(msg='failed to set machine state %s, error: %s' % (state,str(e)))


if __name__ == '__main__':
    main()
