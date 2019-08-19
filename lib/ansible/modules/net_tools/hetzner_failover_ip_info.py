#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: hetzner_failover_ip_info
version_added: "2.9"
short_description: Retrieve information on Hetzner's failover IPs
author:
  - Felix Fontein (@felixfontein)
description:
  - Retrieve information on Hetzner's failover IPs.
seealso:
  - name: Failover IP documentation
    description: Hetzner's documentation on failover IPs.
    link: https://wiki.hetzner.de/index.php/Failover/en
  - module: hetzner_failover_ip
    description: Manage failover IPs.
extends_documentation_fragment:
  - hetzner
options:
  failover_ip:
    description: The failover IP address.
    type: str
    required: yes
'''

EXAMPLES = r'''
- name: Get value of failover IP 1.2.3.4
  hetzner_failover_ip_info:
    hetzner_user: foo
    hetzner_password: bar
    failover_ip: 1.2.3.4
    value: 5.6.7.8
  register: result

- name: Print value of failover IP 1.2.3.4 in case it is routed
  debug:
    msg: "1.2.3.4 routes to {{ result.value }}"
  when: result.state == 'routed'
'''

RETURN = r'''
value:
  description:
    - The value of the failover IP.
    - Will be C(none) if the IP is unrouted.
  returned: success
  type: str
state:
  description:
    - Will be C(routed) or C(unrouted).
  returned: success
  type: str
failover_ip:
  description:
    - The failover IP.
  returned: success
  type: str
  sample: '1.2.3.4'
failover_netmask:
  description:
    - The netmask for the failover IP.
  returned: success
  type: str
  sample: '255.255.255.255'
server_ip:
  description:
    - The main IP of the server this failover IP is associated to.
    - This is I(not) the server the failover IP is routed to.
  returned: success
  type: str
server_number:
  description:
    - The number of the server this failover IP is associated to.
    - This is I(not) the server the failover IP is routed to.
  returned: success
  type: int
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.hetzner import (
    HETZNER_DEFAULT_ARGUMENT_SPEC,
    get_failover_record,
    get_failover_state,
)


def main():
    argument_spec = dict(
        failover_ip=dict(type='str', required=True),
    )
    argument_spec.update(HETZNER_DEFAULT_ARGUMENT_SPEC)
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    failover = get_failover_record(module, module.params['failover_ip'])
    result = get_failover_state(failover['active_server_ip'])
    result['failover_ip'] = failover['ip']
    result['failover_netmask'] = failover['netmask']
    result['server_ip'] = failover['server_ip']
    result['server_number'] = failover['server_number']
    result['changed'] = False
    module.exit_json(**result)


if __name__ == '__main__':
    main()
