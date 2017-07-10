#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

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
      - Transmit rate.
  rx_rate:
    description:
      - Receiver rate.
  collection:
    description: List of Interfaces definitions.
  purge:
    description:
      - Purge Interfaces not defined in the collections parameter.
        This applies only for logical interface.
    default: no
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.junos import load_config, map_params_to_obj, map_obj_to_ele
from ansible.module_utils.junos import commit_configuration, discard_changes, locked_config

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring

USE_PERSISTENT_CONNECTION = True


def validate_mtu(value, module):
    if value and not 256 <= value <= 9192:
        module.fail_json(msg='mtu must be between 256 and 9192')


def validate_param_values(module, obj):
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(module.params.get(key), module)


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        enabled=dict(),
        speed=dict(),
        mtu=dict(type='int'),
        duplex=dict(choices=['full', 'half', 'auto']),
        tx_rate=dict(),
        rx_rate=dict(),
        collection=dict(),
        purge=dict(default=False, type='bool'),
        state=dict(default='present',
                   choices=['present', 'absent', 'up', 'down']),
        active=dict(default=True, type='bool')
    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
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

    state = module.params.get('state')
    module.params['disable'] = True if state == 'down' else False

    if state in ('present', 'up', 'down'):
        module.params['state'] = 'present'

    else:
        module.params['disable'] = True

    choice_to_value_map = {
        'link-mode': {'full': 'full-duplex', 'half': 'half-duplex', 'auto': 'automatic'}
    }

    validate_param_values(module, param_to_xpath_map)

    want = map_params_to_obj(module, param_to_xpath_map)
    ele = map_obj_to_ele(module, want, top, choice_to_value_map)

    with locked_config(module):
        diff = load_config(module, tostring(ele), warnings, action='replace')

        commit = not module.check_mode
        if diff:
            if commit:
                commit_configuration(module)
            else:
                discard_changes(module)
            result['changed'] = True

            if module._diff:
                result['diff'] = {'prepared': diff}

    module.exit_json(**result)

if __name__ == "__main__":
    main()
