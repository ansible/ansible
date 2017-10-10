#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Opsview Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: opsview_host
short_description: Manages Opsview hosts
description:
  - Manages hosts within Opsview.
version_added: '2.5'
author: Joshua Griffiths (@jpgxs)
requirements: [pyopsview]
options:
  username:
    description:
      - Username for the Opsview API.
    required: true
  endpoint:
    description:
      - Opsview API endpoint, including schema.
      - The C(/rest) suffix is optional.
    required: true
  token:
    description:
      - API token, usually returned by the C(opsview_login) module.
      - Required unless C(password) is specified.
  password:
    description:
      - Password for the Opsview API.
  verify_ssl:
    description:
      - Enable SSL verification for HTTPS endpoints.
      - Alternatively, a path to a CA can be provided.
    default: 'yes'
  state:
    description:
      - C(present) and C(updated) will create the object if it doesn't exist.
      - C(updated) will ensure that the object attributes are up to date with
        the given options.
      - C(absent) will ensure that the object is removed if it exists.
      - The object is identified by C(object_id) if specified. Otherwise, it is
        identified by C(name)
    choices: [updated, present, absent]
    default: updated
  object_id:
    description:
      - The internal ID of the object. If specified, the object will be
        found by ID instead of by C(name).
      - Usually only useful for renaming objects.
  name:
    description:
      - Unique name for the object. Will be used to identify existing objects
        unless C(object_id) is specified.
    required: true
  address:
    description:
      - Primary network address for the host.
    required: true
  host_group:
    description:
      - Host group to assign this host to.
    required: true
  monitored_by:
    description:
      - The monitoring server/cluster which will monitor this host.
    default: Master Monitoring Server
  alias:
    description:
      - Alternative name for this host as shown in the UI.
  check_attempts:
    description:
      - The number of checks before the host enters a HARD state.
    default: '2'
  check_command:
    description:
      - Name of the command used for monitoring this host.
    default: ping
  check_interval:
    description:
      - Number of seconds between each host check execution.
    default: '600'
  check_period:
    description:
      - Timeperiod within which this host will be monitored.
    default: 24x7
  description:
    description:
      - User-defined description for this host.
  enable_snmp:
    description:
      - Enable active SNMP checks for this host.
    choices: ['yes', 'no']
  encrypted_rancid_password:
    description:
      - The password for logging into the host with RANCID.
      - Must be pre-encrypted with the opsview_crypt utility.
  encrypted_snmp_community:
    description:
      - The community string to be used with SNMP 1/2c
      - Must be pre-encrypted with the opsview_crypt utility.
  encrypted_snmpv3_auth_password:
    description:
      - The authentication password to be used with SNMP v3
      - Must be pre-encrypted with the opsview_crypt utility.
  encrypted_snmpv3_priv_password:
    description:
      - The privacy password to be used with SNMP v3
      - Must be pre-encrypted with the opsview_crypt utility.
  event_handler:
    description:
      - Script to execute whenever a state change occurs for this host.
  event_handler_always_exec:
    description:
      - Execute the event handler after every check result.
    choices: ['yes', 'no']
  flap_detection_enabled:
    description:
      - Enable flapping states for this host.
    default: 'yes'
    choices: ['yes', 'no']
  hashtags:
    description:
      - List of Hashtags to be applied to this host.
  host_templates:
    description:
      - List of Host Templates to be applied to this host
  icon:
    description:
      - The name of the icon to be used for this host.
  notification_interval:
    description:
      - Number of seconds between sending re-notifications for this host when
        it is in DOWN or UNREACHABLE states.
  notification_options:
    description:
      - Comma-separated list of states to notify on.
      - C(u)=UNREACHABLE, C(d)=DOWN, C(r)=RECOVERY, C(f)=FLAPPING.
    default: u,d,r
  notification_period:
    description:
      - Timeperiod within which notifications for this host will be sent.
    default: 24x7
  other_addresses:
    description:
      - Comma-separated list of additional network addresses for this host.
  parents:
    description:
      - List of host names (as configured in Opsview) which directly determine
        the reachability of this host. For example, the network switches
        connected to this host.
  rancid_auto_enable:
    description:
      - Host has autoenable when connecting to this host with RANCID.
    choices: ['yes', 'no']
  rancid_connection_type:
    description:
      - Method used for connecting to this host with RANCID.
    choices: [ssh, telnet]
    default: ssh
  rancid_password:
    description:
      - Password for logging into the host with RANCID.
      - C(encrypted_rancid_password) is preferred.
  rancid_username:
    description:
      - Username for logging into the host with RANCID.
  rancid_vendor:
    description:
      - The host's vendor, as configured in RANCID. You may have to consult the
        UI for the full list of options.
  retry_check_interval:
    description:
      - Number of seconds between rechecks before a HARD state.
  service_checks:
    description:
      - A list of discrete Service Checks to add to the host, aside from those
        specified via Host Templates.
      - See examples for the argument format.
  snmp_community:
    description:
      - The community string to be used with SNMP 1/2c.
      - C(encrypted_snmp_community) is preferred.
  snmp_extended_throughput_data:
    description:
      - Turn on the collection of broadcast, multicast and and unicast stats.
    choices: ['yes', 'no']
  snmp_max_msg_size:
    description:
      - The maximum message size, in octets, for SNMP messages. For default,
        use 0.
    default: '0'
  snmp_port:
    description:
      - The listening SNMP port on the host.
    default: '161'
  snmp_use_getnext:
    description:
      - Use SNMP C(GetNext) instead of SNMP C(GetBulk).
    choices: ['yes', 'no']
  snmp_use_ifname:
    description:
      - Use SNMP C(ifName) instead of SNMP C(ifDescr).
    choices: ['yes', 'no']
  snmp_version:
    description:
      - The SNMP protocol version to use.
    choices: ['1', '2c', '3']
    default: '2c'
  snmpv3_auth_password:
    description:
      - The authentication password to be used with SNMP v3.
      - C(encrypted_snmpv3_auth_password) is preferred.
  snmpv3_auth_protocol:
    description:
      - The authentication protocol to be used with SNMP v3.
    choices: [md5, sha]
  snmpv3_priv_password:
    description:
      - The privacy password to be used with SNMP v3.
      - C(encrypted_snmpv3_priv_password) is preferred.
  snmpv3_priv_protocol:
    description:
      - The privacy protocol to be used with SNMP v3.
    choices: [des, aes, aes128]
  snmpv3_username:
    description:
      - The username to be used with SNMP v3.
  tidy_ifdescr_level:
    description:
      - Level of cleaning to do on the C(ifDescr) to reduce the length of
        interface names.
      - Refer to https://knowledge.opsview.com/docs/host#section-interfaces
    choices: [0, 1, 2, 3, 4, 5]
  use_rancid:
    description:
      - Enable RANCID.
    choices: ['yes', 'no']
  variables:
    description:
      - List of variables to apply to the host.
      - See the examples for the argument format.
