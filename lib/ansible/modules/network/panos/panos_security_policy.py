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

DOCUMENTATION = '''
---
module: panos_security_policy
short_description: create security rule policy
description: >
    Security policies allow you to enforce rules and take action, and can be as general or specific as needed.
    The policy rules are compared against the incoming traffic in sequence, and because the first rule that matches
    the traffic is applied, the more specific rules must precede the more general ones.
author: "Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - pan-python
    - pandevice
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device
        required: true
    username:
        description:
            - username for authentication
        required: false
        default: "admin"
    password:
        description:
            - password for authentication
        required: true
    rule_name:
        description:
            - description of the security rule
        required: true
    rule_type:
        description:
            - type of security rule (6.1+)
        required: false
        default: "universal"
    description:
        description:
            - Description of this rule
        required: false
        default: "None"
    tag:
        description:
            - Administrative tags that can be added to the rule. Note, tags must be already defined.
        required: false
        default: "None"
    from_zone:
        description:
            - list of source zones
        required: false
        default: "any"
    to_zone:
        description:
            - list of destination zones
        required: false
        default: "any"
    source:
        description:
            - list of source addresses
        required: false
        default: "any"
    source_user:
        description:
            - use users to enforce policy for individual users or a group of users
        required: false
        default: "any"
    hip_profiles:
        description: >
            If you are using GlobalProtect with host information profile (HIP) enabled, you can also base the policy
            on information collected by GlobalProtect. For example, the user access level can be determined HIP that
            notifies the firewall about the user's local configuration.
        required: false
        default: "any"
    destination:
        description:
            - list of destination addresses
        required: false
        default: "any"
    application:
        description:
            - list of applications
        required: false
        default: "any"
    service:
        description:
            - list of services
        required: false
        default: "application-default"
    log_start:
        description:
            - whether to log at session start
        required: false
        default: false
    log_end:
        description:
            - whether to log at session end
        required: false
        default: true
    action:
        description:
            - action
        required: false
        default: "allow"
    group_profile:
        description: >
            security profile group that is already defined in the system. This property supersedes antivirus,
            vulnerability, spyware, url_filtering, file_blocking, data_filtering, and wildfire_analysis properties.
        required: false
        default: None
    antivirus:
        description:
            - name of the already defined profile
        required: false
        default: None
    vulnerability:
        description:
            - name of the already defined profile
        required: false
        default: None
    spyware:
        description:
            - name of the already defined profile
        required: false
        default: None
    url_filtering:
        description:
            - name of the already defined profile
        required: false
        default: None
    file_blocking:
        description:
            - name of the already defined profile
        required: false
        default: None
    data_filtering:
        description:
            - name of the already defined profile
        required: false
        default: None
    wildfire_analysis:
        description:
            - name of the already defined profile
        required: false
        default: None
    commit:
        description:
            - commit if changed
        required: false
        default: true
'''

EXAMPLES = '''
# permit ssh to 1.1.1.1
- panos_security_policy1:
    ip_address: '10.5.172.91'
    username: 'admin'
    password: 'paloalto'
    rule_name: 'SSH permit'
    description: 'SSH rule test'
    from_zone: ['public']
    to_zone: ['private']
    source: ['any']
    source_user: ['any']
    destination: ['1.1.1.1']
    category: ['any']
    application: ['ssh']
    service: ['application-default']
    hip_profiles: ['any']
    action: 'allow'
    commit: false

# Allow HTTP multimedia only from CDNs
- panos_security_policy1:
    ip_address: '10.5.172.91'
    username: 'admin'
    password: 'paloalto'
    rule_name: 'HTTP Multimedia'
    description: 'Allow HTTP multimedia only to host at 1.1.1.1'
    from_zone: ['public']
    to_zone: ['private']
    source: ['any']
    source_user: ['any']
    destination: ['1.1.1.1']
    category: ['content-delivery-networks']
    application: ['http-video', 'http-audio']
    service: ['service-http', 'service-https']
    hip_profiles: ['any']
    action: 'allow'
    commit: false

# more complex fictitious rule that uses profiles
- panos_security_policy1:
    ip_address: '10.5.172.91'
    username: 'admin'
    password: 'paloalto'
    rule_name: 'Allow HTTP w profile'
    log_start: false
    log_end: true
    action: 'allow'
    antivirus: 'default'
    vulnerability: 'default'
    spyware: 'default'
    url_filtering: 'default'
    wildfire_analysis: 'default'
    commit: false

# deny all
- panos_security_policy1:
    ip_address: '10.5.172.91'
    username: 'admin'
    password: 'paloalto'
    rule_name: 'DenyAll'
    log_start: true
    log_end: true
    action: 'deny'
    rule_type: 'interzone'
    commit: false
'''

