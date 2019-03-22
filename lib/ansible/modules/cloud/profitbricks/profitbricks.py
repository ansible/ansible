#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: profitbricks
short_description: Create, destroy, start, stop, and reboot a ProfitBricks virtual machine.
description:
     - Create, destroy, update, start, stop, and reboot a ProfitBricks virtual machine. When the virtual machine is created it can optionally wait
       for it to be 'running' before returning. This module has a dependency on profitbricks >= 1.0.0
version_added: "2.0"
options:
  auto_increment:
    description:
      - Whether or not to increment a single number in the name for created virtual machines.
    type: bool
    default: 'yes'
  name:
    description:
      - The name of the virtual machine.
    required: true
  image:
    description:
      - The system image ID for creating the virtual machine, e.g. a3eae284-a2fe-11e4-b187-5f1f641608c8.
    required: true
  image_password:
    description:
      - Password set for the administrative user.
    version_added: '2.2'
  ssh_keys:
    description:
      - Public SSH keys allowing access to the virtual machine.
    version_added: '2.2'
  datacenter:
    description:
      - The datacenter to provision this virtual machine.
  cores:
    description:
      - The number of CPU cores to allocate to the virtual machine.
    default: 2
  ram:
    description:
      - The amount of memory to allocate to the virtual machine.
    default: 2048
  cpu_family:
    description:
      - The CPU family type to allocate to the virtual machine.
    default: AMD_OPTERON
    choices: [ "AMD_OPTERON", "INTEL_XEON" ]
    version_added: '2.2'
  volume_size:
    description:
      - The size in GB of the boot volume.
    default: 10
  bus:
    description:
      - The bus type for the volume.
    default: VIRTIO
    choices: [ "IDE", "VIRTIO"]
  instance_ids:
    description:
      - list of instance ids, currently only used when state='absent' to remove instances.
  count:
    description:
      - The number of virtual machines to create.
    default: 1
  location:
    description:
      - The datacenter location. Use only if you want to create the Datacenter or else this value is ignored.
    default: us/las
    choices: [ "us/las", "de/fra", "de/fkb" ]
  assign_public_ip:
    description:
      - This will assign the machine to the public LAN. If no LAN exists with public Internet access it is created.
    type: bool
    default: 'no'
  lan:
    description:
      - The ID of the LAN you wish to add the servers to.
    default: 1
  subscription_user:
    description:
      - The ProfitBricks username. Overrides the PB_SUBSCRIPTION_ID environment variable.
  subscription_password:
    description:
      - THe ProfitBricks password. Overrides the PB_PASSWORD environment variable.
  wait:
    description:
      - wait for the instance to be in state 'running' before returning
    type: bool
    default: 'yes'
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
  remove_boot_volume:
    description:
      - remove the bootVolume of the virtual machine you're destroying.
    type: bool
    default: 'yes'
  state:
    description:
      - create or terminate instances
    default: 'present'
    choices: [ "running", "stopped", "absent", "present" ]

requirements:
     - "profitbricks"
     - "python >= 2.6"
author: Matt Baldwin (@baldwinSPC) <baldwin@stackpointcloud.com>
'''

EXAMPLES = '''

# Note: These examples do not set authentication details, see the AWS Guide for details.

# Provisioning example. This will create three servers and enumerate their names.

- profitbricks:
    datacenter: Tardis One
    name: web%02d.stackpointcloud.com
    cores: 4
    ram: 2048
    volume_size: 50
    cpu_family: INTEL_XEON
    image: a3eae284-a2fe-11e4-b187-5f1f641608c8
    location: us/las
    count: 3
    assign_public_ip: true

# Removing Virtual machines

- profitbricks:
    datacenter: Tardis One
    instance_ids:
      - 'web001.stackpointcloud.com'
      - 'web002.stackpointcloud.com'
      - 'web003.stackpointcloud.com'
    wait_timeout: 500
    state: absent

# Starting Virtual Machines.

- profitbricks:
    datacenter: Tardis One
    instance_ids:
      - 'web001.stackpointcloud.com'
      - 'web002.stackpointcloud.com'
      - 'web003.stackpointcloud.com'
    wait_timeout: 500
    state: running

# Stopping Virtual Machines

- profitbricks:
    datacenter: Tardis One
    instance_ids:
      - 'web001.stackpointcloud.com'
      - 'web002.stackpointcloud.com'
      - 'web003.stackpointcloud.com'
    wait_timeout: 500
    state: stopped

