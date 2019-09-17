#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: meraki_device
short_description: Manage devices in the Meraki cloud
version_added: "2.7"
description:
- Visibility into devices associated to a Meraki environment.
notes:
- This module does not support claiming of devices or licenses into a Meraki organization.
- More information about the Meraki API can be found at U(https://dashboard.meraki.com/api_docs).
- Some of the options are likely only used for developers within Meraki.
options:
    state:
        description:
        - Query an organization.
        choices: [absent, present, query]
        default: query
    org_name:
        description:
        - Name of organization.
        - If C(clone) is specified, C(org_name) is the name of the new organization.
        aliases: [ organization ]
    org_id:
        description:
        - ID of organization.
    net_name:
        description:
        - Name of a network.
        aliases: [network]
    net_id:
        description:
        - ID of a network.
    serial:
        description:
        - Serial number of a device to query.
    hostname:
        description:
        - Hostname of network device to search for.
        aliases: [name]
    model:
        description:
        - Model of network device to search for.
    tags:
        description:
        - Space delimited list of tags to assign to device.
    lat:
        description:
        - Latitude of device's geographic location.
        - Use negative number for southern hemisphere.
        aliases: [latitude]
    lng:
        description:
        - Longitude of device's geographic location.
        - Use negative number for western hemisphere.
        aliases: [longitude]
    address:
        description:
        - Postal address of device's location.
    move_map_marker:
        description:
        - Whether or not to set the latitude and longitude of a device based on the new address.
        - Only applies when C(lat) and C(lng) are not specified.
        type: bool
    serial_lldp_cdp:
        description:
        - Serial number of device to query LLDP/CDP information from.
    lldp_cdp_timespan:
        description:
        - Timespan, in seconds, used to query LLDP and CDP information.
        - Must be less than 1 month.
    serial_uplink:
        description:
        - Serial number of device to query uplink information from.
    note:
        description:
        - Informational notes about a device.
        - Limited to 255 characters.
        version_added: '2.8'


author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Query all devices in an organization.
  meraki_device:
    auth_key: abc12345
    org_name: YourOrg
    state: query
  delegate_to: localhost

- name: Query all devices in a network.
  meraki_device:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    state: query
  delegate_to: localhost

- name: Query a device by serial number.
  meraki_device:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    serial: ABC-123
    state: query
  delegate_to: localhost

- name: Lookup uplink information about a device.
  meraki_device:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    serial_uplink: ABC-123
    state: query
  delegate_to: localhost

- name: Lookup LLDP and CDP information about devices connected to specified device.
  meraki_device:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    serial_lldp_cdp: ABC-123
    state: query
  delegate_to: localhost

- name: Lookup a device by hostname.
  meraki_device:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    hostname: main-switch
    state: query
  delegate_to: localhost

- name: Query all devices of a specific model.
  meraki_device:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    model: MR26
    state: query
  delegate_to: localhost

- name: Update information about a device.
  meraki_device:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: present
    serial: '{{serial}}'
    name: mr26
    address: 1060 W. Addison St., Chicago, IL
    lat: 41.948038
    lng: -87.65568
    tags: recently-added
  delegate_to: localhost

- name: Claim a device into a network.
  meraki_device:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    serial: ABC-123
    state: present
  delegate_to: localhost

- name: Remove a device from a network.
  meraki_device:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    serial: ABC-123
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
response:
    description: Data returned from Meraki dashboard.
    type: dict
    returned: info
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def format_tags(tags):
    return " {tags} ".format(tags=tags)


def is_device_valid(meraki, serial, data):
    for device in data:
        if device['serial'] == serial:
            return True
    return False


def get_org_devices(meraki, org_id):
    path = meraki.construct_path('get_all_org', org_id=org_id)
    response = meraki.request(path, method='GET')
    if meraki.status != 200:
        meraki.fail_json(msg='Failed to query all devices belonging to the organization')
    return response


def main():

    # define the available arguments/parameters that a user can pass to
    # the module
    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present', 'query'], default='query'),
                         net_name=dict(type='str', aliases=['network']),
                         net_id=dict(type='str'),
                         serial=dict(type='str'),
                         serial_uplink=dict(type='str'),
                         serial_lldp_cdp=dict(type='str'),
                         lldp_cdp_timespan=dict(type='int'),
                         hostname=dict(type='str', aliases=['name']),
                         model=dict(type='str'),
                         tags=dict(type='str'),
                         lat=dict(type='float', aliases=['latitude']),
                         lng=dict(type='float', aliases=['longitude']),
                         address=dict(type='str'),
                         move_map_marker=dict(type='bool'),
                         note=dict(type='str'),
                         )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )
    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )
    meraki = MerakiModule(module, function='device')

    if meraki.params['serial_lldp_cdp'] and not meraki.params['lldp_cdp_timespan']:
        meraki.fail_json(msg='lldp_cdp_timespan is required when querying LLDP and CDP information')
    if meraki.params['net_name'] and meraki.params['net_id']:
        meraki.fail_json(msg='net_name and net_id are mutually exclusive')

    meraki.params['follow_redirects'] = 'all'

    query_urls = {'device': '/networks/{net_id}/devices'}
    query_org_urls = {'device': '/organizations/{org_id}/inventory'}
    query_device_urls = {'device': '/networks/{net_id}/devices/'}
    claim_device_urls = {'device': '/networks/{net_id}/devices/claim'}
    bind_org_urls = {'device': '/organizations/{org_id}/claim'}
    update_device_urls = {'device': '/networks/{net_id}/devices/'}
    delete_device_urls = {'device': '/networks/{net_id}/devices/'}

    meraki.url_catalog['get_all'].update(query_urls)
    meraki.url_catalog['get_all_org'] = query_org_urls
    meraki.url_catalog['get_device'] = query_device_urls
    meraki.url_catalog['create'] = claim_device_urls
    meraki.url_catalog['bind_org'] = bind_org_urls
    meraki.url_catalog['update'] = update_device_urls
    meraki.url_catalog['delete'] = delete_device_urls

    payload = None

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    # FIXME: Work with Meraki so they can implement a check mode
    if module.check_mode:
        meraki.exit_json(**meraki.result)

    # execute checks for argument completeness

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    org_id = meraki.params['org_id']
    if org_id is None:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    nets = meraki.get_nets(org_id=org_id)
    net_id = None
    if meraki.params['net_id'] or meraki.params['net_name']:
        net_id = meraki.params['net_id']
        if net_id is None:
            net_id = meraki.get_net_id(net_name=meraki.params['net_name'], data=nets)

    if meraki.params['state'] == 'query':
        if meraki.params['net_name'] or meraki.params['net_id']:
            device = []
            if meraki.params['serial']:
                path = meraki.construct_path('get_device', net_id=net_id) + meraki.params['serial']
                request = meraki.request(path, method='GET')
                device.append(request)
                meraki.result['data'] = device
            elif meraki.params['serial_uplink']:
                path = meraki.construct_path('get_device', net_id=net_id) + meraki.params['serial_uplink'] + '/uplink'
                meraki.result['data'] = (meraki.request(path, method='GET'))
            elif meraki.params['serial_lldp_cdp']:
                if meraki.params['lldp_cdp_timespan'] > 2592000:
                    meraki.fail_json(msg='LLDP/CDP timespan must be less than a month (2592000 seconds)')
                path = meraki.construct_path('get_device', net_id=net_id) + meraki.params['serial_lldp_cdp'] + '/lldp_cdp'
                path = path + '?timespan=' + str(meraki.params['lldp_cdp_timespan'])
                device.append(meraki.request(path, method='GET'))
                meraki.result['data'] = device
            elif meraki.params['hostname']:
                path = meraki.construct_path('get_all', net_id=net_id)
                devices = meraki.request(path, method='GET')
                for unit in devices:
                    if unit['name'] == meraki.params['hostname']:
                        device.append(unit)
                        meraki.result['data'] = device
            elif meraki.params['model']:
                path = meraki.construct_path('get_all', net_id=net_id)
                devices = meraki.request(path, method='GET')
                device_match = []
                for device in devices:
                    if device['model'] == meraki.params['model']:
                        device_match.append(device)
                meraki.result['data'] = device_match
            else:
                path = meraki.construct_path('get_all', net_id=net_id)
                request = meraki.request(path, method='GET')
                meraki.result['data'] = request
        else:
            path = meraki.construct_path('get_all_org', org_id=org_id)
            devices = meraki.request(path, method='GET')
            if meraki.params['serial']:
                for device in devices:
                    if device['serial'] == meraki.params['serial']:
                        meraki.result['data'] = device
            else:
                meraki.result['data'] = devices
    elif meraki.params['state'] == 'present':
        device = []
        if meraki.params['hostname']:
            query_path = meraki.construct_path('get_all', net_id=net_id)
            device_list = meraki.request(query_path, method='GET')
            if is_device_valid(meraki, meraki.params['serial'], device_list):
                payload = {'name': meraki.params['hostname'],
                           'tags': format_tags(meraki.params['tags']),
                           'lat': meraki.params['lat'],
                           'lng': meraki.params['lng'],
                           'address': meraki.params['address'],
                           'moveMapMarker': meraki.params['move_map_marker'],
                           'notes': meraki.params['note'],
                           }
                query_path = meraki.construct_path('get_device', net_id=net_id) + meraki.params['serial']
                device_data = meraki.request(query_path, method='GET')
                ignore_keys = ['lanIp', 'serial', 'mac', 'model', 'networkId', 'moveMapMarker', 'wan1Ip', 'wan2Ip']
                if meraki.is_update_required(device_data, payload, optional_ignore=ignore_keys):
                    path = meraki.construct_path('update', net_id=net_id) + meraki.params['serial']
                    updated_device = []
                    updated_device.append(meraki.request(path, method='PUT', payload=json.dumps(payload)))
                    meraki.result['data'] = updated_device
                    meraki.result['changed'] = True
        else:
            if net_id is None:
                device_list = get_org_devices(meraki, org_id)
                if is_device_valid(meraki, meraki.params['serial'], device_list) is False:
                    payload = {'serial': meraki.params['serial']}
                    path = meraki.construct_path('bind_org', org_id=org_id)
                    created_device = []
                    created_device.append(meraki.request(path, method='POST', payload=json.dumps(payload)))
                    meraki.result['data'] = created_device
                    meraki.result['changed'] = True
            else:
                query_path = meraki.construct_path('get_all', net_id=net_id)
                device_list = meraki.request(query_path, method='GET')
                if is_device_valid(meraki, meraki.params['serial'], device_list) is False:
                    if net_id:
                        payload = {'serial': meraki.params['serial']}
                        path = meraki.construct_path('create', net_id=net_id)
                        created_device = []
                        created_device.append(meraki.request(path, method='POST', payload=json.dumps(payload)))
                        meraki.result['data'] = created_device
                        meraki.result['changed'] = True
    elif meraki.params['state'] == 'absent':
        device = []
        query_path = meraki.construct_path('get_all', net_id=net_id)
        device_list = meraki.request(query_path, method='GET')
        if is_device_valid(meraki, meraki.params['serial'], device_list) is True:
            path = meraki.construct_path('delete', net_id=net_id)
            path = path + meraki.params['serial'] + '/remove'
            request = meraki.request(path, method='POST')
            meraki.result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
