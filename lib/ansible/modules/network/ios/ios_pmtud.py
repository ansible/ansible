#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ios_pmtud
short_description: Perform path MTU discovery on Cisco IOS devices.
description:
    - Perform path MTU discovery on Cisco IOS devices.
author:
    - Martin Komon (@mkomon)
version_added: '2.5'
extends_documentation_fragment: ios
options:
    dest:
        description:
            - IP to ping, should respond to 1500 B packets from Internet
        required: true
    vrf:
        description:
            - VRF name
        required: false
    source:
        description:
            - Source interface name or IP address
        required: false
    max_size:
        description:
            - Start and max size for path MTU discovery.
        default: 1500
        required: false
    max_range:
        description:
            - Max range of path MTU discovery. Must be 2^n.
        default: 512
        required: false

'''

EXAMPLES = '''
---
- cli:
    host: "{{ inventory_hostname }}"
    username: cisco
    password: cisco

# Run path MTU discovery
- name: MTU check
  ios_pmtud:
    ip: 169.254.169.254
    provider: "{{ cli }}"


# Run path MTU discovery with source interface and VRF
- name: Test with a message and changed output
  ios_pmtud:
    ip: 169.254.169.254
    src_if: Lo0
    vrf: MGMT
    provider: "{{ cli }}"

# Run a quicker path MTU discovery in smaller range
- name: Test failure of the module
  ios_pmtud:
    ip: 8.8.8.8
    vrf: internet
    max_range: 64
    provider: "{{ cli }}"

# fail the module
- name: Test failure of the module
  ios_pmtud:
    ip: 333.333.333.333
    provider: "{{ cli }}"

'''

RETURN = '''
mtu:
  description: Path MTU size in bytes
  returned: always
  type: int
dest:
  description: Destination IP tested
  returned: always
  type: int
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ios import run_commands
from ansible.module_utils.ios import ios_argument_spec, check_args


def run_module():
    module_args = dict(
        dest=dict(type='str', required=True),
        vrf=dict(type='str', required=False, default=None),
        source=dict(type='str', required=False, default=None),
        max_size=dict(type='int', required=False, default=1500),
        max_range=dict(type='int', required=False, default=512),
    )
    module_args.update(ios_argument_spec)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    results = dict(
        changed=False,
        mtu=0,
        dest=module.params['dest']
    )

    dest = module.params['dest']
    source = module.params['source']
    vrf = module.params['vrf']
    max_size = module.params['max_size']
    max_range = module.params['max_range']

    warnings = list()
    check_args(module, warnings)

    if module.check_mode:
        return results

    test_size = max_size
    step = max_range

    def ping_str(dest, vrf, source, test_size):
        return 'ping {0}{1} df-bit {2}repeat 3 size {3}'.format(
            'vrf {0} '.format(vrf) if vrf else '',
            dest,
            'source {0} '.format(source) if source else '',
            test_size)

    # Check if ICMP passes at all
    ping_results = run_commands(module, commands=ping_str(dest, vrf, source, 64))[0]
    if 'Success rate is 0 percent' in ping_results:
        module.fail_json(msg='Unknown error, PMTUD cannot run.', **results)

    while True:
        step = step / 2 if step >= 2 else 0
        ping_results = run_commands(module, commands=ping_str(dest, vrf, source, test_size))[0]
        if 'Success rate is 0 percent' not in ping_results and test_size == max_size:
            # ping success with max test size, save and break
            results['mtu'] = test_size
            break
        if 'Success rate is 0 percent' not in ping_results:
            # ping success, increase test size
            results['mtu'] = test_size
            test_size += step
        else:
            # ping fail, lower size
            test_size -= step
        if step < 1:
            break

    if not results['mtu']:
        module.fail_json(msg='MTU too low, increase max_range.', **results)

    module.exit_json(**results)


def main():
    run_module()


if __name__ == '__main__':
    main()
