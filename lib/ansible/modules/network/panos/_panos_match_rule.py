#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
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
#  limitations under the License.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: panos_match_rule
short_description: Test for match against a security rule on PAN-OS devices or Panorama management console.
description:
    - Security policies allow you to enforce rules and take action, and can be as general or specific as needed.
author: "Robert Hagen (@rnh556)"
version_added: "2.5"
requirements:
    - pan-python can be obtained from PyPI U(https://pypi.org/project/pan-python/)
    - pandevice can be obtained from PyPI U(https://pypi.org/project/pandevice/)
deprecated:
    alternative: Use U(https://galaxy.ansible.com/PaloAltoNetworks/paloaltonetworks) instead.
    removed_in: "2.12"
    why: Consolidating code base.
notes:
    - Checkmode is not supported.
    - Panorama NOT is supported.
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device being configured.
        required: true
    username:
        description:
            - Username credentials to use for auth unless I(api_key) is set.
        default: "admin"
    password:
        description:
            - Password credentials to use for auth unless I(api_key) is set.
        required: true
    api_key:
        description:
            - API key that can be used instead of I(username)/I(password) credentials.
    rule_type:
        description:
            - Type of rule. Valid types are I(security) or I(nat).
        required: true
        choices:
            - security
            - nat
    source_zone:
        description:
            - The source zone.
    source_ip:
        description:
            - The source IP address.
        required: true
    source_port:
        description:
            - The source port.
    source_user:
        description:
            - The source user or group.
    to_interface:
        description:
            - The inbound interface in a NAT rule.
    destination_zone:
        description:
            - The destination zone.
    destination_ip:
        description:
            - The destination IP address.
    destination_port:
        description:
            - The destination port.
    application:
        description:
            - The application.
    protocol:
        description:
            - The IP protocol number from 1 to 255.
    category:
        description:
            - URL category
    vsys_id:
        description:
            - ID of the VSYS object.
        default: "vsys1"
        required: true
'''

EXAMPLES = '''
- name: check security rules for Google DNS
  panos_match_rule:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    rule_type: 'security'
    source_ip: '10.0.0.0'
    destination_ip: '8.8.8.8'
    application: 'dns'
    destination_port: '53'
    protocol: '17'
  register: result
- debug: msg='{{result.stdout_lines}}'

- name: check security rules inbound SSH with user match
  panos_match_rule:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    rule_type: 'security'
    source_ip: '0.0.0.0'
    source_user: 'mydomain\\jsmith'
    destination_ip: '192.168.100.115'
    destination_port: '22'
    protocol: '6'
  register: result
- debug: msg='{{result.stdout_lines}}'

- name: check NAT rules for source NAT
  panos_match_rule:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    rule_type: 'nat'
    source_zone: 'Prod-DMZ'
    source_ip: '10.10.118.50'
    to_interface: 'ethernet1/2'
    destination_zone: 'Internet'
    destination_ip: '0.0.0.0'
    protocol: '6'
  register: result
- debug: msg='{{result.stdout_lines}}'

- name: check NAT rules for inbound web
  panos_match_rule:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    rule_type: 'nat'
    source_zone: 'Internet'
    source_ip: '0.0.0.0'
    to_interface: 'ethernet1/1'
    destination_zone: 'Prod DMZ'
    destination_ip: '192.168.118.50'
    destination_port: '80'
    protocol: '6'
  register: result
- debug: msg='{{result.stdout_lines}}'

- name: check security rules for outbound POP3 in vsys4
  panos_match_rule:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    vsys_id: 'vsys4'
    rule_type: 'security'
    source_ip: '10.0.0.0'
    destination_ip: '4.3.2.1'
    application: 'pop3'
    destination_port: '110'
    protocol: '6'
  register: result
- debug: msg='{{result.stdout_lines}}'

'''

RETURN = '''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from pan.xapi import PanXapiError
    from pan.xapi import PanXapiError
    from pandevice import base
    from pandevice import policies
    from pandevice import panorama
    import xmltodict
    import json

    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def create_security_test(**kwargs):
    security_test = 'test security-policy-match'

    # Add the source IP (required)
    if kwargs['source_ip']:
        security_test += ' source \"%s\"' % kwargs['source_ip']

    # Add the source user (optional)
    if kwargs['source_user']:
        security_test += ' source-user \"%s\"' % kwargs['source_user']

    # Add the destination IP (required)
    if kwargs['destination_ip']:
        security_test += ' destination \"%s\"' % kwargs['destination_ip']

    # Add the application (optional)
    if kwargs['application']:
        security_test += ' application \"%s\"' % kwargs['application']

    # Add the destination port (required)
    if kwargs['destination_port']:
        security_test += ' destination-port \"%s\"' % kwargs['destination_port']

    # Add the IP protocol number (required)
    if kwargs['protocol']:
        security_test += ' protocol \"%s\"' % kwargs['protocol']

    # Add the URL category (optional)
    if kwargs['category']:
        security_test += ' category \"%s\"' % kwargs['category']

    # Return the resulting string
    return security_test


def create_nat_test(**kwargs):
    nat_test = 'test nat-policy-match'

    # Add the source zone (optional)
    if kwargs['source_zone']:
        nat_test += ' from \"%s\"' % kwargs['source_zone']

    # Add the source IP (required)
    if kwargs['source_ip']:
        nat_test += ' source \"%s\"' % kwargs['source_ip']

    # Add the source user (optional)
    if kwargs['source_port']:
        nat_test += ' source-port \"%s\"' % kwargs['source_port']

    # Add inbound interface (optional)
    if kwargs['to_interface']:
        nat_test += ' to-interface \"%s\"' % kwargs['to_interface']

    # Add the destination zone (optional)
    if kwargs['destination_zone']:
        nat_test += ' to \"%s\"' % kwargs['destination_zone']

    # Add the destination IP (required)
    if kwargs['destination_ip']:
        nat_test += ' destination \"%s\"' % kwargs['destination_ip']

    # Add the destination port (optional)
    if kwargs['destination_port']:
        nat_test += ' destination-port \"%s\"' % kwargs['destination_port']

    # Add the IP protocol number (required)
    if kwargs['protocol']:
        nat_test += ' protocol \"%s\"' % kwargs['protocol']

    # Return the resulting string
    return nat_test


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(no_log=True),
        username=dict(default='admin'),
        api_key=dict(no_log=True),
        vsys_id=dict(default='vsys1'),
        rule_type=dict(required=True, choices=['security', 'nat']),
        source_zone=dict(default=None),
        source_ip=dict(default=None),
        source_user=dict(default=None),
        source_port=dict(default=None, type=int),
        to_interface=dict(default=None),
        destination_zone=dict(default=None),
        category=dict(default=None),
        application=dict(default=None),
        protocol=dict(default=None, type=int),
        destination_ip=dict(default=None),
        destination_port=dict(default=None, type=int)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,
                           required_one_of=[['api_key', 'password']])
    if not HAS_LIB:
        module.fail_json(msg='Missing required libraries.')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']
    api_key = module.params['api_key']
    vsys_id = module.params['vsys_id']
    rule_type = module.params['rule_type']
    source_zone = module.params['source_zone']
    source_ip = module.params['source_ip']
    source_user = module.params['source_user']
    source_port = module.params['source_port']
    to_interface = module.params['to_interface']
    destination_zone = module.params['destination_zone']
    destination_ip = module.params['destination_ip']
    destination_port = module.params['destination_port']
    category = module.params['category']
    application = module.params['application']
    protocol = module.params['protocol']

    # Create the device with the appropriate pandevice type
    device = base.PanDevice.create_from_device(ip_address, username, password, api_key=api_key)

    # Fail the module if this is a Panorama instance
    if isinstance(device, panorama.Panorama):
        module.fail_json(
            failed=1,
            msg='Panorama is not supported.'
        )

    # Create and attach security and NAT rulebases. Then populate them.
    sec_rule_base = nat_rule_base = policies.Rulebase()
    device.add(sec_rule_base)
    device.add(nat_rule_base)
    policies.SecurityRule.refreshall(sec_rule_base)
    policies.NatRule.refreshall(nat_rule_base)

    # Which action shall we take on the object?
    if rule_type == 'security':
        # Search for the object
        test_string = create_security_test(
            source_ip=source_ip,
            source_user=source_user,
            destination_ip=destination_ip,
            destination_port=destination_port,
            application=application,
            protocol=protocol,
            category=category
        )
    elif rule_type == 'nat':
        test_string = create_nat_test(
            source_zone=source_zone,
            source_ip=source_ip,
            source_port=source_port,
            to_interface=to_interface,
            destination_zone=destination_zone,
            destination_ip=destination_ip,
            destination_port=destination_port,
            protocol=protocol
        )

    # Submit the op command with the appropriate test string
    try:
        response = device.op(cmd=test_string, vsys=vsys_id)
    except PanXapiError as exc:
        module.fail_json(msg=exc.message)

    if response.find('result/rules').__len__() == 1:
        rule_name = response.find('result/rules/entry').text.split(';')[0]
    elif rule_type == 'nat':
        module.exit_json(msg='No matching NAT rule.')
    else:
        module.fail_json(msg='Rule match failed. Please check playbook syntax.')

    if rule_type == 'security':
        rule_match = sec_rule_base.find(rule_name, policies.SecurityRule)
    elif rule_type == 'nat':
        rule_match = nat_rule_base.find(rule_name, policies.NatRule)

    # Print out the rule
    module.exit_json(
        stdout_lines=json.dumps(xmltodict.parse(rule_match.element_str()), indent=2),
        msg='Rule matched'
    )


if __name__ == '__main__':
    main()
