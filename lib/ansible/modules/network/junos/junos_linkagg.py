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
module: junos_linkagg
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage link aggregation groups on Juniper JUNOS network devices
description:
  - This module provides declarative management of link aggregation groups
    on Juniper JUNOS network devices.
options:
  name:
    description:
      - Name of the link aggregation group.
    required: true
  mode:
    description:
      - Mode of the link aggregation group. A value of C(on) will enable LACP in C(passive) mode.
        C(active) configures the link to actively information about the state of the link,
        or it can be configured in C(passive) mode ie. send link state information only when
        received them from another link. A value of C(off) will disable LACP.
    default: off
    choices: ['on', 'off', 'active', 'passive']
  members:
    description:
      - List of members interfaces of the link aggregation group. The value can be
        single interface or list of interfaces.
    required: true
  min_links:
    description:
      - Minimum members that should be up
        before bringing up the link aggregation group.
  device_count:
    description:
      - Number of aggregated ethernet devices that can be configured.
        Acceptable integer value is between 1 and 128.
  description:
    description:
      - Description of Interface.
  state:
    description:
      - State of the link aggregation group.
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
- name: configure link aggregation
  junos_linkagg:
    name: ae11
    members:
      - ge-0/0/5
      - ge-0/0/6
      - ge-0/0/7
    lacp: active
    device_count: 4
    state: present

- name: delete link aggregation
  junos_linkagg:
    name: ae11
    members:
      - ge-0/0/5
      - ge-0/0/6
      - ge-0/0/7
    lacp: active
    device_count: 4
    state: delete

- name: deactivate link aggregation
  junos_linkagg:
    name: ae11
    members:
      - ge-0/0/5
      - ge-0/0/6
      - ge-0/0/7
    lacp: active
    device_count: 4
    state: present
    active: False

- name: Activate link aggregation
  junos_linkagg:
    name: ae11
    members:
      - ge-0/0/5
      - ge-0/0/6
      - ge-0/0/7
    lacp: active
    device_count: 4
    state: present
    active: True

- name: Disable link aggregation
  junos_linkagg:
    name: ae11
    state: down

- name: Enable link aggregation
  junos_linkagg:
    name: ae11
    state: up
"""

RETURN = """
diff:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: string
  sample: >
            [edit interfaces]
            +   ge-0/0/6 {
            +       ether-options {
            +           802.3ad ae0;
            +       }
            +   }
            [edit interfaces ge-0/0/7]
            +   ether-options {
            +       802.3ad ae0;
            +   }
            [edit interfaces]
            +   ae0 {
            +       description "configured by junos_linkagg";
            +       aggregated-ether-options {
            +           lacp {
            +               active;
            +           }
            +       }
            +   }
"""
import collections

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.junos import load_config, map_params_to_obj, map_obj_to_ele
from ansible.module_utils.junos import commit_configuration, discard_changes, locked_config, get_configuration

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring

USE_PERSISTENT_CONNECTION = True
DEFAULT_COMMENT = 'configured by junos_linkagg'


def validate_device_count(value, module):
    if value and not 1 <= value <= 128:
        module.fail_json(msg='device_count must be between 1 and 128')


def validate_min_links(value, module):
    if value and not 1 <= value <= 8:
        module.fail_json(msg='min_links must be between 1 and 8')


def validate_param_values(module, obj):
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(module.params.get(key), module)


def configure_lag_params(module, warnings):
    top = 'interfaces/interface'
    param_lag_to_xpath_map = collections.OrderedDict()
    param_lag_to_xpath_map.update([
        ('name', {'xpath': 'name', 'is_key': True}),
        ('description', 'description'),
        ('min_links', {'xpath': 'minimum-links', 'top': 'aggregated-ether-options'}),
        ('disable', {'xpath': 'disable', 'tag_only': True}),
        ('mode', {'xpath': module.params['mode'], 'tag_only': True, 'top': 'aggregated-ether-options/lacp'}),
    ])

    validate_param_values(module, param_lag_to_xpath_map)

    want = map_params_to_obj(module, param_lag_to_xpath_map)
    ele = map_obj_to_ele(module, want, top)

    diff = load_config(module, tostring(ele), warnings, action='replace')
    if module.params['device_count']:
        top = 'chassis/aggregated-devices/ethernet'
        device_count_to_xpath_map = {'device_count': {'xpath': 'device-count', 'leaf_only': True}}

        validate_param_values(module, device_count_to_xpath_map)

        want = map_params_to_obj(module, device_count_to_xpath_map)
        ele = map_obj_to_ele(module, want, top)

        diff = load_config(module, tostring(ele), warnings, action='replace')

    return diff


def configure_member_params(module, warnings, diff=None):
    top = 'interfaces/interface'
    members = module.params['members']

    if members:
        member_to_xpath_map = collections.OrderedDict()
        member_to_xpath_map.update([
            ('name', {'xpath': 'name', 'is_key': True, 'parent_attrib': False}),
            ('bundle', {'xpath': 'bundle', 'leaf_only': True, 'top': 'ether-options/ieee-802.3ad', 'is_key': True}),
        ])

        # link aggregation bundle assigned to member
        module.params['bundle'] = module.params['name']

        for member in members:

            if module.params['state'] == 'absent':
                # if link aggregate bundle is not assigned to member, trying to
                # delete it results in rpc-reply error, hence if is not assigned
                # skip deleting it and continue to next member.
                resp = get_configuration(module)
                bundle = resp.xpath("configuration/interfaces/interface[name='%s']/ether-options/"
                                    "ieee-802.3ad[bundle='%s']" % (member, module.params['bundle']))
                if not bundle:
                    continue
            # Name of member to be assigned to link aggregation bundle
            module.params['name'] = member

            validate_param_values(module, member_to_xpath_map)

            want = map_params_to_obj(module, member_to_xpath_map)
            ele = map_obj_to_ele(module, want, top)
            diff = load_config(module, tostring(ele), warnings)

    return diff


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        name=dict(required=True),
        mode=dict(default='on', type='str', choices=['on', 'off', 'active', 'passive']),
        members=dict(type='list'),
        min_links=dict(type='int'),
        device_count=dict(type='int'),
        description=dict(default=DEFAULT_COMMENT),
        state=dict(default='present', choices=['present', 'absent', 'up', 'down']),
        active=dict(default=True, type='bool')
    )

    argument_spec.update(junos_argument_spec)
    required_one_of = [['name', 'collection']]
    mutually_exclusive = [['name', 'collection']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    state = module.params.get('state')
    module.params['disable'] = True if state == 'down' else False

    if state in ('present', 'up', 'down'):
        module.params['state'] = 'present'

    else:
        module.params['disable'] = True

    if module.params.get('mode') == 'off':
        module.params['mode'] = ''
    elif module.params.get('mode') == 'on':
        module.params['mode'] = 'passive'

    with locked_config(module):
        diff = configure_lag_params(module, warnings)
        diff = configure_member_params(module, warnings, diff)

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
