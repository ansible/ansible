#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_hbacrule
author: Thomas Krahn (@Nosmoht)
short_description: Manage FreeIPA HBAC rule
description:
- Add, modify or delete an IPA HBAC rule using IPA API.
options:
  cn:
    description:
    - Canonical name.
    - Can not be changed as it is the unique identifier.
    required: true
    aliases: ["name"]
  description:
    description: Description
  host:
    description:
    - List of host names to assign.
    - If an empty list is passed all hosts will be removed from the rule.
    - If option is omitted hosts will not be checked or changed.
    required: false
  hostcategory:
    description: Host category
    choices: ['all']
  hostgroup:
    description:
    - List of hostgroup names to assign.
    - If an empty list is passed all hostgroups will be removed. from the rule
    - If option is omitted hostgroups will not be checked or changed.
  service:
    description:
    - List of service names to assign.
    - If an empty list is passed all services will be removed from the rule.
    - If option is omitted services will not be checked or changed.
  servicecategory:
    description: Service category
    choices: ['all']
  servicegroup:
    description:
    - List of service group names to assign.
    - If an empty list is passed all assigned service groups will be removed from the rule.
    - If option is omitted service groups will not be checked or changed.
  sourcehost:
    description:
    - List of source host names to assign.
    - If an empty list if passed all assigned source hosts will be removed from the rule.
    - If option is omitted source hosts will not be checked or changed.
  sourcehostcategory:
    description: Source host category
    choices: ['all']
  sourcehostgroup:
    description:
    - List of source host group names to assign.
    - If an empty list if passed all assigned source host groups will be removed from the rule.
    - If option is omitted source host groups will not be checked or changed.
  state:
    description: State to ensure
    default: "present"
    choices: ["present", "absent", "enabled", "disabled"]
  user:
    description:
    - List of user names to assign.
    - If an empty list if passed all assigned users will be removed from the rule.
    - If option is omitted users will not be checked or changed.
  usercategory:
    description: User category
    choices: ['all']
  usergroup:
    description:
    - List of user group names to assign.
    - If an empty list if passed all assigned user groups will be removed from the rule.
    - If option is omitted user groups will not be checked or changed.
extends_documentation_fragment: ipa.documentation
version_added: "2.3"
'''

EXAMPLES = '''
# Ensure rule to allow all users to access any host from any host
- ipa_hbacrule:
    name: allow_all
    description: Allow all users to access any host from any host
    hostcategory: all
    servicecategory: all
    usercategory: all
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure rule with certain limitations
- ipa_hbacrule:
    name: allow_all_developers_access_to_db
    description: Allow all developers to access any database from any host
    hostgroup:
    - db-server
    usergroup:
    - developers
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure rule is absent
- ipa_hbacrule:
    name: rule_to_be_deleted
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
hbacrule:
  description: HBAC rule as returned by IPA API.
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class HBACRuleIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(HBACRuleIPAClient, self).__init__(module, host, port, protocol)

    def hbacrule_find(self, name):
        return self._post_json(method='hbacrule_find', name=None, item={'all': True, 'cn': name})

    def hbacrule_add(self, name, item):
        return self._post_json(method='hbacrule_add', name=name, item=item)

    def hbacrule_mod(self, name, item):
        return self._post_json(method='hbacrule_mod', name=name, item=item)

    def hbacrule_del(self, name):
        return self._post_json(method='hbacrule_del', name=name)

    def hbacrule_add_host(self, name, item):
        return self._post_json(method='hbacrule_add_host', name=name, item=item)

    def hbacrule_remove_host(self, name, item):
        return self._post_json(method='hbacrule_remove_host', name=name, item=item)

    def hbacrule_add_service(self, name, item):
        return self._post_json(method='hbacrule_add_service', name=name, item=item)

    def hbacrule_remove_service(self, name, item):
        return self._post_json(method='hbacrule_remove_service', name=name, item=item)

    def hbacrule_add_user(self, name, item):
        return self._post_json(method='hbacrule_add_user', name=name, item=item)

    def hbacrule_remove_user(self, name, item):
        return self._post_json(method='hbacrule_remove_user', name=name, item=item)

    def hbacrule_add_sourcehost(self, name, item):
        return self._post_json(method='hbacrule_add_sourcehost', name=name, item=item)

    def hbacrule_remove_sourcehost(self, name, item):
        return self._post_json(method='hbacrule_remove_sourcehost', name=name, item=item)


def get_hbacrule_dict(description=None, hostcategory=None, ipaenabledflag=None, servicecategory=None,
                      sourcehostcategory=None,
                      usercategory=None):
    data = {}
    if description is not None:
        data['description'] = description
    if hostcategory is not None:
        data['hostcategory'] = hostcategory
    if ipaenabledflag is not None:
        data['ipaenabledflag'] = ipaenabledflag
    if servicecategory is not None:
        data['servicecategory'] = servicecategory
    if sourcehostcategory is not None:
        data['sourcehostcategory'] = sourcehostcategory
    if usercategory is not None:
        data['usercategory'] = usercategory
    return data