RETURN = '''
# Default return values
'''

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_exception

try:
    import pan.xapi
    from pan.xapi import PanXapiError
    import pandevice
    import pandevice.firewall
    import pandevice.objects
    import pandevice.policies

    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def security_rule_exists(fw, rule_name):
    rule_base = pandevice.policies.Rulebase.refreshall(fw)
    if rule_base:
        rule_base = rule_base[0]
        security_rules = rule_base.findall(pandevice.policies.SecurityRule)

        for r in security_rules:
            if r.name == rule_name:
                return True

    return False


def create_security_rule(**kwargs):
    security_rule = pandevice.policies.SecurityRule(
        name=kwargs['rule_name'],
        description=kwargs['description'],
        tozone=kwargs['to_zone'],
        fromzone=kwargs['from_zone'],
        source=kwargs['source'],
        source_user=kwargs['source_user'],
        destination=kwargs['destination'],
        category=kwargs['category'],
        application=kwargs['application'],
        service=kwargs['service'],
        hip_profiles=kwargs['hip_profiles'],
        log_start=kwargs['log_start'],
        log_end=kwargs['log_end'],
        type=kwargs['rule_type'],
        action=kwargs['action'])

    if 'tag' in kwargs:
        security_rule.tag = kwargs['tag']

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


def add_security_rule(fw, sec_rule):
    rule_base = pandevice.policies.Rulebase.refreshall(fw)

    if rule_base:
        rule_base = rule_base[0]

        rule_base.add(sec_rule)
        sec_rule.create()

        return True
    else:
        return False


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        rule_name=dict(required=True),
        description=dict(default=''),
        tag=dict(),
        to_zone=dict(type='list', default=['any']),
        from_zone=dict(type='list', default=['any']),
        source=dict(type='list', default=["any"]),
        source_user=dict(type='list', default=['any']),
        destination=dict(type='list', default=["any"]),
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
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']
    rule_name = module.params['rule_name']
    description = module.params['description']
    tag = module.params['tag']
    from_zone = module.params['from_zone']
    to_zone = module.params['to_zone']
    source = module.params['source']
    source_user = module.params['source_user']
    destination = module.params['destination']
    category = module.params['category']
    application = module.params['application']
    service = module.params['service']
    hip_profiles = module.params['hip_profiles']
    log_start = module.params['log_start']
    log_end = module.params['log_end']
    rule_type = module.params['rule_type']
    action = module.params['action']

    group_profile = module.params['group_profile']
    antivirus = module.params['antivirus']
    vulnerability = module.params['vulnerability']
    spyware = module.params['spyware']
    url_filtering = module.params['url_filtering']
    file_blocking = module.params['file_blocking']
    data_filtering = module.params['data_filtering']
    wildfire_analysis = module.params['wildfire_analysis']

    commit = module.params['commit']

    fw = pandevice.firewall.Firewall(ip_address, username, password)

    if security_rule_exists(fw, rule_name):
        module.fail_json(msg='Rule with the same name already exists.')

    try:
        sec_rule = create_security_rule(
            rule_name=rule_name,
            description=description,
            tag=tag,
            from_zone=from_zone,
            to_zone=to_zone,
            source=source,
            source_user=source_user,
            destination=destination,
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

        changed = add_security_rule(fw, sec_rule)
    except PanXapiError:
        exc = get_exception()
        module.fail_json(msg=exc.message)

    if changed and commit:
        fw.commit(sync=True)

    module.exit_json(changed=changed, msg="okey dokey")


if __name__ == '__main__':
    main()