"""

EXAMPLES = """
---
- name: Create Host in Opsview
  opsview_host:
    username: admin
    # Providing a token from the opsview_login module is preferred to using a
    # password and is much faster.
    password: initial
    endpoint: https://opsview.example.com
    state: updated
    name: web-uk-01
    address: 127.214.167.12
    host_group: web-uk
    monitored_by: ov-cluster-uk
    alias: Web UK 01
    hashtags:
      - Production
      - Production - UK
      - Production - UK - Web
    host_templates:
      - Application - Apache2
      - OS - Opsview Agent
      - Network - Base
    icon: SYMBOL - Web Site
    parents:
      - switch-uk-01
      - switch-uk-02
    service_checks:
      # Add a Service Check
      - HTTP / SSL
      # Add a Service Check with alternative arguments
      - name: HTTPS Certificate Expiration Check
        exception: -H $HOSTADDRESS$ -C 30,14
      # Add a Service Check with a timed exception
      - name: Unix Load Average
        timed_exception:
          timeperiod: nonworkhours
          args: -H $HOSTADDRESS$ -c check_load -a '-w 5,4,3 -c 7,6,5'
      # Remove a Service Check from an applied Host Template
      - name: Unix Swap
        remove_service_check: true
    variables:
      # Arguments 1-4 can be provided as argN
      # Encrypted arguments 1-4 can be provided as encrypted_argN
      - name: DISK
        value: /
        arg1: -w 10% -c 5%
      - name: DISK
        value: /var
"""

RETURN = """
---
object_id:
  description: ID of the object in Opsview.
  returned: When not check_mode.
  type: int
