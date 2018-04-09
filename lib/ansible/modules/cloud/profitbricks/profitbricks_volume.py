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
module: profitbricks_volume
short_description: Create or destroy a volume.
description:
     - Allows you to create or remove a volume from a ProfitBricks datacenter. This module has a dependency on profitbricks >= 1.0.0
version_added: "2.0"
options:
  datacenter:
    description:
      - The datacenter in which to create the volumes.
    required: true
  name:
    description:
      - The name of the volumes. You can enumerate the names using auto_increment.
    required: true
  size:
    description:
      - The size of the volume.
    required: false
    default: 10
  bus:
    description:
      - The bus type.
    required: false
    default: VIRTIO
    choices: [ "IDE", "VIRTIO"]
  image:
    description:
      - The system image ID for the volume, e.g. a3eae284-a2fe-11e4-b187-5f1f641608c8. This can also be a snapshot image ID.
    required: true
  image_password:
    description:
      - Password set for the administrative user.
    required: false
    version_added: '2.2'
  ssh_keys:
    description:
      - Public SSH keys allowing access to the virtual machine.
    required: false
    version_added: '2.2'
  disk_type:
    description:
      - The disk type of the volume.
    required: false
    default: HDD
    choices: [ "HDD", "SSD" ]
  licence_type:
    description:
      - The licence type for the volume. This is used when the image is non-standard.
    required: false
    default: UNKNOWN
    choices: ["LINUX", "WINDOWS", "UNKNOWN" , "OTHER"]
  count:
    description:
      - The number of volumes you wish to create.
    required: false
    default: 1
  auto_increment:
    description:
      - Whether or not to increment a single number in the name for created virtual machines.
    default: yes
    choices: ["yes", "no"]
  instance_ids:
    description:
      - list of instance ids, currently only used when state='absent' to remove instances.
    required: false
  subscription_user:
    description:
      - The ProfitBricks username. Overrides the PB_SUBSCRIPTION_ID environment variable.
    required: false
  subscription_password:
    description:
      - THe ProfitBricks password. Overrides the PB_PASSWORD environment variable.
    required: false
  wait:
    description:
      - wait for the datacenter to be created before returning
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
  state:
    description:
      - create or terminate datacenters
    required: false
    default: 'present'
    choices: ["present", "absent"]

requirements: [ "profitbricks" ]
author: Matt Baldwin (baldwin@stackpointcloud.com)
'''

EXAMPLES = '''

# Create Multiple Volumes

- profitbricks_volume:
    datacenter: Tardis One
    name: vol%02d
    count: 5
    auto_increment: yes
    wait_timeout: 500
    state: present

# Remove Volumes

- profitbricks_volume:
    datacenter: Tardis One
    instance_ids:
      - 'vol01'
      - 'vol02'
    wait_timeout: 500
    state: absent