'''

import re
import uuid
import time
import traceback

HAS_PB_SDK = True

try:
    from profitbricks.client import ProfitBricksService, Volume, Server, Datacenter, NIC, LAN
except ImportError:
    HAS_PB_SDK = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import xrange
from ansible.module_utils._text import to_native


LOCATIONS = ['us/las',
             'de/fra',
             'de/fkb']

uuid_match = re.compile(
    r'[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}', re.I)


def _wait_for_completion(profitbricks, promise, wait_timeout, msg):
    if not promise:
        return
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time():
        time.sleep(5)
        operation_result = profitbricks.get_request(
            request_id=promise['requestId'],
            status=True)

        if operation_result['metadata']['status'] == "DONE":
            return
        elif operation_result['metadata']['status'] == "FAILED":
            raise Exception(
                'Request failed to complete ' + msg + ' "' + str(
                    promise['requestId']) + '" to complete.')

    raise Exception(
        'Timed out waiting for async operation ' + msg + ' "' + str(
            promise['requestId']
        ) + '" to complete.')


def _create_machine(module, profitbricks, datacenter, name):
    cores = module.params.get('cores')
    ram = module.params.get('ram')
    cpu_family = module.params.get('cpu_family')
    volume_size = module.params.get('volume_size')
    disk_type = module.params.get('disk_type')
    image_password = module.params.get('image_password')
    ssh_keys = module.params.get('ssh_keys')
    bus = module.params.get('bus')
    lan = module.params.get('lan')
    assign_public_ip = module.params.get('assign_public_ip')
    subscription_user = module.params.get('subscription_user')
    subscription_password = module.params.get('subscription_password')
    location = module.params.get('location')
    image = module.params.get('image')
    assign_public_ip = module.boolean(module.params.get('assign_public_ip'))
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    if assign_public_ip:
        public_found = False

        lans = profitbricks.list_lans(datacenter)
        for lan in lans['items']:
            if lan['properties']['public']:
                public_found = True
                lan = lan['id']

        if not public_found:
            i = LAN(
                name='public',
                public=True)

            lan_response = profitbricks.create_lan(datacenter, i)
            _wait_for_completion(profitbricks, lan_response,
                                 wait_timeout, "_create_machine")
            lan = lan_response['id']

    v = Volume(
        name=str(uuid.uuid4()).replace('-', '')[:10],
        size=volume_size,
        image=image,
        image_password=image_password,
        ssh_keys=ssh_keys,
        disk_type=disk_type,
        bus=bus)

    n = NIC(
        lan=int(lan)
    )

    s = Server(
        name=name,
        ram=ram,
        cores=cores,
        cpu_family=cpu_family,
        create_volumes=[v],
        nics=[n],
    )

    try:
        create_server_response = profitbricks.create_server(
            datacenter_id=datacenter, server=s)

        _wait_for_completion(profitbricks, create_server_response,
                             wait_timeout, "create_virtual_machine")

        server_response = profitbricks.get_server(
            datacenter_id=datacenter,
            server_id=create_server_response['id'],
            depth=3
        )
    except Exception as e:
        module.fail_json(msg="failed to create the new server: %s" % str(e))
    else:
        return server_response


def _startstop_machine(module, profitbricks, datacenter_id, server_id):
    state = module.params.get('state')

    try:
        if state == 'running':
            profitbricks.start_server(datacenter_id, server_id)
        else:
            profitbricks.stop_server(datacenter_id, server_id)

        return True
    except Exception as e:
        module.fail_json(msg="failed to start or stop the virtual machine %s at %s: %s" % (server_id, datacenter_id, str(e)))


def _create_datacenter(module, profitbricks):
    datacenter = module.params.get('datacenter')
    location = module.params.get('location')
    wait_timeout = module.params.get('wait_timeout')

    i = Datacenter(
        name=datacenter,
        location=location
    )

    try:
        datacenter_response = profitbricks.create_datacenter(datacenter=i)

        _wait_for_completion(profitbricks, datacenter_response,
                             wait_timeout, "_create_datacenter")

        return datacenter_response
    except Exception as e:
        module.fail_json(msg="failed to create the new server(s): %s" % str(e))


def create_virtual_machine(module, profitbricks):
    """
    Create new virtual machine

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object

    Returns:
        True if a new virtual machine was created, false otherwise
    """
    datacenter = module.params.get('datacenter')
    name = module.params.get('name')
    auto_increment = module.params.get('auto_increment')
    count = module.params.get('count')
    lan = module.params.get('lan')
    wait_timeout = module.params.get('wait_timeout')
    failed = True
    datacenter_found = False

    virtual_machines = []
    virtual_machine_ids = []

    # Locate UUID for datacenter if referenced by name.
    datacenter_list = profitbricks.list_datacenters()
    datacenter_id = _get_datacenter_id(datacenter_list, datacenter)
    if datacenter_id:
        datacenter_found = True

    if not datacenter_found:
        datacenter_response = _create_datacenter(module, profitbricks)
        datacenter_id = datacenter_response['id']

        _wait_for_completion(profitbricks, datacenter_response,
                             wait_timeout, "create_virtual_machine")

    if auto_increment:
        numbers = set()
        count_offset = 1

        try:
            name % 0
        except TypeError as e:
            if e.message.startswith('not all'):
                name = '%s%%d' % name
            else:
                module.fail_json(msg=e.message, exception=traceback.format_exc())

        number_range = xrange(count_offset, count_offset + count + len(numbers))
        available_numbers = list(set(number_range).difference(numbers))
        names = []
        numbers_to_use = available_numbers[:count]
        for number in numbers_to_use:
            names.append(name % number)
    else:
        names = [name]

    # Prefetch a list of servers for later comparison.
    server_list = profitbricks.list_servers(datacenter_id)
    for name in names:
        # Skip server creation if the server already exists.
        if _get_server_id(server_list, name):
            continue

        create_response = _create_machine(module, profitbricks, str(datacenter_id), name)
        nics = profitbricks.list_nics(datacenter_id, create_response['id'])
        for n in nics['items']:
            if lan == n['properties']['lan']:
                create_response.update({'public_ip': n['properties']['ips'][0]})

        virtual_machines.append(create_response)

    failed = False

    results = {
        'failed': failed,
        'machines': virtual_machines,
        'action': 'create',
        'instance_ids': {
            'instances': [i['id'] for i in virtual_machines],
        }
    }

    return results


def remove_virtual_machine(module, profitbricks):
    """
    Removes a virtual machine.

    This will remove the virtual machine along with the bootVolume.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Not yet supported: handle deletion of attached data disks.

    Returns:
        True if a new virtual server was deleted, false otherwise
    """
    datacenter = module.params.get('datacenter')
    instance_ids = module.params.get('instance_ids')
    remove_boot_volume = module.params.get('remove_boot_volume')
    changed = False

    if not isinstance(module.params.get('instance_ids'), list) or len(module.params.get('instance_ids')) < 1:
        module.fail_json(msg='instance_ids should be a list of virtual machine ids or names, aborting')

    # Locate UUID for datacenter if referenced by name.
    datacenter_list = profitbricks.list_datacenters()
    datacenter_id = _get_datacenter_id(datacenter_list, datacenter)
    if not datacenter_id:
        module.fail_json(msg='Virtual data center \'%s\' not found.' % str(datacenter))

    # Prefetch server list for later comparison.
    server_list = profitbricks.list_servers(datacenter_id)
    for instance in instance_ids:
        # Locate UUID for server if referenced by name.
        server_id = _get_server_id(server_list, instance)
        if server_id:
            # Remove the server's boot volume
            if remove_boot_volume:
                _remove_boot_volume(module, profitbricks, datacenter_id, server_id)

            # Remove the server
            try:
                server_response = profitbricks.delete_server(datacenter_id, server_id)
            except Exception as e:
                module.fail_json(msg="failed to terminate the virtual server: %s" % to_native(e), exception=traceback.format_exc())
            else:
                changed = True

    return changed


def _remove_boot_volume(module, profitbricks, datacenter_id, server_id):
    """
    Remove the boot volume from the server
    """
    try:
        server = profitbricks.get_server(datacenter_id, server_id)
        volume_id = server['properties']['bootVolume']['id']
        volume_response = profitbricks.delete_volume(datacenter_id, volume_id)
    except Exception as e:
        module.fail_json(msg="failed to remove the server's boot volume: %s" % to_native(e), exception=traceback.format_exc())


def startstop_machine(module, profitbricks, state):
    """
    Starts or Stops a virtual machine.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True when the servers process the action successfully, false otherwise.
    """
    if not isinstance(module.params.get('instance_ids'), list) or len(module.params.get('instance_ids')) < 1:
        module.fail_json(msg='instance_ids should be a list of virtual machine ids or names, aborting')

    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    changed = False

    datacenter = module.params.get('datacenter')
    instance_ids = module.params.get('instance_ids')

    # Locate UUID for datacenter if referenced by name.
    datacenter_list = profitbricks.list_datacenters()
    datacenter_id = _get_datacenter_id(datacenter_list, datacenter)
    if not datacenter_id:
        module.fail_json(msg='Virtual data center \'%s\' not found.' % str(datacenter))

    # Prefetch server list for later comparison.
    server_list = profitbricks.list_servers(datacenter_id)
    for instance in instance_ids:
        # Locate UUID of server if referenced by name.
        server_id = _get_server_id(server_list, instance)
        if server_id:
            _startstop_machine(module, profitbricks, datacenter_id, server_id)
            changed = True

    if wait:
        wait_timeout = time.time() + wait_timeout
        while wait_timeout > time.time():
            matched_instances = []
            for res in profitbricks.list_servers(datacenter_id)['items']:
                if state == 'running':
                    if res['properties']['vmState'].lower() == state:
                        matched_instances.append(res)
                elif state == 'stopped':
                    if res['properties']['vmState'].lower() == 'shutoff':
                        matched_instances.append(res)

            if len(matched_instances) < len(instance_ids):
                time.sleep(5)
            else:
                break

        if wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(msg="wait for virtual machine state timeout on %s" % time.asctime())

    return (changed)


def _get_datacenter_id(datacenters, identity):
    """
    Fetch and return datacenter UUID by datacenter name if found.
    """
    for datacenter in datacenters['items']:
        if identity in (datacenter['properties']['name'], datacenter['id']):
            return datacenter['id']
    return None


def _get_server_id(servers, identity):
    """
    Fetch and return server UUID by server name if found.
    """
    for server in servers['items']:
        if identity in (server['properties']['name'], server['id']):
            return server['id']
    return None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            datacenter=dict(),
            name=dict(),
            image=dict(),
            cores=dict(type='int', default=2),
            ram=dict(type='int', default=2048),
            cpu_family=dict(choices=['AMD_OPTERON', 'INTEL_XEON'],
                            default='AMD_OPTERON'),
            volume_size=dict(type='int', default=10),
            disk_type=dict(choices=['HDD', 'SSD'], default='HDD'),
            image_password=dict(default=None, no_log=True),
            ssh_keys=dict(type='list', default=[]),
            bus=dict(choices=['VIRTIO', 'IDE'], default='VIRTIO'),
            lan=dict(type='int', default=1),
            count=dict(type='int', default=1),
            auto_increment=dict(type='bool', default=True),
            instance_ids=dict(type='list', default=[]),
            subscription_user=dict(),
            subscription_password=dict(no_log=True),
            location=dict(choices=LOCATIONS, default='us/las'),
            assign_public_ip=dict(type='bool', default=False),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=600),
            remove_boot_volume=dict(type='bool', default=True),
            state=dict(default='present'),
        )
    )

    if not HAS_PB_SDK:
        module.fail_json(msg='profitbricks required for this module')

    subscription_user = module.params.get('subscription_user')
    subscription_password = module.params.get('subscription_password')

    profitbricks = ProfitBricksService(
        username=subscription_user,
        password=subscription_password)

    state = module.params.get('state')

    if state == 'absent':
        if not module.params.get('datacenter'):
            module.fail_json(msg='datacenter parameter is required ' +
                             'for running or stopping machines.')

        try:
            (changed) = remove_virtual_machine(module, profitbricks)
            module.exit_json(changed=changed)
        except Exception as e:
            module.fail_json(msg='failed to set instance state: %s' % to_native(e), exception=traceback.format_exc())

    elif state in ('running', 'stopped'):
        if not module.params.get('datacenter'):
            module.fail_json(msg='datacenter parameter is required for ' +
                             'running or stopping machines.')
        try:
            (changed) = startstop_machine(module, profitbricks, state)
            module.exit_json(changed=changed)
        except Exception as e:
            module.fail_json(msg='failed to set instance state: %s' % to_native(e), exception=traceback.format_exc())

    elif state == 'present':
        if not module.params.get('name'):
            module.fail_json(msg='name parameter is required for new instance')
        if not module.params.get('image'):
            module.fail_json(msg='image parameter is required for new instance')
        if not module.params.get('subscription_user'):
            module.fail_json(msg='subscription_user parameter is ' +
                             'required for new instance')
        if not module.params.get('subscription_password'):
            module.fail_json(msg='subscription_password parameter is ' +
                             'required for new instance')

        try:
            (machine_dict_array) = create_virtual_machine(module, profitbricks)
            module.exit_json(**machine_dict_array)
        except Exception as e:
            module.fail_json(msg='failed to set instance state: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