def get_hbcarule_diff(client, ipa_hbcarule, module_hbcarule):
    return client.get_diff(ipa_data=ipa_hbcarule, module_data=module_hbcarule)


def ensure(module, client):
    name = module.params['cn']
    state = module.params['state']

    if state in ['present', 'enabled']:
        ipaenabledflag = 'TRUE'
    else:
        ipaenabledflag = 'FALSE'

    host = module.params['host']
    hostcategory = module.params['hostcategory']
    hostgroup = module.params['hostgroup']
    service = module.params['service']
    servicecategory = module.params['servicecategory']
    servicegroup = module.params['servicegroup']
    sourcehost = module.params['sourcehost']
    sourcehostcategory = module.params['sourcehostcategory']
    sourcehostgroup = module.params['sourcehostgroup']
    user = module.params['user']
    usercategory = module.params['usercategory']
    usergroup = module.params['usergroup']

    module_hbacrule = get_hbacrule_dict(description=module.params['description'],
                                        hostcategory=hostcategory,
                                        ipaenabledflag=ipaenabledflag,
                                        servicecategory=servicecategory,
                                        sourcehostcategory=sourcehostcategory,
                                        usercategory=usercategory)
    ipa_hbacrule = client.hbacrule_find(name=name)

    changed = False
    if state in ['present', 'enabled', 'disabled']:
        if not ipa_hbacrule:
            changed = True
            if not module.check_mode:
                ipa_hbacrule = client.hbacrule_add(name=name, item=module_hbacrule)
        else:
            diff = get_hbcarule_diff(client, ipa_hbacrule, module_hbacrule)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    data = {}
                    for key in diff:
                        data[key] = module_hbacrule.get(key)
                    client.hbacrule_mod(name=name, item=data)

        if host is not None:
            changed = client.modify_if_diff(name, ipa_hbacrule.get('memberhost_host', []), host,
                                            client.hbacrule_add_host,
                                            client.hbacrule_remove_host, 'host') or changed

        if hostgroup is not None:
            changed = client.modify_if_diff(name, ipa_hbacrule.get('memberhost_hostgroup', []), hostgroup,
                                            client.hbacrule_add_host,
                                            client.hbacrule_remove_host, 'hostgroup') or changed

        if service is not None:
            changed = client.modify_if_diff(name, ipa_hbacrule.get('memberservice_hbacsvc', []), service,
                                            client.hbacrule_add_service,
                                            client.hbacrule_remove_service, 'hbacsvc') or changed

        if servicegroup is not None:
            changed = client.modify_if_diff(name, ipa_hbacrule.get('memberservice_hbacsvcgroup', []),
                                            servicegroup,
                                            client.hbacrule_add_service,
                                            client.hbacrule_remove_service, 'hbacsvcgroup') or changed

        if sourcehost is not None:
            changed = client.modify_if_diff(name, ipa_hbacrule.get('sourcehost_host', []), sourcehost,
                                            client.hbacrule_add_sourcehost,
                                            client.hbacrule_remove_sourcehost, 'host') or changed

        if sourcehostgroup is not None:
            changed = client.modify_if_diff(name, ipa_hbacrule.get('sourcehost_group', []), sourcehostgroup,
                                            client.hbacrule_add_sourcehost,
                                            client.hbacrule_remove_sourcehost, 'hostgroup') or changed

        if user is not None:
            changed = client.modify_if_diff(name, ipa_hbacrule.get('memberuser_user', []), user,
                                            client.hbacrule_add_user,
                                            client.hbacrule_remove_user, 'user') or changed

        if usergroup is not None:
            changed = client.modify_if_diff(name, ipa_hbacrule.get('memberuser_group', []), usergroup,
                                            client.hbacrule_add_user,
                                            client.hbacrule_remove_user, 'group') or changed
    else:
        if ipa_hbacrule:
            changed = True
            if not module.check_mode:
                client.hbacrule_del(name=name)

    return changed, client.hbacrule_find(name=name)


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(cn=dict(type='str', required=True, aliases=['name']),
                         description=dict(type='str'),
                         host=dict(type='list'),
                         hostcategory=dict(type='str', choices=['all']),
                         hostgroup=dict(type='list'),
                         service=dict(type='list'),
                         servicecategory=dict(type='str', choices=['all']),
                         servicegroup=dict(type='list'),
                         sourcehost=dict(type='list'),
                         sourcehostcategory=dict(type='str', choices=['all']),
                         sourcehostgroup=dict(type='list'),
                         state=dict(type='str', default='present', choices=['present', 'absent', 'enabled', 'disabled']),
                         user=dict(type='list'),
                         usercategory=dict(type='str', choices=['all']),
                         usergroup=dict(type='list'))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True
                           )

    client = HBACRuleIPAClient(module=module,
                               host=module.params['ipa_host'],
                               port=module.params['ipa_port'],
                               protocol=module.params['ipa_prot'])

    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, hbacrule = ensure(module, client)
        module.exit_json(changed=changed, hbacrule=hbacrule)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
