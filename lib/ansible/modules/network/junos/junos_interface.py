#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: junos_interface
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage Interface on Juniper JUNOS network devices
description:
  - This module provides declarative management of Interfaces
    on Juniper JUNOS network devices.
options:
  name:
    description:
      - Name of the Interface.
    required: true
  description:
    description:
      - Description of Interface.
  enabled:
    description:
      - Interface link status.
  speed:
    description:
      - Interface link speed.
  mtu:
    description:
      - Maximum size of transmit packet.
  duplex:
    description:
      - Interface link status.
    default: auto
    choices: ['full', 'half', 'auto']
  tx_rate:
    description:
      - Transmit rate in bits per second (bps).
  rx_rate:
    description:
      - Receiver rate in bits per second (bps).
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device. This wait is applicable for operational state argument which are
        I(enabled), I(tx_rate) and I(rx_rate).
  aggregate:
    description: List of Interfaces definitions.
  state:
    description:
      - State of the Interface configuration, C(up) means present and
        operationally up and C(down) means present and operationally C(down)
    default: present
    choices: ['present', 'absent', 'up', 'down']
  active:
    description:
      - Specifies whether or not the configuration is active or deactivated
    default: True
    choices: [True, False]
requirements:
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed
"""

EXAMPLES = """
- name: configure interface
  junos_interface:
    name: ge-0/0/1
    description: test-interface

- name: remove interface
  junos_interface:
    name: ge-0/0/1
    state: absent

- name: make interface down
  junos_interface:
    name: ge-0/0/1
    state: down

- name: make interface up
  junos_interface:
    name: ge-0/0/1
    state: up

- name: Deactivate interface config
  junos_interface:
    name: ge-0/0/1
    state: present
    active: False

- name: Activate interface config
  net_interface:
    name: ge-0/0/1
    state: present
    active: True

- name: Configure interface speed, mtu, duplex
  junos_interface:
    name: ge-0/0/1
    state: present
    speed: 1g
    mtu: 256
    duplex: full

- name: Create interface using aggregate
  junos_interface:
    aggregate:
      - { name: ge-0/0/1, description: test-interface-1,  speed: 1g, duplex: half, mtu: 512}
      - { name: ge-0/0/2, description: test-interface-2,  speed: 10m, duplex: full, mtu: 256}

- name: Delete interface using aggregate
  junos_interface:
    aggregate:
      - { name: ge-0/0/1, description: test-interface-1, state: absent}
      - { name: ge-0/0/2, description: test-interface-2, state: absent}
"""

RETURN = """
diff.prepared:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: string
  sample: >
        [edit interfaces]
        +   ge-0/0/1 {
        +       description test-interface;
        +   }
"""
import collections

from time import sleep

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netconf import send_request
from ansible.module_utils.network_common import conditional
from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.junos import load_config, map_params_to_obj, map_obj_to_ele
from ansible.module_utils.junos import commit_configuration, discard_changes, locked_config, to_param_list

try:
    from lxml.etree import Element, SubElement, tostring
except ImportError:
    from xml.etree.ElementTree import Element, SubElement, tostring

USE_PERSISTENT_CONNECTION = True


def validate_mtu(value, module):
    if value and not 256 <= value <= 9192:
        module.fail_json(msg='mtu must be between 256 and 9192')


def validate_param_values(module, obj, param=None):
    if not param:
        param = module.params
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(param.get(key), module)


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        description=dict(),
        enabled=dict(),
        speed=dict(),
        mtu=dict(type='int'),
        duplex=dict(choices=['full', 'half', 'auto']),
        tx_rate=dict(),
        rx_rate=dict(),
        delay=dict(default=10, type='int'),
        state=dict(default='present',
                   choices=['present', 'absent', 'up', 'down']),
        active=dict(default=True, type='bool')
    )

    aggregate_spec = element_spec.copy()
    aggregate_spec['name'] = dict(required=True)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(junos_argument_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate'],
                          ['state', 'aggregate'],
                          ['active', 'aggregate']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    top = 'interfaces/interface'

    param_to_xpath_map = collections.OrderedDict()
    param_to_xpath_map.update([
        ('name', {'xpath': 'name', 'is_key': True}),
        ('description', 'description'),
        ('speed', 'speed'),
        ('mtu', 'mtu'),
        ('duplex', 'link-mode'),
        ('disable', {'xpath': 'disable', 'tag_only': True})
    ])

    choice_to_value_map = {
        'link-mode': {'full': 'full-duplex', 'half': 'half-duplex', 'auto': 'automatic'}
    }

    params = to_param_list(module)

    requests = list()
    for param in params:
        item = param.copy()
        state = item.get('state')
        item['disable'] = True if state == 'down' else False

        if state in ('present', 'up', 'down'):
            item['state'] = 'present'
        else:
            item['disable'] = True

        validate_param_values(module, param_to_xpath_map, param=item)
        want = map_params_to_obj(module, param_to_xpath_map, param=item)
        requests.append(map_obj_to_ele(module, want, top, value_map=choice_to_value_map, param=item))

    diff = None
    with locked_config(module):
        for req in requests:
            diff = load_config(module, tostring(req), warnings, action='merge')

        # issue commit after last configuration change is done
        commit = not module.check_mode
        if diff:
            if commit:
                commit_configuration(module)
            else:
                discard_changes(module)
            result['changed'] = True

            if module._diff:
                result['diff'] = {'prepared': diff}

    failed_conditions = []
    for item in params:
        enabled = item.get('enabled')
        tx_rate = item.get('tx_rate')
        rx_rate = item.get('rx_rate')

        if enabled is None and tx_rate is None and rx_rate is None:
            continue

        element = Element('get-interface-information')
        intf_name = SubElement(element, 'interface-name')
        intf_name.text = item.get('name')

        if result['changed']:
            sleep(item.get('delay'))

        reply = send_request(module, element, ignore_warning=False)

        if enabled:
            admin_status = reply.xpath('interface-information/physical-interface/admin-status')
            if not admin_status or not conditional(enabled, admin_status[0].text.strip()):
                failed_conditions.append('enabled ' + enabled)

        if tx_rate:
            output_bps = reply.xpath('interface-information/physical-interface/traffic-statistics/output-bps')
            if not output_bps or not conditional(tx_rate, output_bps[0].text.strip(), cast=int):
                failed_conditions.append('tx_rate ' + tx_rate)

        if rx_rate:
            input_bps = reply.xpath('interface-information/physical-interface/traffic-statistics/input-bps')
            if not input_bps or not conditional(rx_rate, input_bps[0].text.strip(), cast=int):
                failed_conditions.append('rx_rate ' + rx_rate)

    if failed_conditions:
        msg = 'One or more conditional statements have not be satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    module.exit_json(**result)

if __name__ == "__main__":
    main()
