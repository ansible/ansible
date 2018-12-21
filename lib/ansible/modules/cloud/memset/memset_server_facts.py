#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, Simon Weald <ansible@simonweald.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: memset_server_facts
author: "Simon Weald (@glitchcrab)"
version_added: "2.8"
short_description: Retrieve server information.
notes:
    - An API key generated via the Memset customer control panel is needed with the
      following minimum scope - I(server.info).
description:
    - Retrieve server information.
options:
    api_key:
        required: true
        description:
            - The API key obtained from the Memset control panel.
    name:
        required: true
        description:
            - The server product name (i.e. C(testyaa1)).
'''

EXAMPLES = '''
- name: get details for testyaa1
  memset_server_facts:
    name: testyaa1
    api_key: 5eb86c9896ab03919abcf03857163741
  delegate_to: localhost
'''

RETURN = '''
---
memset_api:
  description: Info from the Memset API
  returned: always
  type: complex
  contains:
    backups:
      description: Whether this server has a backup service.
      returned: always
      type: bool
      sample: true
    control_panel:
      description: Whether the server has a control panel (i.e. cPanel).
      returned: always
      type: str
      sample: 'cpanel'
    data_zone:
      description: The data zone the server is in.
      returned: always
      type: str
      sample: 'Memset Public Cloud'
    expiry_date:
      description: Current expiry date of the server.
      returned: always
      type: str
      sample: '2018-08-10'
    firewall_rule_group:
      description: Details about the firewall group this server is in.
      returned: always
      type: dict
      sample: {
        "default_outbound_policy": "RETURN",
        "name": "testyaa-fw1",
        "nickname": "testyaa cPanel rules",
        "notes": "",
        "public": false,
        "rules": {
          "51d7db54d39c3544ef7c48baa0b9944f": {
            "action": "ACCEPT",
            "comment": "",
            "dest_ip6s": "any",
            "dest_ips": "any",
            "dest_ports": "any",
            "direction": "Inbound",
            "ip_version": "any",
            "ordering": 2,
            "protocols": "icmp",
            "rule_group_name": "testyaa-fw1",
            "rule_id": "51d7db54d39c3544ef7c48baa0b9944f",
            "source_ip6s": "any",
            "source_ips": "any",
            "source_ports": "any"
          }
        }
      }
    firewall_type:
      description: The type of firewall the server has (i.e. self-managed, managed).
      returned: always
      type: str
      sample: 'managed'
    host_name:
      description: The server's hostname.
      returned: always
      type: str
      sample: 'testyaa1.miniserver.com'
    ignore_monitoring_off:
      description: When true, Memset won't remind the customer that monitoring is disabled.
      returned: always
      type: bool
      sample: true
    ips:
      description: List of dictionaries of all IP addresses assigned to the server.
      returned: always
      type: list
      sample: [
        {
          "address": "1.2.3.4",
          "bytes_in_today": 1000.0,
          "bytes_in_yesterday": 2000.0,
          "bytes_out_today": 1000.0,
          "bytes_out_yesterday": 2000.0
        }
      ]
    monitor:
      description: Whether the server has monitoring enabled.
      returned: always
      type: bool
      sample: true
    monitoring_level:
      description: The server's monitoring level (i.e. basic).
      returned: always
      type: str
      sample: 'basic'
    name:
      description: Server name (same as the service name).
      returned: always
      type: str
      sample: 'testyaa1'
    network_zones:
      description: The network zone(s) the server is in.
      returned: always
      type: list
      sample: [ 'reading' ]
    nickname:
      description: Customer-set nickname for the server.
      returned: always
      type: str
      sample: 'database server'
    no_auto_reboot:
      description: Whether or not to reboot the server if monitoring detects it down.
      returned: always
      type: bool
      sample: true
    no_nrpe:
      description: Whether Memset should use NRPE to monitor this server.
      returned: always
      type: bool
      sample: true
    os:
      description: The server's Operating System.
      returned: always
      type: str
      sample: 'debian_stretch_64'
    penetration_patrol:
      description: Intrusion detection support level for this server.
      returned: always
      type: str
      sample: 'managed'
    penetration_patrol_alert_level:
      description: The alert level at which notifications are sent.
      returned: always
      type: int
      sample: 10
    primary_ip:
      description: Server's primary IP.
      returned: always
      type: str
      sample: '1.2.3.4'
    renewal_price_amount:
      description: Renewal cost for the server.
      returned: always
      type: str
      sample: '30.00'
    renewal_price_currency:
      description: Currency for renewal payments.
      returned: always
      type: str
      sample: 'GBP'
    renewal_price_vat:
      description: VAT rate for renewal payments
      returned: always
      type: str
      sample: '20'
    start_date:
      description: Server's start date.
      returned: always
      type: str
      sample: '2013-04-10'
    status:
      description: Current status of the server (i.e. live, onhold).
      returned: always
      type: str
      sample: 'LIVE'
    support_level:
      description: Support level included with the server.
      returned: always
      type: str
      sample: 'managed'
    type:
      description: What this server is (i.e. dedicated)
      returned: always
      type: str
      sample: 'miniserver'
    vlans:
      description: Dictionary of tagged and untagged VLANs this server is in.
      returned: always
      type: dict
      sample: {
        tagged: [],
        untagged: [ 'testyaa-vlan1', 'testyaa-vlan2' ]
      }
    vulnscan:
      description: Vulnerability scanning level.
      returned: always
      type: str
      sample: 'basic'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.memset import memset_api_call


def get_facts(args=None):
    '''
    Performs a simple API call and returns a JSON blob.
    '''
    retvals, payload = dict(), dict()
    has_changed, has_failed = False, False
    msg, stderr, memset_api = None, None, None

    payload['name'] = args['name']

    api_method = 'server.info'
    has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)

    if has_failed:
        # this is the first time the API is called; incorrect credentials will
        # manifest themselves at this point so we need to ensure the user is
        # informed of the reason.
        retvals['failed'] = has_failed
        retvals['msg'] = msg
        retvals['stderr'] = "API returned an error: {0}" . format(response.status_code)
        return(retvals)

    # we don't want to return the same thing twice
    msg = None
    memset_api = response.json()

    retvals['changed'] = has_changed
    retvals['failed'] = has_failed
    for val in ['msg', 'memset_api']:
        if val is not None:
            retvals[val] = eval(val)

    return(retvals)


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True, type='str', no_log=True),
            name=dict(required=True, type='str')
        ),
        supports_check_mode=False
    )

    # populate the dict with the user-provided vars.
    args = dict()
    for key, arg in module.params.items():
        args[key] = arg

    retvals = get_facts(args)

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)


if __name__ == '__main__':
    main()
