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
module: hetzner_failover_ip
version_added: "2.9"
short_description: Manage Hetzner's failover IPs
author:
  - Felix Fontein (@felixfontein)
description:
  - Manage Hetzner's failover IPs.
seealso:
  - name: Failover IP documentation
    description: Hetzner's documentation on failover IPs.
    link: https://wiki.hetzner.de/index.php/Failover/en
  - module: hetzner_failover_ip_info
    description: Retrieve information on failover IPs.
extends_documentation_fragment:
  - hetzner
options:
  failover_ip:
    description: The failover IP address.
    type: str
    required: yes
  state:
    description:
      - Defines whether the IP will be routed or not.
      - If set to C(routed), I(value) must be specified.
    type: str
    choices:
      - routed
      - unrouted
    default: routed
  value:
    description:
      - The new value for the failover IP address.
      - Required when setting I(state) to C(routed).
    type: str
  timeout:
    description:
      - Timeout to use when routing or unrouting the failover IP.
      - Note that the API call returns when the failover IP has been
        successfully routed to the new address, respectively successfully
        unrouted.
    type: int
    default: 180
'''

EXAMPLES = r'''
- name: Set value of failover IP 1.2.3.4 to 5.6.7.8
  hetzner_failover_ip:
    hetzner_user: foo
    hetzner_password: bar
    failover_ip: 1.2.3.4
    value: 5.6.7.8

- name: Set value of failover IP 1.2.3.4 to unrouted
  hetzner_failover_ip:
    hetzner_user: foo
    hetzner_password: bar
    failover_ip: 1.2.3.4
    state: unrouted
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
    HETZNER_DEFAULT_ARGUMENT_SPEC,
    get_failover,
    set_failover,
    get_failover_state,
)


def main():
    argument_spec = dict(
        failover_ip=dict(type='str', required=True),
        state=dict(type='str', default='routed', choices=['routed', 'unrouted']),
        value=dict(type='str'),
        timeout=dict(type='int', default=180),
    )
    argument_spec.update(HETZNER_DEFAULT_ARGUMENT_SPEC)
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=(
            ('state', 'routed', ['value']),
        ),
    )

    failover_ip = module.params['failover_ip']
    value = get_failover(module, failover_ip)
    changed = False
    before = get_failover_state(value)

    if module.params['state'] == 'routed':
        new_value = module.params['value']
    else:
        new_value = None

    if value != new_value:
        if module.check_mode:
            value = new_value
            changed = True
        else:
            value, changed = set_failover(module, failover_ip, new_value, timeout=module.params['timeout'])

    after = get_failover_state(value)
    module.exit_json(
        changed=changed,
        diff=dict(
            before=before,
            after=after,
        ),
        **after
    )


if __name__ == '__main__':
    main()
