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
'''

RETURN = r'''
data:
    description: Information about SNMP settings.
    type: complex
    returned: always
    contains:
        hostname:
            description: Hostname of SNMP server.
            returned: success
            type: string
            sample: n1.meraki.com
        peerIps:
            description: Semi-colon delimited list of IPs which can poll SNMP information.
            returned: success
            type: string
            sample: 192.0.1.1
        port:
            description: Port number of SNMP.
            returned: success
            type: string
            sample: 16100
        v2cEnabled:
            description: Shows enabled state of SNMPv2c
            returned: success
            type: bool
            sample: true
        v3Enabled:
            description: Shows enabled state of SNMPv3
            returned: success
            type: bool
            sample: true
        v3AuthMode:
            description: The SNMP version 3 authentication mode either MD5 or SHA.
            returned: success
            type: string
            sample: SHA
        v3PrivMode:
            description: The SNMP version 3 privacy mode DES or AES128.
            returned: success
            type: string
            sample: AES128
        v2CommunityString:
            description: Automatically generated community string for SNMPv2c.
            returned: When SNMPv2c is enabled.
            type: string
            sample: o/8zd-JaSb
        v3User:
            description: Automatically generated username for SNMPv3.
            returned: When SNMPv3c is enabled.
            type: string
            sample: o/8zd-JaSb
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
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
    if meraki.params['v3_enabled'] is not None:
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
                   'peerIps': meraki.params['peer_ips'],
                   }
    full_compare = {'v2cEnabled': meraki.params['v2c_enabled'],
                    'v3Enabled': meraki.params['v3_enabled'],
                    'v3AuthMode': meraki.params['v3_auth_mode'],
                    'v3PrivMode': meraki.params['v3_priv_mode'],
                    'peerIps': meraki.params['peer_ips'],
                    }
    if meraki.params['v3_enabled'] is None:
        full_compare['v3Enabled'] = False
    if meraki.params['v2c_enabled'] is None:
        full_compare['v2cEnabled'] = False
    path = meraki.construct_path('create', org_id=org_id)
    snmp = get_snmp(meraki, org_id)
    ignored_parameters = ('v3AuthPass', 'v3PrivPass', 'hostname', 'port', 'v2CommunityString', 'v3User')
    if meraki.is_update_required(snmp, full_compare, optional_ignore=ignored_parameters):
        r = meraki.request(path,
                           method='PUT',
                           payload=json.dumps(payload))
        if meraki.status == 200:
            meraki.result['changed'] = True
            return r
    return -1


def main():

    # define the available arguments/parameters that a user can pass to
    # the module
    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['present', 'query'], default='present'),
                         org_name=dict(type='str', aliases=['organization']),
                         org_id=dict(type='int'),
                         v2c_enabled=dict(type='bool'),
                         v3_enabled=dict(type='bool'),
                         v3_auth_mode=dict(type='str', choices=['SHA', 'MD5']),
                         v3_auth_pass=dict(type='str', no_log=True),
                         v3_priv_mode=dict(type='str', choices=['DES', 'AES128']),
                         v3_priv_pass=dict(type='str', no_log=True),
                         peer_ips=dict(type='str'),
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

    query_urls = {'snmp': '/organizations/{org_id}/snmp',
                  }

    update_urls = {'snmp': '/organizations/{org_id}/snmp',
                   }

    meraki.url_catalog['get_all'] = query_urls
    meraki.url_catalog['create'] = update_urls

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

    if not meraki.params['org_name'] and not meraki.params['org_id']:
        meraki.fail_json(msg='org_name or org_id is required')

    org_id = meraki.params['org_id']
    if org_id is None:
        org_id = meraki.get_org_id(meraki.params['org_name'])

    if meraki.params['state'] == 'query':
        meraki.result['data'] = get_snmp(meraki, org_id)
    elif meraki.params['state'] == 'present':
        meraki.result['data'] = set_snmp(meraki, org_id)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
