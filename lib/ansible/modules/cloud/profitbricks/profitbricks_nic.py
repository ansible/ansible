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
module: profitbricks_nic
short_description: Create, Update or Remove a NIC.
description:
     - This module allows you to create, update or remove a NIC.
version_added: "2.0"
options:
  datacenter:
    description:
      - The datacenter in which to operate.
    required: true
  server:
    description:
      - The server name or ID.
    required: true
  name:
    description:
      - The name or ID of the NIC. This is only required on deletes, but not on create.
    required: true
  lan:
    description:
      - The LAN to place the NIC on. You can pass a LAN that doesn't exist and it will be created. Required on create.
    required: true
    default: None
  nat:
    description:
      - Boolean value indicating if the private IP address has outbound access to the public internet.
    required: false
    default: None
    version_added: "2.3"
  dhcp:
    description:
      - Boolean value indicating if the NIC is using DHCP or not.
    required: false
    default: None
    version_added: "2.4"
  firewall_active:
    description:
      - Boolean value indicating if the firewall is active.
    required: false
    default: None
    version_added: "2.4"
  ips:
    description:
      - A list of IPs to be assigned to the NIC.
    required: false
    default: None
    version_added: "2.4"
  api_url:
    description:
      - The ProfitBricks API base URL.
    required: false
    default: The value specified by API_HOST variable in ProfitBricks SDK for Python dependency.
    version_added: "2.4"
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
    default: "present"
    choices: ["present", "absent", "update"]

requirements:
    - "python >= 2.6"
    - "profitbricks >= 4.0.0"
author:
    - "Matt Baldwin (baldwin@stackpointcloud.com)"
    - "Ethan Devenport (@edevenport)"
'''

EXAMPLES = '''

# Create a NIC
- profitbricks_nic:
    datacenter: Tardis One
    server: node002
    lan: 2
    wait_timeout: 500
    state: present

# Update a NIC
- profitbricks_nic:
    datacenter: Tardis One
    server: node002
    name: 7341c2454f
    lan: 1
    ips:
      - 158.222.103.23
      - 158.222.103.24
    dhcp: false
    state: update

# Remove a NIC
- profitbricks_nic:
    datacenter: Tardis One
    server: node002
    name: 7341c2454f
    wait_timeout: 500
    state: absent

