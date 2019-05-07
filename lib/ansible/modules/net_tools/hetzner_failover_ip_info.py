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
    hetzner_pass: bar
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
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.hetzner import (
    get_failover,
    get_failover_state,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hetzner_user=dict(type='str', required=True),
            hetzner_pass=dict(type='str', required=True, no_log=True),
            failover_ip=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )

    value = get_failover(module, module.params['failover_ip'])
    result = get_failover_state(value)
    result['changed'] = False
    module.exit_json(**result)


if __name__ == '__main__':
    main()