"""

import traceback

from ansible.module_utils import opsview as ov
from ansible.module_utils.basic import to_native
from ansible.module_utils.six import string_types

ARG_SPEC = {
    "address": {
        "required": True
    },
    "alias": {},
    "check_attempts": {
        "default": 2,
        "type": "int"
    },
    "check_command": {
        "default": "ping"
    },
    "check_interval": {
        "default": 600,
        "type": "int"
    },
    "check_period": {
        "default": "24x7"
    },
    "description": {},
    "enable_snmp": {
        "type": "bool"
    },
    "encrypted_rancid_password": {
        "no_log": True
    },
    "encrypted_snmp_community": {
        "no_log": True
    },
    "encrypted_snmpv3_auth_password": {
        "no_log": True
    },
    "encrypted_snmpv3_priv_password": {
        "no_log": True
    },
    "endpoint": {
        "required": True
    },
    "event_handler": {},
    "event_handler_always_exec": {
        "type": "bool"
    },
    "flap_detection_enabled": {
        "default": True,
        "type": "bool"
    },
    "hashtags": {
        "type": "list"
    },
    "host_group": {
        "required": True
    },
    "host_templates": {
        "type": "list"
    },
    "icon": {},
    "monitored_by": {
        "default": "Master Monitoring Server"
    },
    "name": {
        "required": True
    },
    "notification_interval": {
        "type": "int"
    },
    "notification_options": {
        "default": "u,d,r"
    },
    "notification_period": {
        "default": "24x7"
    },
    "object_id": {
        "type": "int"
    },
    "other_addresses": {},
    "parents": {
        "type": "list"
    },
    "password": {
        "no_log": True
    },
    "rancid_auto_enable": {
        "type": "bool"
    },
    "rancid_connection_type": {
        "choices": ["ssh", "telnet"],
        "default": "ssh"
    },
    "rancid_password": {
        "no_log": True
    },
    "rancid_username": {},
    "rancid_vendor": {},
    "retry_check_interval": {
        "type": "int"
    },
    "service_checks": {
        "type": "list"
    },
    "snmp_community": {
        "no_log": True
    },
    "snmp_extended_throughput_data": {
        "type": "bool"
    },
    "snmp_max_msg_size": {
        "default": 0,
        "type": "int"
    },
    "snmp_port": {
        "default": 161,
        "type": "int"
    },
    "snmp_use_getnext": {
        "type": "bool"
    },
    "snmp_use_ifname": {
        "type": "bool"
    },
    "snmp_version": {
        "choices": [
            "1",
            "2c",
            "3"
        ],
        "default": "2c"
    },
    "snmpv3_auth_password": {
        "no_log": True
    },
    "snmpv3_auth_protocol": {
        "choices": [
            "md5",
            "sha"
        ]
    },
    "snmpv3_priv_password": {
        "no_log": True
    },
    "snmpv3_priv_protocol": {
        "choices": [
            "des",
            "aes",
            "aes128"
        ]
    },
    "snmpv3_username": {},
    "state": {
        "choices": [
            "updated",
            "present",
            "absent"
        ],
        "default": "updated"
    },
    "tidy_ifdescr_level": {
        "choices": [0, 1, 2, 3, 4, 5],
        "type": "int"
    },
    "token": {
        "no_log": True
    },
    "use_rancid": {
        "type": "bool"
    },
    "username": {
        "required": True
    },
    "variables": {
        "type": "list"
    },
    "verify_ssl": {
        "default": True
    }
}


def hook_trans_payload(params):
    # Ensure that the notification options are duly sorted
    if params.get('notification_options'):
        option_sort_order = {'u': 0, 'd': 1, 'r': 2, 'f': 3}
        notif_opts = params['notification_options'].lower().split(',').sort(
            key=lambda x: option_sort_order.get(x, 99)
        )
        params['notification_options'] = notif_opts

    # Ensure that string value for icon gets passed as the icon name
    if isinstance(params.get('icon'), string_types):
        params['icon'] = {'name': params['icon']}

    return params


def main():
    module = ov.new_module(ARG_SPEC)
    # Handle exception importing 'pyopsview'
    if ov.PYOV_IMPORT_EXC is not None:
        module.fail_json(msg=ov.PYOV_IMPORT_EXC[0],
                         exception=ov.PYOV_IMPORT_EXC[1])

    try:
        summary = ov.config_module_main(
            module, 'hosts',
            get_params={'include_encrypted': '1'},
            pre_compare_hook=hook_trans_payload,
            payload_finalize_hook=hook_trans_payload)

    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(**summary)


if __name__ == '__main__':
    main()
