#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: panos_security_rule
short_description: Create security rule policy on PAN-OS devices or Panorama management console.
description:
    - Security policies allow you to enforce rules and take action, and can be as general or specific as needed.
      The policy rules are compared against the incoming traffic in sequence, and because the first rule that matches the traffic is applied,
      the more specific rules must precede the more general ones.
author: "Ivan Bojer (@ivanbojer), Robert Hagen (@rnh556)"
version_added: "2.4"
requirements:
    - pan-python can be obtained from PyPi U(https://pypi.python.org/pypi/pan-python)
    - pandevice can be obtained from PyPi U(https://pypi.python.org/pypi/pandevice)
    - xmltodict can be obtained from PyPi U(https://pypi.python.org/pypi/xmltodict)
notes:
    - Checkmode is not supported.
    - Panorama is supported.
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
    operation:
        description:
            - The action to be taken.  Supported values are I(add)/I(update)/I(find)/I(delete).
        default: 'add'
    rule_name:
        description:
            - Name of the security rule.
        required: true
    rule_type:
        description:
            - Type of security rule (version 6.1 of PanOS and above).
        default: "universal"
    description:
        description:
            - Description for the security rule.
        default: "None"
    tag_name:
        description:
            - Administrative tags that can be added to the rule. Note, tags must be already defined.
        default: "None"
    source_zone:
        description:
            - List of source zones.
        default: "any"
    destination_zone:
        description:
            - List of destination zones.
        default: "any"
    source_ip:
        description:
            - List of source addresses.
        default: "any"
    source_user:
        description:
            - Use users to enforce policy for individual users or a group of users.
        default: "any"
    hip_profiles:
        description: >
            - If you are using GlobalProtect with host information profile (HIP) enabled, you can also base the policy
            on information collected by GlobalProtect. For example, the user access level can be determined HIP that
            notifies the firewall about the user's local configuration.
        default: "any"
    destination_ip:
        description:
            - List of destination addresses.
        default: "any"
    application:
        description:
            - List of applications.
        default: "any"
    service:
        description:
            - List of services.
        default: "application-default"
    log_start:
        description:
            - Whether to log at session start.
        default: false
    log_end:
        description:
            - Whether to log at session end.
        default: true
    action:
        description:
            - Action to apply once rules maches.
        default: "allow"
    group_profile:
        description: >
            - Security profile group that is already defined in the system. This property supersedes antivirus,
            vulnerability, spyware, url_filtering, file_blocking, data_filtering, and wildfire_analysis properties.
        default: None
    antivirus:
        description:
            - Name of the already defined antivirus profile.
        default: None
    vulnerability:
        description:
            - Name of the already defined vulnerability profile.
        default: None
    spyware:
        description:
            - Name of the already defined spyware profile.
        default: None
    url_filtering:
        description:
            - Name of the already defined url_filtering profile.
        default: None
    file_blocking:
        description:
            - Name of the already defined file_blocking profile.
        default: None
    data_filtering:
        description:
            - Name of the already defined data_filtering profile.
        default: None
    wildfire_analysis:
        description:
            - Name of the already defined wildfire_analysis profile.
        default: None
    devicegroup:
        description: >
            - Device groups are used for the Panorama interaction with Firewall(s). The group must exists on Panorama.
            If device group is not define we assume that we are contacting Firewall.
        default: None
    commit:
        description:
            - Commit configuration if changed.
        default: true
'''

EXAMPLES = '''
- name: add an SSH inbound rule to devicegroup
  panos_security_rule:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    operation: 'add'
    rule_name: 'SSH permit'
    description: 'SSH rule test'
    tag_name: ['ProjectX']
    source_zone: ['public']
    destination_zone: ['private']
    source: ['any']
    source_user: ['any']
    destination: ['1.1.1.1']
    category: ['any']
    application: ['ssh']
    service: ['application-default']
    hip_profiles: ['any']
    action: 'allow'
    devicegroup: 'Cloud Edge'

- name: add a rule to allow HTTP multimedia only from CDNs
  panos_security_rule:
    ip_address: '10.5.172.91'
    username: 'admin'
    password: 'paloalto'
    operation: 'add'
    rule_name: 'HTTP Multimedia'
    description: 'Allow HTTP multimedia only to host at 1.1.1.1'
    source_zone: ['public']
    destination_zone: ['private']
    source: ['any']
    source_user: ['any']
    destination: ['1.1.1.1']
    category: ['content-delivery-networks']
    application: ['http-video', 'http-audio']
    service: ['service-http', 'service-https']
    hip_profiles: ['any']
    action: 'allow'

- name: add a more complex rule that uses security profiles
  panos_security_rule:
    ip_address: '{{ ip_address }}'
    username: '{{ username }}'
    password: '{{ password }}'
    operation: 'add'
    rule_name: 'Allow HTTP w profile'
    log_start: false
    log_end: true
    action: 'allow'
    antivirus: 'default'
    vulnerability: 'default'
    spyware: 'default'
    url_filtering: 'default'
    wildfire_analysis: 'default'

- name: delete a devicegroup security rule
  panos_security_rule:
    ip_address: '{{ ip_address }}'
    api_key: '{{ api_key }}'
    operation: 'delete'
    rule_name: 'Allow telnet'
    devicegroup: 'DC Firewalls'

- name: find a specific security rule
  panos_security_rule:
    ip_address: '{{ ip_address }}'
    password: '{{ password }}'
    operation: 'find'
    rule_name: 'Allow RDP to DCs'
  register: result
- debug: msg='{{result.stdout_lines}}'

'''

RETURN = '''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_exception

try:
    import pan.xapi
    from pan.xapi import PanXapiError
    import pandevice
    from pandevice import base
    from pandevice import firewall
    from pandevice import panorama
    from pandevice import objects
    from pandevice import policies
    import xmltodict
    import json

    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def get_devicegroup(device, devicegroup):
    dg_list = device.refresh_devices()
    for group in dg_list:
        if isinstance(group, pandevice.panorama.DeviceGroup):
            if group.name == devicegroup:
                return group
    return False


def get_rulebase(device, devicegroup):
    # Build the rulebase
    if isinstance(device, pandevice.firewall.Firewall):
        rulebase = pandevice.policies.Rulebase()
        device.add(rulebase)
    elif isinstance(device, pandevice.panorama.Panorama):
        dg = panorama.DeviceGroup(devicegroup)
        device.add(dg)
        rulebase = policies.PreRulebase()
        dg.add(rulebase)
    else:
        return False
    policies.SecurityRule.refreshall(rulebase)
    return rulebase


def find_rule(rulebase, rule_name):
    # Search for the rule name
    rule = rulebase.find(rule_name)
    if rule:
        return rule
    else:
        return False


def rule_is_match(propose_rule, current_rule):

    match_check = ['name', 'description', 'group_profile', 'antivirus', 'vulnerability',
                   'spyware', 'url_filtering', 'file_blocking', 'data_filtering',
                   'wildfire_analysis', 'type', 'action', 'tag', 'log_start', 'log_end']
    list_check = ['tozone', 'fromzone', 'source', 'source_user', 'destination', 'category',
                  'application', 'service', 'hip_profiles']

    for check in match_check:
        propose_check = getattr(propose_rule, check, None)
        current_check = getattr(current_rule, check, None)
        if propose_check != current_check:
            return False
    for check in list_check:
        propose_check = getattr(propose_rule, check, [])
        current_check = getattr(current_rule, check, [])
        if set(propose_check) != set(current_check):
            return False
    return True


def create_security_rule(**kwargs):
    security_rule = policies.SecurityRule(
        name=kwargs['rule_name'],
        description=kwargs['description'],
        fromzone=kwargs['source_zone'],
        source=kwargs['source_ip'],
        source_user=kwargs['source_user'],
        hip_profiles=kwargs['hip_profiles'],
        tozone=kwargs['destination_zone'],
        destination=kwargs['destination_ip'],
        application=kwargs['application'],
        service=kwargs['service'],
        category=kwargs['category'],
        log_start=kwargs['log_start'],
        log_end=kwargs['log_end'],
        action=kwargs['action'],
        type=kwargs['rule_type']
    )

    if 'tag_name' in kwargs:
        security_rule.tag = kwargs['tag_name']

    # profile settings
    if 'group_profile' in kwargs:
        security_rule.group = kwargs['group_profile']
    else:
        if 'antivirus' in kwargs:
            security_rule.virus = kwargs['antivirus']
        if 'vulnerability' in kwargs:
            security_rule.vulnerability = kwargs['vulnerability']
        if 'spyware' in kwargs:
            security_rule.spyware = kwargs['spyware']
        if 'url_filtering' in kwargs:
            security_rule.url_filtering = kwargs['url_filtering']
        if 'file_blocking' in kwargs:
            security_rule.file_blocking = kwargs['file_blocking']
        if 'data_filtering' in kwargs:
            security_rule.data_filtering = kwargs['data_filtering']
        if 'wildfire_analysis' in kwargs:
            security_rule.wildfire_analysis = kwargs['wildfire_analysis']
    return security_rule


def add_rule(rulebase, sec_rule):
    if rulebase:
        rulebase.add(sec_rule)
        sec_rule.create()
        return True
    else:
        return False


def update_rule(rulebase, nat_rule):
    if rulebase:
        rulebase.add(nat_rule)
        nat_rule.apply()
        return True
    else:
        return False


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(no_log=True),
        username=dict(default='admin'),
        api_key=dict(no_log=True),
        operation=dict(default='add', choices=['add', 'update', 'delete', 'find']),
        rule_name=dict(required=True),
        description=dict(default=''),
        tag_name=dict(type='list'),
        destination_zone=dict(type='list', default=['any']),
        source_zone=dict(type='list', default=['any']),
        source_ip=dict(type='list', default=["any"]),
        source_user=dict(type='list', default=['any']),
        destination_ip=dict(type='list', default=["any"]),
        category=dict(type='list', default=['any']),
        application=dict(type='list', default=['any']),
        service=dict(type='list', default=['application-default']),
        hip_profiles=dict(type='list', default=['any']),
        group_profile=dict(),
        antivirus=dict(),
        vulnerability=dict(),
        spyware=dict(),
        url_filtering=dict(),
        file_blocking=dict(),
        data_filtering=dict(),
        wildfire_analysis=dict(),
        log_start=dict(type='bool', default=False),
        log_end=dict(type='bool', default=True),
        rule_type=dict(default='universal'),
        action=dict(default='allow'),
        devicegroup=dict(),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,
                           required_one_of=[['api_key', 'password']])
    if not HAS_LIB:
        module.fail_json(msg='Missing required libraries.')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']
    api_key = module.params['api_key']
    operation = module.params['operation']
    rule_name = module.params['rule_name']
    description = module.params['description']
    tag_name = module.params['tag_name']
    source_zone = module.params['source_zone']
    source_ip = module.params['source_ip']
    source_user = module.params['source_user']
    hip_profiles = module.params['hip_profiles']
    destination_zone = module.params['destination_zone']
    destination_ip = module.params['destination_ip']
    application = module.params['application']
    service = module.params['service']
    category = module.params['category']
    log_start = module.params['log_start']
    log_end = module.params['log_end']
    action = module.params['action']
    group_profile = module.params['group_profile']
    antivirus = module.params['antivirus']
    vulnerability = module.params['vulnerability']
    spyware = module.params['spyware']
    url_filtering = module.params['url_filtering']
    file_blocking = module.params['file_blocking']
    data_filtering = module.params['data_filtering']
    wildfire_analysis = module.params['wildfire_analysis']
    rule_type = module.params['rule_type']
    devicegroup = module.params['devicegroup']

    commit = module.params['commit']

    # Create the device with the appropriate pandevice type
    device = base.PanDevice.create_from_device(ip_address, username, password, api_key=api_key)

    # If Panorama, validate the devicegroup
    dev_group = None
    if devicegroup and isinstance(device, panorama.Panorama):
        dev_group = get_devicegroup(device, devicegroup)
        if dev_group:
            device.add(dev_group)
        else:
            module.fail_json(msg='\'%s\' device group not found in Panorama. Is the name correct?' % devicegroup)

    # Get the rulebase
    rulebase = get_rulebase(device, dev_group)

    # Which action shall we take on the object?
    if operation == "find":
        # Search for the object
        match = find_rule(rulebase, rule_name)
        # If found, format and return the result
        if match:
            match_dict = xmltodict.parse(match.element_str())
            module.exit_json(
                stdout_lines=json.dumps(match_dict, indent=2),
                msg='Rule matched'
            )
        else:
            module.fail_json(msg='Rule \'%s\' not found. Is the name correct?' % rule_name)
    elif operation == "delete":
        # Search for the object
        match = find_rule(rulebase, rule_name)
        # If found, delete it
        if match:
            try:
                if commit:
                    match.delete()
            except PanXapiError:
                exc = get_exception()
                module.fail_json(msg=exc.message)

            module.exit_json(changed=True, msg='Rule \'%s\' successfully deleted' % rule_name)
        else:
            module.fail_json(msg='Rule \'%s\' not found. Is the name correct?' % rule_name)
    elif operation == "add":
        new_rule = create_security_rule(
            rule_name=rule_name,
            description=description,
            tag_name=tag_name,
            source_zone=source_zone,
            destination_zone=destination_zone,
            source_ip=source_ip,
            source_user=source_user,
            destination_ip=destination_ip,
            category=category,
            application=application,
            service=service,
            hip_profiles=hip_profiles,
            group_profile=group_profile,
            antivirus=antivirus,
            vulnerability=vulnerability,
            spyware=spyware,
            url_filtering=url_filtering,
            file_blocking=file_blocking,
            data_filtering=data_filtering,
            wildfire_analysis=wildfire_analysis,
            log_start=log_start,
            log_end=log_end,
            rule_type=rule_type,
            action=action
        )
        # Search for the rule. Fail if found.
        match = find_rule(rulebase, rule_name)
        if match:
            if rule_is_match(match, new_rule):
                module.exit_json(changed=False, msg='Rule \'%s\' is already in place' % rule_name)
            else:
                module.fail_json(msg='Rule \'%s\' already exists. Use operation: \'update\' to change it.' % rule_name)
        else:
            try:
                changed = add_rule(rulebase, new_rule)
                if changed and commit:
                    device.commit(sync=True)
            except PanXapiError:
                exc = get_exception()
                module.fail_json(msg=exc.message)
            module.exit_json(changed=changed, msg='Rule \'%s\' successfully added' % rule_name)
    elif operation == 'update':
        # Search for the rule. Update if found.
        match = find_rule(rulebase, rule_name)
        if match:
            try:
                new_rule = create_security_rule(
                    rule_name=rule_name,
                    description=description,
                    tag_name=tag_name,
                    source_zone=source_zone,
                    destination_zone=destination_zone,
                    source_ip=source_ip,
                    source_user=source_user,
                    destination_ip=destination_ip,
                    category=category,
                    application=application,
                    service=service,
                    hip_profiles=hip_profiles,
                    group_profile=group_profile,
                    antivirus=antivirus,
                    vulnerability=vulnerability,
                    spyware=spyware,
                    url_filtering=url_filtering,
                    file_blocking=file_blocking,
                    data_filtering=data_filtering,
                    wildfire_analysis=wildfire_analysis,
                    log_start=log_start,
                    log_end=log_end,
                    rule_type=rule_type,
                    action=action
                )
                changed = update_rule(rulebase, new_rule)
                if changed and commit:
                    device.commit(sync=True)
            except PanXapiError:
                exc = get_exception()
                module.fail_json(msg=exc.message)
            module.exit_json(changed=changed, msg='Rule \'%s\' successfully updated' % rule_name)
        else:
            module.fail_json(msg='Rule \'%s\' does not exist. Use operation: \'add\' to add it.' % rule_name)


if __name__ == '__main__':
    main()
