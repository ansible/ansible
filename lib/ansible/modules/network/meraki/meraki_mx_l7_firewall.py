#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: meraki_mx_l7_firewall
short_description: Manage MX appliance layer 7 firewalls in the Meraki cloud
version_added: "2.9"
description:
- Allows for creation, management, and visibility into layer 7 firewalls implemented on Meraki MX firewalls.
notes:
- Module assumes a complete list of firewall rules are passed as a parameter.
- If there is interest in this module allowing manipulation of a single firewall rule, please submit an issue against this module.
options:
    state:
        description:
        - Query or modify a firewall rule.
        choices: ['present', 'query']
        default: present
        type: str
    net_name:
        description:
        - Name of network which MX firewall is in.
        type: str
    net_id:
        description:
        - ID of network which MX firewall is in.
        type: str
    rules:
        description:
        - List of layer 7 firewall rules.
        type: list
        suboptions:
            policy:
                description:
                - Policy to apply if rule is hit.
                choices: [deny]
                default: deny
                type: str
            type:
                description:
                - Type of policy to apply.
                choices: [application,
                          application_category,
                          blacklisted_countries,
                          host,
                          ip_range,
                          port,
                          whitelisted_countries]
                type: str
            application:
                description:
                - Application to filter.
                suboptions:
                    name:
                        description:
                        - Name of application to filter as defined by Meraki.
                        type: str
                    id:
                        description:
                        - URI of application as defined by Meraki.
                        type: str
            application_category:
                description:
                - Category of applications to filter.
                suboptions:
                    name:
                        description:
                        - Name of application category to filter as defined by Meraki.
                        type: str
                    id:
                        description:
                        - URI of application category as defined by Meraki.
                        type: str
            host:
                description:
                - FQDN of host to filter.
                type: str
            ip_range:
                description:
                - CIDR notation range of IP addresses to apply rule to.
                - Port can be appended to range with a C(":").
                type: str
            port:
                description:
                - TCP or UDP based port to filter.
                type: str
            countries:
                description:
                - List of countries to whitelist or blacklist.
                - The countries follow the two-letter ISO 3166-1 alpha-2 format.
                type: list
    categories:
        description:
        - When C(True), specifies that applications and application categories should be queried instead of firewall rules.
        type: bool
author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Query firewall rules
  meraki_mx_l7_firewall:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: query
  delegate_to: localhost

- name: Query applications and application categories
  meraki_mx_l7_firewall:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    categories: yes
    state: query
  delegate_to: localhost

- name: Set firewall rules
  meraki_mx_l7_firewall:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: present
    rules:
      - type: whitelisted_countries
        countries:
          - US
          - FR
      - type: blacklisted_countries
        countries:
          - CN
      - policy: deny
        type: port
        port: 8080
      - type: port
        port: 1234
      - type: host
        host: asdf.com
      - type: application
        application:
          id: meraki:layer7/application/205
      - type: application_category
        application:
          id: meraki:layer7/category/24
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Firewall rules associated to network.
    returned: success
    type: complex
    contains:
        rules:
            description: Ordered list of firewall rules.
            returned: success, when not querying applications
            type: list
            contains:
                policy:
                    description: Action to apply when rule is hit.
                    returned: success
                    type: str
                    sample: deny
                type:
                    description: Type of rule category.
                    returned: success
                    type: str
                    sample: applications
                applications:
                    description: List of applications within a category.
                    type: list
                    contains:
                        id:
                            description: URI of application.
                            returned: success
                            type: str
                            sample: Gmail
                        name:
                            description: Descriptive name of application.
                            returned: success
                            type: str
                            sample: meraki:layer7/application/4
                applicationCategory:
                    description: List of application categories within a category.
                    type: list
                    contains:
                        id:
                            description: URI of application.
                            returned: success
                            type: str
                            sample: Gmail
                        name:
                            description: Descriptive name of application.
                            returned: success
                            type: str
                            sample: meraki:layer7/application/4
                port:
                    description: Port number in rule.
                    returned: success
                    type: str
                    sample: 23
                ipRange:
                    description: Range of IP addresses in rule.
                    returned: success
                    type: str
                    sample: 1.1.1.0/23
                whitelistedCountries:
                    description: Countries to be whitelisted.
                    returned: success
                    type: str
                    sample: CA
                blacklistedCountries:
                    description: Countries to be blacklisted.
                    returned: success
                    type: str
                    sample: RU
        application_categories:
            description: List of application categories and applications.
            type: list
            returned: success, when querying applications
            contains:
                applications:
                    description: List of applications within a category.
                    type: list
                    contains:
                        id:
                            description: URI of application.
                            returned: success
                            type: str
                            sample: Gmail
                        name:
                            description: Descriptive name of application.
                            returned: success
                            type: str
                            sample: meraki:layer7/application/4
                id:
                    description: URI of application category.
                    returned: success
                    type: string
                    sample: Email
                name:
                    description: Descriptive name of application category.
                    returned: success
                    type: string
                    sample: layer7/category/1
