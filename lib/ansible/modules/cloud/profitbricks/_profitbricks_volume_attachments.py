#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: profitbricks_volume_attachments
short_description: Attach or detach a volume.
description:
     - Allows you to attach or detach a volume from a ProfitBricks server. This module has a dependency on profitbricks >= 1.0.0
version_added: "2.0"
deprecated:
    removed_in: "2.12"
    alternative: Use M(profitbricks) instead.
    why: The module is redundant.
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
  api_url:
    description:
      - The ProfitBricks API base URL.
    default: null
    version_added: "2.8"
  username:
    description:
      - The ProfitBricks username. Overrides the PROFITBRICKS_USERNAME environment variable.
    required: false
    aliases:
      - subscription_user
  password:
    description:
      - The ProfitBricks password. Overrides the PROFITBRICKS_PASSWORD environment variable.
    required: false
    aliases:
      - subscription_password
  wait:
    description:
      - wait for the operation to complete before returning
    type: bool
    required: false
    default: true
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
  state:
    description:
      - Indicate desired state of the resource
    required: false
    default: "present"
    choices: ["present", "absent"]

requirements: [ "profitbricks" ]
author: Matt Baldwin (baldwin@stackpointcloud.com)
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
    state: absent

'''

HAS_PB_SDK = True
try:
    from profitbricks import __version__ as sdk_version
    from profitbricks.client import ProfitBricksService
except ImportError:
    HAS_PB_SDK = False

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.cloud.profitbricks.profitbricks import uuid_match, wait_for_completion


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
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

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

    volume_response = profitbricks.attach_volume(datacenter, server, volume)

    if wait:
        wait_for_completion(profitbricks, volume_response, wait_timeout, 'attach_volume')

    return volume_response


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
            datacenter=dict(type='str'),
            server=dict(type='str'),
            volume=dict(type='str'),
            api_url=dict(type='str', default=None),
            username=dict(
                required=True,
                aliases=['subscription_user'],
                fallback=(env_fallback, ['PROFITBRICKS_USERNAME'])
            ),
            password=dict(
                required=True,
                aliases=['subscription_password'],
                fallback=(env_fallback, ['PROFITBRICKS_PASSWORD']),
                no_log=True
            ),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=600),
            state=dict(type='str', default='present', choices=['present', 'absent']),
        )
    )

    if not HAS_PB_SDK:
        module.fail_json(msg='profitbricks required for this module')

    if not module.params.get('datacenter'):
        module.fail_json(msg='datacenter parameter is required')
    if not module.params.get('server'):
        module.fail_json(msg='server parameter is required')
    if not module.params.get('volume'):
        module.fail_json(msg='volume parameter is required')

    if module.check_mode:
        module.exit_json(changed=True)

    username = module.params.get('username')
    password = module.params.get('password')
    api_url = module.params.get('api_url')

    if not api_url:
        profitbricks = ProfitBricksService(username=username, password=password)
    else:
        profitbricks = ProfitBricksService(
            username=username,
            password=password,
            host_base=api_url
        )

    user_agent = 'profitbricks-sdk-python/%s Ansible/%s' % (sdk_version, module.ansible_version)
    profitbricks.headers = {'User-Agent': user_agent}

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
