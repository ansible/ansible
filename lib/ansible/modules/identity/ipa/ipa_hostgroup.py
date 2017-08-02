#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_hostgroup
author: Thomas Krahn (@Nosmoht)
short_description: Manage FreeIPA host-group
description:
- Add, modify and delete an IPA host-group using IPA API
options:
  cn:
    description:
    - Name of host-group.
    - Can not be changed as it is the unique identifier.
    required: true
    aliases: ["name"]
  description:
    description:
    - Description
    required: false
  host:
    description:
    - List of hosts that belong to the host-group.
    - If an empty list is passed all hosts will be removed from the group.
    - If option is omitted hosts will not be checked or changed.
    - If option is passed all assigned hosts that are not passed will be unassigned from the group.
    required: false
  hostgroup:
    description:
    - List of host-groups than belong to that host-group.
    - If an empty list is passed all host-groups will be removed from the group.
    - If option is omitted host-groups will not be checked or changed.
    - If option is passed all assigned hostgroups that are not passed will be unassigned from the group.
    required: false
  state:
    description:
    - State to ensure.
    required: false
    default: "present"
    choices: ["present", "absent"]
  ipa_port:
    description: Port of IPA server
    required: false
    default: 443
  ipa_host:
    description: IP or hostname of IPA server
    required: false
    default: "ipa.example.com"
  ipa_user:
    description: Administrative account used on IPA server
    required: false
    default: "admin"
  ipa_pass:
    description: Password of administrative user
    required: true
  ipa_prot:
    description: Protocol used by IPA server
    required: false
    default: "https"
    choices: ["http", "https"]
  validate_certs:
    description:
    - This only applies if C(ipa_prot) is I(https).
    - If set to C(no), the SSL certificates will not be validated.
    - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    required: false
    default: true
version_added: "2.3"
'''

EXAMPLES = '''
# Ensure host-group databases is present
- ipa_hostgroup:
    name: databases
    state: present
    host:
    - db.example.com
    hostgroup:
    - mysql-server
    - oracle-server
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure host-group databases is absent
- ipa_hostgroup:
    name: databases
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
hostgroup:
  description: Hostgroup as returned by IPA API.
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient
from ansible.module_utils._text import to_native


class HostGroupIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(HostGroupIPAClient, self).__init__(module, host, port, protocol)

    def hostgroup_find(self, name):
        return self._post_json(method='hostgroup_find', name=None, item={'all': True, 'cn': name})

    def hostgroup_add(self, name, item):
        return self._post_json(method='hostgroup_add', name=name, item=item)

    def hostgroup_mod(self, name, item):
        return self._post_json(method='hostgroup_mod', name=name, item=item)

    def hostgroup_del(self, name):
        return self._post_json(method='hostgroup_del', name=name)

    def hostgroup_add_member(self, name, item):
        return self._post_json(method='hostgroup_add_member', name=name, item=item)

    def hostgroup_add_host(self, name, item):
        return self.hostgroup_add_member(name=name, item={'host': item})

    def hostgroup_add_hostgroup(self, name, item):
        return self.hostgroup_add_member(name=name, item={'hostgroup': item})

    def hostgroup_remove_member(self, name, item):
        return self._post_json(method='hostgroup_remove_member', name=name, item=item)

    def hostgroup_remove_host(self, name, item):
        return self.hostgroup_remove_member(name=name, item={'host': item})

    def hostgroup_remove_hostgroup(self, name, item):
        return self.hostgroup_remove_member(name=name, item={'hostgroup': item})


def get_hostgroup_dict(description=None):
    data = {}
    if description is not None:
        data['description'] = description
    return data


def get_hostgroup_diff(client, ipa_hostgroup, module_hostgroup):
    return client.get_diff(ipa_data=ipa_hostgroup, module_data=module_hostgroup)


def ensure(module, client):
    name = module.params['name']
    state = module.params['state']
    host = module.params['host']
    hostgroup = module.params['hostgroup']

    ipa_hostgroup = client.hostgroup_find(name=name)
    module_hostgroup = get_hostgroup_dict(description=module.params['description'])

    changed = False
    if state == 'present':
        if not ipa_hostgroup:
            changed = True
            if not module.check_mode:
                ipa_hostgroup = client.hostgroup_add(name=name, item=module_hostgroup)
        else:
            diff = get_hostgroup_diff(client, ipa_hostgroup, module_hostgroup)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    data = {}
                    for key in diff:
                        data[key] = module_hostgroup.get(key)
                    client.hostgroup_mod(name=name, item=data)

        if host is not None:
            changed = client.modify_if_diff(name, ipa_hostgroup.get('member_host', []), [item.lower() for item in host],
                                            client.hostgroup_add_host, client.hostgroup_remove_host) or changed

        if hostgroup is not None:
            changed = client.modify_if_diff(name, ipa_hostgroup.get('member_hostgroup', []),
                                            [item.lower() for item in hostgroup],
                                            client.hostgroup_add_hostgroup,
                                            client.hostgroup_remove_hostgroup) or changed

    else:
        if ipa_hostgroup:
            changed = True
            if not module.check_mode:
                client.hostgroup_del(name=name)

    return changed, client.hostgroup_find(name=name)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cn=dict(type='str', required=True, aliases=['name']),
            description=dict(type='str', required=False),
            host=dict(type='list', required=False),
            hostgroup=dict(type='list', required=False),
            state=dict(type='str', required=False, default='present',
                       choices=['present', 'absent', 'enabled', 'disabled']),
            ipa_prot=dict(type='str', required=False, default='https', choices=['http', 'https']),
            ipa_host=dict(type='str', required=False, default='ipa.example.com'),
            ipa_port=dict(type='int', required=False, default=443),
            ipa_user=dict(type='str', required=False, default='admin'),
            ipa_pass=dict(type='str', required=True, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
        ),
        supports_check_mode=True,
    )

    client = HostGroupIPAClient(module=module,
                                host=module.params['ipa_host'],
                                port=module.params['ipa_port'],
                                protocol=module.params['ipa_prot'])

    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, hostgroup = ensure(module, client)
        module.exit_json(changed=changed, hostgroup=hostgroup)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
