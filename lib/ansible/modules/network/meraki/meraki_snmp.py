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
module: meraki_snmp
short_description: Manage organizations in the Meraki cloud
version_added: "2.6"
description:
- Allows for management of SNMP settings for Meraki.
options:
    state:
        description:
        - Specifies whether SNMP information should be queried or modified.
        choices: ['query', 'present']
        default: present
    v2c_enabled:
        description:
        - Specifies whether SNMPv2c is enabled.
        type: bool
    v3_enabled:
        description:
        - Specifies whether SNMPv3 is enabled.
        type: bool
    v3_auth_mode:
        description:
        - Sets authentication mode for SNMPv3.
        choices: ['MD5', 'SHA']
    v3_auth_pass:
        description:
        - Authentication password for SNMPv3.
        - Must be at least 8 characters long.
    v3_priv_mode:
        description:
        - Specifies privacy mode for SNMPv3.
        choices: ['DES', 'AES128']
    v3_priv_pass:
        description:
        - Privacy password for SNMPv3.
        - Must be at least 8 characters long.
    peer_ips:
        description:
        - Semi-colon delimited IP addresses which can perform SNMP queries.
    net_name:
        description:
        - Name of network.
        type: str
        version_added: '2.9'
    net_id:
        description:
        - ID of network.
        type: str
        version_added: '2.9'
    access:
        description:
        - Type of SNMP access.
        choices: [community, none, users]
        type: str
        version_added: '2.9'
    community_string:
        description:
        - SNMP community string.
        - Only relevant if C(access) is set to C(community).
        type: str
        version_added: '2.9'
    users:
        description:
        - Information about users with access to SNMP.
        - Only relevant if C(access) is set to C(users).
        type: list
        version_added: '2.9'
        suboptions:
            username:
                description: Username of user with access.
                type: str
                version_added: '2.9'
            passphrase:
                description: Passphrase for user SNMP access.
                type: str
                version_added: '2.9'
author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Query SNMP values
  meraki_snmp:
    auth_key: abc12345
    org_name: YourOrg
    state: query
  delegate_to: localhost

- name: Enable SNMPv2
  meraki_snmp:
    auth_key: abc12345
    org_name: YourOrg
    state: present
    v2c_enabled: yes
  delegate_to: localhost

- name: Disable SNMPv2
  meraki_snmp:
    auth_key: abc12345
    org_name: YourOrg
    state: present
    v2c_enabled: no
  delegate_to: localhost

- name: Enable SNMPv3
  meraki_snmp:
    auth_key: abc12345
    org_name: YourOrg
    state: present
    v3_enabled: true
    v3_auth_mode: SHA
    v3_auth_pass: ansiblepass
    v3_priv_mode: AES128
    v3_priv_pass: ansiblepass
    peer_ips: 192.0.1.1;192.0.1.2
  delegate_to: localhost

- name: Set network access type to community string
  meraki_snmp:
    auth_key: abc1235
    org_name: YourOrg
    net_name: YourNet
    state: present
    access: community
    community_string: abc123
  delegate_to: localhost

- name: Set network access type to username
  meraki_snmp:
    auth_key: abc1235
    org_name: YourOrg
    net_name: YourNet
    state: present
    access: users
    users:
      - username: ansibleuser
        passphrase: ansiblepass
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Information about SNMP settings.
    type: complex
    returned: always
    contains:
        hostname:
            description: Hostname of SNMP server.
            returned: success and no network specified.
            type: str
            sample: n1.meraki.com
        peerIps:
            description: Semi-colon delimited list of IPs which can poll SNMP information.
            returned: success and no network specified.
            type: str
            sample: 192.0.1.1
        port:
            description: Port number of SNMP.
            returned: success and no network specified.
            type: str
            sample: 16100
        v2c_enabled:
            description: Shows enabled state of SNMPv2c
            returned: success and no network specified.
            type: bool
            sample: true
        v3_enabled:
            description: Shows enabled state of SNMPv3
            returned: success and no network specified.
            type: bool
            sample: true
        v3_auth_mode:
            description: The SNMP version 3 authentication mode either MD5 or SHA.
            returned: success and no network specified.
            type: str
            sample: SHA
        v3_priv_mode:
            description: The SNMP version 3 privacy mode DES or AES128.
            returned: success and no network specified.
            type: str
            sample: AES128
        v2_community_string:
            description: Automatically generated community string for SNMPv2c.
            returned: When SNMPv2c is enabled and no network specified.
            type: str
            sample: o/8zd-JaSb
        v3_user:
            description: Automatically generated username for SNMPv3.
            returned: When SNMPv3c is enabled and no network specified.
            type: str
            sample: o/8zd-JaSb
        access:
            description: Type of SNMP access.
            type: str
            returned: success, when network specified
        community_string:
            description: SNMP community string. Only relevant if C(access) is set to C(community).
            type: str
            returned: success, when network specified
        users:
            description: Information about users with access to SNMP. Only relevant if C(access) is set to C(users).
            type: complex
            contains:
                username:
                    description: Username of user with access.
                    type: str
                    returned: success, when network specified
                passphrase:
                    description: Passphrase for user SNMP access.
                    type: str
                    returned: success, when network specified
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import recursive_diff, snake_dict_to_camel_dict
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def get_snmp(meraki, org_id):
    path = meraki.construct_path('get_all', org_id=org_id)
    r = meraki.request(path,
                       method='GET',
                       )
    if meraki.status == 200:
        return r