'''

from uuid import uuid4

HAS_PB_SDK = True

try:
    from profitbricks import API_HOST
    from profitbricks import __version__ as sdk_version
    from profitbricks.client import ProfitBricksService, NIC
except ImportError:
    HAS_PB_SDK = False

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils._text import to_native
from ansible.module_utils.profitbricks import uuid_match, wait_for_completion


def create_nic(module, profitbricks):
    """
    Creates a NIC.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        The NIC instance being created
    """
    datacenter = module.params.get('datacenter')
    server = module.params.get('server')
    lan = module.params.get('lan')
    dhcp = module.params.get('dhcp') or False
    nat = module.params.get('nat') or False
    firewall_active = module.params.get('firewall_active')
    ips = module.params.get('ips')
    name = module.params.get('name')
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

    if module.check_mode:
        module.exit_json(changed=True)

    try:
        n = NIC(
            name=name,
            lan=lan,
            nat=nat,
            dhcp=dhcp,
            ips=ips,
            firewall_active=firewall_active
        )

        nic_response = profitbricks.create_nic(datacenter, server, n)

        if wait:
            wait_for_completion(profitbricks, nic_response,
                                wait_timeout, 'create_nic')

        # Refresh NIC properties
        nic_response = profitbricks.get_nic(datacenter, server, nic_response['id'])

        return nic_response

    except Exception as e:
        module.fail_json(msg="failed to create the NIC: %s" % to_native(e))


def update_nic(module, profitbricks):
    """
    Updates a NIC.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        The NIC instance being updated
    """
    datacenter = module.params.get('datacenter')
    server = module.params.get('server')
    lan = module.params.get('lan')
    nat = module.params.get('nat')
    dhcp = module.params.get('dhcp')
    firewall_active = module.params.get('firewall_active')
    ips = module.params.get('ips')
    name = module.params.get('name')
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

    nic = None
    # Locate NIC to update
    if not (uuid_match.match(name)):
        nic_list = profitbricks.list_nics(datacenter, server)
        for n in nic_list['items']:
            if name == n['properties']['name'] or name == n['id']:
                nic = n
                break

    if not nic:
        module.fail_json(msg="NIC could not be found.")

    if module.check_mode:
        module.exit_json(changed=True)

    try:
        if lan is None:
            lan = nic['properties']['lan']
        if firewall_active is None:
            firewall_active = nic['properties']['firewallActive']
        if nat is None:
            nat = nic['properties']['nat']
        if dhcp is None:
            dhcp = nic['properties']['dhcp']

        nic_response = profitbricks.update_nic(
            datacenter,
            server,
            nic['id'],
            lan=lan,
            firewall_active=firewall_active,
            nat=nat,
            dhcp=dhcp,
            ips=ips
        )

        if wait:
            wait_for_completion(profitbricks, nic_response,
                                wait_timeout, 'update_nic')

        # Refresh NIC properties
        nic_response = profitbricks.get_nic(datacenter, server, nic_response['id'])

        return nic_response

    except Exception as e:
        module.fail_json(msg="failed to update the NIC: %s" % to_native(e))


def delete_nic(module, profitbricks):
    """
    Removes a NIC

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True if the NIC was removed, false otherwise
    """
    datacenter = module.params.get('datacenter')
    server = module.params.get('server')
    name = module.params.get('name')

    # Locate UUID for Datacenter
    if not (uuid_match.match(datacenter)):
        datacenter_list = profitbricks.list_datacenters()
        for d in datacenter_list['items']:
            dc = profitbricks.get_datacenter(d['id'])
            if datacenter == dc['properties']['name']:
                datacenter = d['id']
                break

    # Locate UUID for Server
    server_found = False
    if not (uuid_match.match(server)):
        server_list = profitbricks.list_servers(datacenter)
        for s in server_list['items']:
            if server == s['properties']['name']:
                server_found = True
                server = s['id']
                break

        if not server_found:
            return False

    # Locate UUID for NIC
    nic_found = False
    if not (uuid_match.match(name)):
        nic_list = profitbricks.list_nics(datacenter, server)
        for n in nic_list['items']:
            if name == n['properties']['name']:
                nic_found = True
                name = n['id']
                break

        if not nic_found:
            return False

    if module.check_mode:
        module.exit_json(changed=True)

    try:
        nic_response = profitbricks.delete_nic(datacenter, server, name)
        return nic_response
    except Exception as e:
        module.fail_json(msg="failed to remove the NIC: %s" % to_native(e))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            datacenter=dict(type='str'),
            server=dict(type='str'),
            name=dict(type='str', default=str(uuid4()).replace('-', '')[:10]),
            lan=dict(type='int', default=None),
            dhcp=dict(type='bool', default=None),
            nat=dict(type='bool', default=None),
            firewall_active=dict(type='bool', default=None),
            ips=dict(type='list', default=None),
            api_url=dict(type='str', default=API_HOST),
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
            state=dict(type='str', default='present'),
        ),
        supports_check_mode=True
    )

    if not HAS_PB_SDK:
        module.fail_json(msg='profitbricks required for this module')

    if not module.params.get('datacenter'):
        module.fail_json(msg='datacenter parameter is required')
    if not module.params.get('server'):
        module.fail_json(msg='server parameter is required')

    username = module.params.get('username')
    password = module.params.get('password')
    api_url = module.params.get('api_url')

    profitbricks = ProfitBricksService(
        username=username,
        password=password,
        host_base=api_url
    )

    user_agent = 'profitbricks-sdk-python/%s Ansible/%s' % (sdk_version, module.ansible_version)
    profitbricks.headers = {'User-Agent': user_agent}

    state = module.params.get('state')

    if state == 'absent':
        if not module.params.get('name'):
            module.fail_json(msg='name parameter is required')

        try:
            (changed) = delete_nic(module, profitbricks)
            module.exit_json(changed=changed)
        except Exception as e:
            module.fail_json(msg='failed to set nic state: %s' % to_native(e))

    elif state == 'present':
        if not module.params.get('lan'):
            module.fail_json(msg='lan parameter is required')

        try:
            (nic_dict) = create_nic(module, profitbricks)
            module.exit_json(**nic_dict)
        except Exception as e:
            module.fail_json(msg='failed to set nic state: %s' % to_native(e))

    elif state == 'update':
        try:
            (nic_dict) = update_nic(module, profitbricks)
            module.exit_json(**nic_dict)
        except Exception as e:
            module.fail_json(msg='failed to update nic: %s' % to_native(e))


if __name__ == '__main__':
    main()
