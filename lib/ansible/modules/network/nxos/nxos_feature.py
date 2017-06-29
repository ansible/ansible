#!/usr/bin/python
#
# This file is part of Ansible
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
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nxos_feature
extends_documentation_fragment: nxos
version_added: "2.1"
short_description: Manage features in NX-OS switches.
description:
    - Offers ability to enable and disable features in NX-OS.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
options:
    feature:
        description:
            - Name of feature.
        required: true
    state:
        description:
            - Desired state of the feature.
        required: false
        default: 'enabled'
        choices: ['enabled','disabled']
'''

EXAMPLES = '''
- name: Ensure lacp is enabled
  nxos_feature:
    feature: lacp
    state: enabled
    host: "{{ inventory_hostname }}"

- name: Ensure ospf is disabled
  nxos_feature:
    feature: ospf
    state: disabled
    host: "{{ inventory_hostname }}"

- name: Ensure vpc is enabled
  nxos_feature:
    feature: vpc
    state: enabled
    host: "{{ inventory_hostname }}"

'''

RETURN = '''
commands:
    description: The set of commands to be sent to the remote device
    returned: always
    type: list
    sample: ['nv overlay evpn']
'''
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nxos import load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec
from ansible.module_utils.nxos import check_args as nxos_check_args

def check_args(module, warnings):
    nxos_check_args(module, warnings)

    for key in ('include_defaults', 'config', 'save'):
        if module.params[key] is not None:
            warnings.append('argument %s is no longer supported, ignoring value' % key)


def get_available_features(feature, module):
    available_features = {}
    feature_regex = '(?P<feature>\S+)\s+\d+\s+(?P<state>.*)'
    command = 'show feature'

    command = {'command': command, 'output': 'text'}

    try:
        body = run_commands(module, [command])[0]
        split_body = body.splitlines()
    except (KeyError, AttributeError, IndexError):
        return {}

    for line in split_body:
        try:
            match_feature = re.match(feature_regex, line, re.DOTALL)
            feature_group = match_feature.groupdict()
            feature = feature_group['feature']
            state = feature_group['state']
        except AttributeError:
            feature = ''
            state = ''

        if feature and state:
            if 'enabled' in state:
                state = 'enabled'

            if feature not in available_features:
                available_features[feature] = state
            else:
                if (available_features[feature] == 'disabled' and
                    state == 'enabled'):
                    available_features[feature] = state

    return available_features



def get_commands(proposed, existing, state, module):
    feature = validate_feature(module, mode='config')
    commands = []
    feature_check = proposed == existing
    if not feature_check:
        if state == 'enabled':
            command = 'feature {0}'.format(feature)
            commands.append(command)
        elif state == 'disabled':
            command = "no feature {0}".format(feature)
            commands.append(command)
    return commands


def validate_feature(module, mode='show'):
    '''Some features may need to be mapped due to inconsistency
    between how they appear from "show feature" output and
    how they are configured'''

    feature = module.params['feature']

    feature_to_be_mapped = {
        'show': {
            'nv overlay': 'nve',
            'vn-segment-vlan-based': 'vnseg_vlan',
            'hsrp': 'hsrp_engine',
            'fabric multicast': 'fabric_mcast',
            'scp-server': 'scpServer',
            'sftp-server': 'sftpServer',
            'sla responder': 'sla_responder',
            'sla sender': 'sla_sender',
            'ssh': 'sshServer',
            'tacacs+': 'tacacs',
            'telnet': 'telnetServer',
            'ethernet-link-oam': 'elo',
            'port-security': 'eth_port_sec'
            },
        'config': {
            'nve': 'nv overlay',
            'vnseg_vlan': 'vn-segment-vlan-based',
            'hsrp_engine': 'hsrp',
            'fabric_mcast': 'fabric multicast',
            'scpServer': 'scp-server',
            'sftpServer': 'sftp-server',
            'sla_sender': 'sla sender',
            'sla_responder': 'sla responder',
            'sshServer': 'ssh',
            'tacacs': 'tacacs+',
            'telnetServer': 'telnet',
            'elo': 'ethernet-link-oam',
            'eth_port_sec': 'port-security'
            }
        }

    if feature in feature_to_be_mapped[mode]:
        feature = feature_to_be_mapped[mode][feature]

    return feature


def main():
    argument_spec = dict(
        feature=dict(type='str', required=True),
        state=dict(choices=['enabled', 'disabled'], default='enabled'),

        # deprecated in Ans2.3
        include_defaults=dict(),
        config=dict(),
        save=dict()
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    feature = validate_feature(module)
    state = module.params['state'].lower()

    available_features = get_available_features(feature, module)
    if feature not in available_features:
        module.fail_json(
            msg='Invalid feature name.',
            features_currently_supported=available_features,
            invalid_feature=feature)
    else:
        existstate = available_features[feature]

        existing = dict(state=existstate)
        proposed = dict(state=state)
        changed = False
        end_state = existing

        cmds = get_commands(proposed, existing, state, module)

        if cmds:
            if not module.check_mode:
                load_config(module, cmds)
            changed = True

    results = {
        'commands': cmds,
        'changed': changed,
        'warnings': warnings
    }

    module.exit_json(**results)


if __name__ == '__main__':
    main()