def set_snmp(meraki, org_id):
    payload = dict()
    if meraki.params['peer_ips']:
        if len(meraki.params['peer_ips']) > 7:
            if ';' not in meraki.params['peer_ips']:
                meraki.fail_json(msg='Peer IP addresses are semi-colon delimited.')
    if meraki.params['v2c_enabled'] is not None:
        payload = {'v2cEnabled': meraki.params['v2c_enabled'],
                   }
    if meraki.params['v3_enabled'] is True:
        if len(meraki.params['v3_auth_pass']) < 8 or len(meraki.params['v3_priv_pass']) < 8:
            meraki.fail_json(msg='v3_auth_pass and v3_priv_pass must both be at least 8 characters long.')
        if (meraki.params['v3_auth_mode'] is None or
                meraki.params['v3_auth_pass'] is None or
                meraki.params['v3_priv_mode'] is None or
                meraki.params['v3_priv_pass'] is None):
            meraki.fail_json(msg='v3_auth_mode, v3_auth_pass, v3_priv_mode, and v3_auth_pass are required')
        payload = {'v3Enabled': meraki.params['v3_enabled'],
                   'v3AuthMode': meraki.params['v3_auth_mode'].upper(),
                   'v3AuthPass': meraki.params['v3_auth_pass'],
                   'v3PrivMode': meraki.params['v3_priv_mode'].upper(),
                   'v3PrivPass': meraki.params['v3_priv_pass'],
                   }
        if meraki.params['peer_ips'] is not None:
            payload['peerIps'] = meraki.params['peer_ips']
    elif meraki.params['v3_enabled'] is False:
        payload = {'v3Enabled': False}
    full_compare = snake_dict_to_camel_dict(payload)
    path = meraki.construct_path('create', org_id=org_id)
    snmp = get_snmp(meraki, org_id)
    ignored_parameters = ['v3AuthPass', 'v3PrivPass', 'hostname', 'port', 'v2CommunityString', 'v3User']
    if meraki.is_update_required(snmp, full_compare, optional_ignore=ignored_parameters):
        if meraki.module.check_mode is True:
            diff = recursive_diff(snmp, full_compare)
            snmp.update(payload)
            meraki.result['data'] = snmp
            meraki.result['changed'] = True
            meraki.result['diff'] = {'before': diff[0],
                                     'after': diff[1]}
            meraki.exit_json(**meraki.result)
        r = meraki.request(path,
                           method='PUT',
                           payload=json.dumps(payload))
        if meraki.status == 200:
            diff = recursive_diff(snmp, r)
            meraki.result['diff'] = {'before': diff[0],
                                     'after': diff[1]}
            meraki.result['changed'] = True
            return r
    else:
        return snmp


def main():

    # define the available arguments/parameters that a user can pass to
    # the module
    user_arg_spec = dict(username=dict(type='str'),
                         passphrase=dict(type='str', no_log=True),
                         )

    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['present', 'query'], default='present'),
                         v2c_enabled=dict(type='bool'),
                         v3_enabled=dict(type='bool'),
                         v3_auth_mode=dict(type='str', choices=['SHA', 'MD5']),
                         v3_auth_pass=dict(type='str', no_log=True),
                         v3_priv_mode=dict(type='str', choices=['DES', 'AES128']),
                         v3_priv_pass=dict(type='str', no_log=True),
                         peer_ips=dict(type='str'),
                         access=dict(type='str', choices=['none', 'community', 'users']),
                         community_string=dict(type='str', no_log=True),
                         users=dict(type='list', default=None, element='str', options=user_arg_spec),
                         net_name=dict(type='str'),
                         net_id=dict(type='str'),
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
    meraki = MerakiModule(module, function='snmp')
    meraki.params['follow_redirects'] = 'all'

    query_urls = {'snmp': '/organizations/{org_id}/snmp'}
    query_net_urls = {'snmp': '/networks/{net_id}/snmpSettings'}
    update_urls = {'snmp': '/organizations/{org_id}/snmp'}
    update_net_urls = {'snmp': '/networks/{net_id}/snmpSettings'}

    meraki.url_catalog['get_all'].update(query_urls)
    meraki.url_catalog['query_net_all'] = query_net_urls
    meraki.url_catalog['create'] = update_urls
    meraki.url_catalog['create_net'] = update_net_urls

    payload = None

    if not meraki.params['org_name'] and not meraki.params['org_id']:
        meraki.fail_json(msg='org_name or org_id is required')

    org_id = meraki.params['org_id']
    if org_id is None:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    net_id = meraki.params['net_id']
    if net_id is None and meraki.params['net_name']:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(org_id, meraki.params['net_name'], data=nets)

    if meraki.params['state'] == 'present':
        if net_id is not None:
            payload = {'access': meraki.params['access']}
            if meraki.params['community_string'] is not None:
                payload['communityString'] = meraki.params['community_string']
            elif meraki.params['users'] is not None:
                payload['users'] = meraki.params['users']

    if meraki.params['state'] == 'query':
        if net_id is None:
            meraki.result['data'] = get_snmp(meraki, org_id)
        else:
            path = meraki.construct_path('query_net_all', net_id=net_id)
            response = meraki.request(path, method='GET')
            if meraki.status == 200:
                meraki.result['data'] = response
    elif meraki.params['state'] == 'present':
        if net_id is None:
            meraki.result['data'] = set_snmp(meraki, org_id)
        else:
            path = meraki.construct_path('query_net_all', net_id=net_id)
            original = meraki.request(path, method='GET')
            if meraki.is_update_required(original, payload):
                path = meraki.construct_path('create_net', net_id=net_id)
                response = meraki.request(path, method='PUT', payload=json.dumps(payload))
                if meraki.status == 200:
                    if response['access'] == 'none':
                        meraki.result['data'] = {}
                    else:
                        meraki.result['data'] = response
                    meraki.result['changed'] = True
            else:
                meraki.result['data'] = original

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