'''

import copy
import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.common.dict_transformations import recursive_diff
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def get_applications(meraki, net_id):
    path = meraki.construct_path('get_categories', net_id=net_id)
    return meraki.request(path, method='GET')


def lookup_application(meraki, net_id, application):
    response = get_applications(meraki, net_id)
    for category in response['applicationCategories']:
        if category['name'].lower() == application.lower():
            return category['id']
        for app in category['applications']:
            if app['name'].lower() == application.lower():
                return app['id']
    meraki.fail_json(msg="No application or category named {0} found".format(application))


def assemble_payload(meraki, net_id, rule):
    if rule['type'] == 'application':
        new_rule = {'policy': rule['policy'],
                    'type': 'application',
                    }
        if rule['application']['id']:
            new_rule['value'] = {'id': rule['application']['id']}
        elif rule['application']['name']:
            new_rule['value'] = {'id': lookup_application(meraki, net_id, rule['application']['name'])}
    elif rule['type'] == 'application_category':
        new_rule = {'policy': rule['policy'],
                    'type': 'applicationCategory',
                    }
        if rule['application']['id']:
            new_rule['value'] = {'id': rule['application']['id']}
        elif rule['application']['name']:
            new_rule['value'] = {'id': lookup_application(meraki, net_id, rule['application']['name'])}
    elif rule['type'] == 'ip_range':
        new_rule = {'policy': rule['policy'],
                    'type': 'ipRange',
                    'value': rule['ip_range']}
    elif rule['type'] == 'host':
        new_rule = {'policy': rule['policy'],
                    'type': rule['type'],
                    'value': rule['host']}
    elif rule['type'] == 'port':
        new_rule = {'policy': rule['policy'],
                    'type': rule['type'],
                    'value': rule['port']}
    elif rule['type'] == 'blacklisted_countries':
        new_rule = {'policy': rule['policy'],
                    'type': 'blacklistedCountries',
                    'value': rule['countries']
                    }
    elif rule['type'] == 'whitelisted_countries':
        new_rule = {'policy': rule['policy'],
                    'type': 'whitelistedCountries',
                    'value': rule['countries']
                    }
    return new_rule


def restructure_response(rules):
    for rule in rules['rules']:
        type = rule['type']
        rule[type] = copy.deepcopy(rule['value'])
        del rule['value']
    return rules


def get_rules(meraki, net_id):
    path = meraki.construct_path('get_all', net_id=net_id)
    response = meraki.request(path, method='GET')
    if meraki.status == 200:
        return response


def rename_id_to_appid(rules):
    for rule in rules['rules']:
        print(rule['type'])
        if rule['type'] == 'application' or rule['type'] == 'applicationCategory':
            rule['value']['appId'] = rule['value'].pop('id')
    return rules


def rename_appid_to_id(rules):
    for rule in rules['rules']:
        if rule['type'] == 'application' or rule['type'] == 'applicationCategory':
            rule['value']['id'] = rule['value'].pop('appId')
    return rules


def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    application_arg_spec = dict(id=dict(type='str'),
                                name=dict(type='str'),
                                )

    rule_arg_spec = dict(policy=dict(type='str', choices=['deny'], default='deny'),
                         type=dict(type='str', choices=['application',
                                                        'application_category',
                                                        'blacklisted_countries',
                                                        'host',
                                                        'ip_range',
                                                        'port',
                                                        'whitelisted_countries']),
                         ip_range=dict(type='str'),
                         application=dict(type='dict', default=None, options=application_arg_spec),
                         host=dict(type='str'),
                         port=dict(type='str'),
                         countries=dict(type='list'),
                         )

    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['present', 'query'], default='present'),
                         net_name=dict(type='str'),
                         net_id=dict(type='str'),
                         rules=dict(type='list', default=None, elements='dict', options=rule_arg_spec),
                         categories=dict(type='bool'),
                         )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )
    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )
    meraki = MerakiModule(module, function='mx_l7_firewall')

    # check for argument completeness
    if meraki.params['rules']:
        for rule in meraki.params['rules']:
            if rule['type'] == 'application' and rule['application'] is None:
                meraki.fail_json(msg="application argument is required when type is application.")
            elif rule['type'] == 'application_category' and rule['application'] is None:
                meraki.fail_json(msg="application argument is required when type is application_category.")
            elif rule['type'] == 'blacklisted_countries' and rule['countries'] is None:
                meraki.fail_json(msg="countries argument is required when type is blacklisted_countries.")
            elif rule['type'] == 'host' and rule['host'] is None:
                meraki.fail_json(msg="host argument is required when type is host.")
            elif rule['type'] == 'port' and rule['port'] is None:
                meraki.fail_json(msg="port argument is required when type is port.")
            elif rule['type'] == 'whitelisted_countries' and rule['countries'] is None:
                meraki.fail_json(msg="countries argument is required when type is whitelisted_countries.")

    meraki.params['follow_redirects'] = 'all'

    query_urls = {'mx_l7_firewall': '/networks/{net_id}/l7FirewallRules/'}
    query_category_urls = {'mx_l7_firewall': '/networks/{net_id}/l7FirewallRules/applicationCategories'}
    update_urls = {'mx_l7_firewall': '/networks/{net_id}/l7FirewallRules/'}

    meraki.url_catalog['get_all'].update(query_urls)
    meraki.url_catalog['get_categories'] = (query_category_urls)
    meraki.url_catalog['update'] = update_urls

    payload = None

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    org_id = meraki.params['org_id']
    orgs = None
    if org_id is None:
        orgs = meraki.get_orgs()
        for org in orgs:
            if org['name'] == meraki.params['org_name']:
                org_id = org['id']
    net_id = meraki.params['net_id']
    if net_id is None:
        if orgs is None:
            orgs = meraki.get_orgs()
        net_id = meraki.get_net_id(net_name=meraki.params['net_name'],
                                   data=meraki.get_nets(org_id=org_id))

    if meraki.params['state'] == 'query':
        if meraki.params['categories'] is True:  # Output only applications
            meraki.result['data'] = get_applications(meraki, net_id)
        else:
            meraki.result['data'] = restructure_response(get_rules(meraki, net_id))
    elif meraki.params['state'] == 'present':
        rules = get_rules(meraki, net_id)
        path = meraki.construct_path('get_all', net_id=net_id)
        if meraki.params['rules']:
            payload = {'rules': []}
            for rule in meraki.params['rules']:
                payload['rules'].append(assemble_payload(meraki, net_id, rule))
        else:
            payload = dict()

        '''
        The rename_* functions are needed because the key is id and
        is_update_required() by default ignores id.
        '''
        rules = rename_id_to_appid(rules)
        payload = rename_id_to_appid(payload)
        if meraki.is_update_required(rules, payload):
            rules = rename_appid_to_id(rules)
            payload = rename_appid_to_id(payload)
            if meraki.module.check_mode is True:
                response = restructure_response(payload)
                diff = recursive_diff(restructure_response(rules), response)
                meraki.result['diff'] = {'before': diff[0],
                                         'after': diff[1],
                                         }
                meraki.result['data'] = response
                meraki.result['changed'] = True
                meraki.exit_json(**meraki.result)
            response = meraki.request(path, method='PUT', payload=json.dumps(payload))
            response = restructure_response(response)
            if meraki.status == 200:
                diff = recursive_diff(restructure_response(rules), response)
                meraki.result['diff'] = {'before': diff[0],
                                         'after': diff[1],
                                         }
                meraki.result['data'] = response
                meraki.result['changed'] = True
        else:
            rules = rename_appid_to_id(rules)
            payload = rename_appid_to_id(payload)
            if meraki.module.check_mode is True:
                meraki.result['data'] = rules
                meraki.result['changed'] = False
                meraki.exit_json(**meraki.result)
            meraki.result['data'] = payload

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