'''

import re
import time
import traceback

HAS_PB_SDK = True
try:
    from profitbricks.client import ProfitBricksService, Volume
except ImportError:
    HAS_PB_SDK = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import xrange
from ansible.module_utils._text import to_native


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


def _create_volume(module, profitbricks, datacenter, name):
    size = module.params.get('size')
    bus = module.params.get('bus')
    image = module.params.get('image')
    image_password = module.params.get('image_password')
    ssh_keys = module.params.get('ssh_keys')
    disk_type = module.params.get('disk_type')
    licence_type = module.params.get('licence_type')
    wait_timeout = module.params.get('wait_timeout')
    wait = module.params.get('wait')

    try:
        v = Volume(
            name=name,
            size=size,
            bus=bus,
            image=image,
            image_password=image_password,
            ssh_keys=ssh_keys,
            disk_type=disk_type,
            licence_type=licence_type
        )

        volume_response = profitbricks.create_volume(datacenter, v)

        if wait:
            _wait_for_completion(profitbricks, volume_response,
                                 wait_timeout, "_create_volume")

    except Exception as e:
        module.fail_json(msg="failed to create the volume: %s" % str(e))

    return volume_response


def _delete_volume(module, profitbricks, datacenter, volume):
    try:
        profitbricks.delete_volume(datacenter, volume)
    except Exception as e:
        module.fail_json(msg="failed to remove the volume: %s" % str(e))


def create_volume(module, profitbricks):
    """
    Creates a volume.

    This will create a volume in a datacenter.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True if the volume was created, false otherwise
    """
    datacenter = module.params.get('datacenter')
    name = module.params.get('name')
    auto_increment = module.params.get('auto_increment')
    count = module.params.get('count')

    datacenter_found = False
    failed = True
    volumes = []

    # Locate UUID for Datacenter
    if not (uuid_match.match(datacenter)):
        datacenter_list = profitbricks.list_datacenters()
        for d in datacenter_list['items']:
            dc = profitbricks.get_datacenter(d['id'])
            if datacenter == dc['properties']['name']:
                datacenter = d['id']
                datacenter_found = True
                break

    if not datacenter_found:
        module.fail_json(msg='datacenter could not be found.')

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
        names = [name] * count

    for name in names:
        create_response = _create_volume(module, profitbricks, str(datacenter), name)
        volumes.append(create_response)
        _attach_volume(module, profitbricks, datacenter, create_response['id'])
        failed = False

    results = {
        'failed': failed,
        'volumes': volumes,
        'action': 'create',
        'instance_ids': {
            'instances': [i['id'] for i in volumes],
        }
    }

    return results


def delete_volume(module, profitbricks):
    """
    Removes a volume.

    This will create a volume in a datacenter.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True if the volume was removed, false otherwise
    """
    if not isinstance(module.params.get('instance_ids'), list) or len(module.params.get('instance_ids')) < 1:
        module.fail_json(msg='instance_ids should be a list of virtual machine ids or names, aborting')

    datacenter = module.params.get('datacenter')
    changed = False
    instance_ids = module.params.get('instance_ids')

    # Locate UUID for Datacenter
    if not (uuid_match.match(datacenter)):
        datacenter_list = profitbricks.list_datacenters()
        for d in datacenter_list['items']:
            dc = profitbricks.get_datacenter(d['id'])
            if datacenter == dc['properties']['name']:
                datacenter = d['id']
                break

    for n in instance_ids:
        if(uuid_match.match(n)):
            _delete_volume(module, profitbricks, datacenter, n)
            changed = True
        else:
            volumes = profitbricks.list_volumes(datacenter)
            for v in volumes['items']:
                if n == v['properties']['name']:
                    volume_id = v['id']
                    _delete_volume(module, profitbricks, datacenter, volume_id)
                    changed = True

    return changed


def _attach_volume(module, profitbricks, datacenter, volume):
    """
    Attaches a volume.

    This will attach a volume to the server.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True if the volume was attached, false otherwise
    """
    server = module.params.get('server')

    # Locate UUID for Server
    if server:
        if not (uuid_match.match(server)):
            server_list = profitbricks.list_servers(datacenter)
            for s in server_list['items']:
                if server == s['properties']['name']:
                    server = s['id']
                    break

        try:
            return profitbricks.attach_volume(datacenter, server, volume)
        except Exception as e:
            module.fail_json(msg='failed to attach volume: %s' % to_native(e), exception=traceback.format_exc())


def main():
    module = AnsibleModule(
        argument_spec=dict(
            datacenter=dict(),
            server=dict(),
            name=dict(),
            size=dict(type='int', default=10),
            bus=dict(choices=['VIRTIO', 'IDE'], default='VIRTIO'),
            image=dict(),
            image_password=dict(default=None, no_log=True),
            ssh_keys=dict(type='list', default=[]),
            disk_type=dict(choices=['HDD', 'SSD'], default='HDD'),
            licence_type=dict(default='UNKNOWN'),
            count=dict(type='int', default=1),
            auto_increment=dict(type='bool', default=True),
            instance_ids=dict(type='list', default=[]),
            subscription_user=dict(),
            subscription_password=dict(no_log=True),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=600),
            state=dict(default='present'),
        )
    )

    if not module.params.get('subscription_user'):
        module.fail_json(msg='subscription_user parameter is required')
    if not module.params.get('subscription_password'):
        module.fail_json(msg='subscription_password parameter is required')

    subscription_user = module.params.get('subscription_user')
    subscription_password = module.params.get('subscription_password')

    profitbricks = ProfitBricksService(
        username=subscription_user,
        password=subscription_password)

    state = module.params.get('state')

    if state == 'absent':
        if not module.params.get('datacenter'):
            module.fail_json(msg='datacenter parameter is required for running or stopping machines.')

        try:
            (changed) = delete_volume(module, profitbricks)
            module.exit_json(changed=changed)
        except Exception as e:
            module.fail_json(msg='failed to set volume state: %s' % to_native(e), exception=traceback.format_exc())

    elif state == 'present':
        if not module.params.get('datacenter'):
            module.fail_json(msg='datacenter parameter is required for new instance')
        if not module.params.get('name'):
            module.fail_json(msg='name parameter is required for new instance')

        try:
            (volume_dict_array) = create_volume(module, profitbricks)
            module.exit_json(**volume_dict_array)
        except Exception as e:
            module.fail_json(msg='failed to set volume state: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
