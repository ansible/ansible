#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_authserver_ldap
version_added: "2.9"
short_description: Manage pfSense LDAP authentication servers
description:
  >
    Manage pfSense LDAP authentication servers
author: Orion Poplawski (@opoplawski)
notes:
options:
  name:
    description: The name of the authentication server
    required: true
    type: str
  state:
    description: State in which to leave the authentication server
    required: true
    choices: [ "present", "absent" ]
    type: str
  host:
    description: The hostname or IP address of the authentication server
    required: true
    type: str
  port:
    description: Port to connect to
    default: 389
    type: str
  transport:
    description: Transport to use
    choices: [ "tcp", "starttls", "ssl" ]
    type: str
  ca:
    description: Certificat Authority
    type: str
  protver:
    description: LDAP protocol version
    default: 3
    choices: [ "2", "3" ]
    type: str
  timeout:
    description: Server timeout in seconds
    default: 25
    type: str
  scope:
    description: Search scope
    choices: [ 'one', 'subtree' ]
    type: str
  basedn:
    description: Search base DN
    type: str
  authcn:
    description: Authentication containers added to basedn
    type: str
  binddn:
    description: Search bind DN
    type: str
  bindpw:
    description: Search bind password
    type: str
  attr_user:
    description: LDAP User naming attribute
    default: cn
    type: str
  attr_group:
    description: LDAP Group naming attribute
    default: cn
    type: str
  attr_member:
    description: LDAP Group member naming attribute
    default: member
    type: str
  attr_groupobj:
    description: LDAP Group objectClass naming attribute
    default: posixGroup
    type: str

"""

EXAMPLES = """
- name: Add adservers authentication server
  pfsense_authserver_ldap:
    name: AD
    hostname: adserver.example.com
    port: 636
    transport: ssl
    scope: subtree
    basedn: dc=example,dc=com
    binddb: cn=bind,ou=Service Accounts,dc=example,dc=com
    bindpw: "{{ vaulted_bindpw }}"
    attr_user: samAccountName
    attr_member: memberOf
    attr_groupobj: group
    state: present

- name: Remove LDAP authentication server
  pfsense_authserver_ldap:
    name: AD
    state: absent
"""

RETURN = """

"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.pfsense import PFSenseModule


class PFSenseAuthserverLDAP(object):

    def __init__(self, module):
        self.module = module
        self.pfsense = PFSenseModule(module)
        self.system = self.pfsense.get_element('system')
        self.authservers = self.system.findall('authserver')

    def _find_authserver_ldap(self, name):
        found = None
        i = 0
        for authserver in self.authservers:
            i = list(self.system).index(authserver)
            if authserver.find('name').text == name and authserver.find('type').text == 'ldap':
                found = authserver
                break
        return (found, i)

    def add(self, authserver):
        authserver_elt, i = self._find_authserver_ldap(authserver['name'])
        changed = False

        # Replace the text CA name with the caref id
        authserver['ldap_caref'] = self.pfsense.get_caref(authserver['ca'])
        if authserver['ldap_caref'] is None and authserver['transport'] != 'tcp':
            self.module.fail_json(msg="could not find CA '%s'" % (authserver['ca']))
        del authserver['ca']
        if authserver_elt is None:
            changed = True
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            authserver_elt = self.pfsense.new_element('authserver')
            authserver['refid'] = self.pfsense.uniqid()
            self.pfsense.copy_dict_to_element(authserver, authserver_elt)
            self.system.insert(i + 1, authserver_elt)
            self.pfsense.write_config(descr='ansible pfsense_authserver_ldap added %s' % (authserver['name']))
        else:
            changed = self.pfsense.copy_dict_to_element(authserver, authserver_elt)
            if self.module.check_mode:
                self.module.exit_json(changed=changed)
            if changed:
                self.pfsense.write_config(descr='ansible pfsense_authserver_ldap updated "%s"' % (authserver['name']))
        self.module.exit_json(changed=changed)

    def remove(self, authserver):
        authserver_elt, dummy = self._find_authserver_ldap(authserver['name'])
        changed = False
        if authserver_elt is not None:
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            self.authservers.remove(authserver_elt)
            changed = True
            self.pfsense.write_config(descr='ansible pfsense_authserver_ldap removed "%s"' % (authserver['name']))
        self.module.exit_json(changed=changed)


def main():
    module = AnsibleModule(
        argument_spec={
            'name': {'required': True, 'type': 'str'},
            'state': {
                'required': True,
                'choices': ['present', 'absent']
            },
            'host': {'required': True, 'type': 'str'},
            'port': {'default': '389', 'type': 'str'},
            'transport': {
                'required': True,
                'choices': ['tcp', 'starttls', 'ssl']
            },
            'ca': {'required': False, 'type': 'str'},
            'protver': {
                'default': '3',
                'choices': ['2', '3']
            },
            'timeout': {'default': '25', 'type': 'str'},
            'scope': {
                'required': True,
                'choices': ['one', 'subtree']
            },
            'basedn': {'required': False, 'type': 'str'},
            'authcn': {'required': False, 'type': 'str'},
            'binddn': {'required': False, 'type': 'str'},
            'bindpw': {'required': False, 'type': 'str'},
            'attr_user': {'default': 'cn', 'type': 'str'},
            'attr_group': {'default': 'cn', 'type': 'str'},
            'attr_member': {'default': 'member', 'type': 'str'},
            'attr_groupobj': {'default': 'posixGroup', 'type': 'str'},
        },
        required_if=[
            ["transport", "starttls", ["ca"]],
            ["transport", "ssl", ["ca"]],
        ],
        supports_check_mode=True)

    pfauthserverldap = PFSenseAuthserverLDAP(module)

    authserver = dict()
    authserver['name'] = module.params['name']
    authserver['type'] = 'ldap'
    state = module.params['state']
    if state == 'absent':
        pfauthserverldap.remove(authserver)
    elif state == 'present':
        authserver['host'] = module.params['host']
        authserver['ldap_port'] = module.params['port']
        urltype = dict({'tcp': '', 'starttls': '', 'ssl': 'SSL - Encrypted'})
        authserver['ldap_urltype'] = urltype[module.params['transport']]
        authserver['ldap_protver'] = module.params['protver']
        authserver['ldap_timeout'] = module.params['timeout']
        authserver['ldap_scope'] = module.params['scope']
        authserver['ldap_basedn'] = module.params['basedn']
        authserver['ldap_authcn'] = module.params['authcn']
        authserver['ldap_binddn'] = module.params['binddn']
        authserver['ldap_bindpw'] = module.params['bindpw']
        authserver['ldap_attr_user'] = module.params['attr_user']
        authserver['ldap_attr_group'] = module.params['attr_group']
        authserver['ldap_attr_member'] = module.params['attr_member']
        authserver['ldap_attr_groupobj'] = module.params['attr_groupobj']
        # This gets replaced by add()
        authserver['ca'] = module.params['ca']
        pfauthserverldap.add(authserver)


if __name__ == '__main__':
    main()
