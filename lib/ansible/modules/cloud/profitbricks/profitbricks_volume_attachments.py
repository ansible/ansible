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
module: profitbricks_volume_attachments
short_description: Attach or detach a volume.
description:
     - Allows you to attach or detach a volume from a ProfitBricks server. This module has a dependency on profitbricks >= 1.0.0
version_added: "2.0"
options:
  datacenter:
    description:
      - The datacenter in which to operate.
    required: true
  server:
    description:
      - The name of the server you wish to detach or attach the volume.
    required: true
  volume:
    description:
      - The volume name or ID.
    required: true
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
      - wait for the operation to complete before returning
    required: false
    default: "yes"
    type: bool
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
  state:
    description:
      - Indicate desired state of the resource
    required: false
    default: 'present'
    choices: ["present", "absent"]

requirements: [ "profitbricks" ]
author: Matt Baldwin (@baldwinSPC) <baldwin@stackpointcloud.com>
'''

EXAMPLES = '''

# Attach a Volume

- profitbricks_volume_attachments:
    datacenter: Tardis One
    server: node002
    volume: vol01
    wait_timeout: 500
    state: present

# Detach a Volume

- profitbricks_volume_attachments:
    datacenter: Tardis One
    server: node002
    volume: vol01
    wait_timeout: 500
    state: absent

'''

import re
import time

HAS_PB_SDK = True
try:
    from profitbricks.client import ProfitBricksService
except ImportError:
    HAS_PB_SDK = False

from ansible.module_utils.basic import AnsibleModule


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


def attach_volume(module, profitbricks):
    """
    Attaches a volume.

    This will attach a volume to the server.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True if the volume was attached, false otherwise
    """
    datacenter = module.params.get('datacenter')
    server = module.params.get('server')
    volume = module.params.get('volume')

    # Locate UUID for Datacenter
    if not (uuid_match.match(datacenter)):
        datacenter_list = profitbricks.list_datacenters()
        for d in datacenter_list['items']:
            dc = profitbricks.get_datacenter(d['id'])
            if datacenter == dc['properties']['name']:
                datacenter = d['id']
                break

    # Locate UUID for Server
    if not (uuid_match.match(server)):
        server_list = profitbricks.list_servers(datacenter)
        for s in server_list['items']:
            if server == s['properties']['name']:
                server = s['id']
                break

    # Locate UUID for Volume
    if not (uuid_match.match(volume)):
        volume_list = profitbricks.list_volumes(datacenter)
        for v in volume_list['items']:
            if volume == v['properties']['name']:
                volume = v['id']
                break

    return profitbricks.attach_volume(datacenter, server, volume)


def detach_volume(module, profitbricks):
    """
    Detaches a volume.

    This will remove a volume from the server.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True if the volume was detached, false otherwise
    """
    datacenter = module.params.get('datacenter')
    server = module.params.get('server')
    volume = module.params.get('volume')

    # Locate UUID for Datacenter
    if not (uuid_match.match(datacenter)):
        datacenter_list = profitbricks.list_datacenters()
        for d in datacenter_list['items']:
            dc = profitbricks.get_datacenter(d['id'])
            if datacenter == dc['properties']['name']:
                datacenter = d['id']
                break

    # Locate UUID for Server
    if not (uuid_match.match(server)):
        server_list = profitbricks.list_servers(datacenter)
        for s in server_list['items']:
            if server == s['properties']['name']:
                server = s['id']
                break

    # Locate UUID for Volume
    if not (uuid_match.match(volume)):
        volume_list = profitbricks.list_volumes(datacenter)
        for v in volume_list['items']:
            if volume == v['properties']['name']:
                volume = v['id']
                break

    return profitbricks.detach_volume(datacenter, server, volume)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            datacenter=dict(),
            server=dict(),
            volume=dict(),
            subscription_user=dict(),
            subscription_password=dict(no_log=True),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=600),
            state=dict(default='present'),
        )
    )

    if not HAS_PB_SDK:
        module.fail_json(msg='profitbricks required for this module')

    if not module.params.get('subscription_user'):
        module.fail_json(msg='subscription_user parameter is required')
    if not module.params.get('subscription_password'):
        module.fail_json(msg='subscription_password parameter is required')
    if not module.params.get('datacenter'):
        module.fail_json(msg='datacenter parameter is required')
    if not module.params.get('server'):
        module.fail_json(msg='server parameter is required')
    if not module.params.get('volume'):
        module.fail_json(msg='volume parameter is required')

    subscription_user = module.params.get('subscription_user')
    subscription_password = module.params.get('subscription_password')

    profitbricks = ProfitBricksService(
        username=subscription_user,
        password=subscription_password)

    state = module.params.get('state')

    if state == 'absent':
        try:
            (changed) = detach_volume(module, profitbricks)
            module.exit_json(changed=changed)
        except Exception as e:
            module.fail_json(msg='failed to set volume_attach state: %s' % str(e))
    elif state == 'present':
        try:
            attach_volume(module, profitbricks)
            module.exit_json()
        except Exception as e:
            module.fail_json(msg='failed to set volume_attach state: %s' % str(e))


if __name__ == '__main__':
    main()
