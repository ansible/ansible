#!/usr/bin/python
# -*- coding: utf-8 -*-
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_user
author: Thomas Krahn (@Nosmoht)
short_description: Manage FreeIPA users
description:
- Add, modify and delete user within IPA server
options:
  displayname:
    description: Display name
    required: false
  givenname:
    description: First name
    required: false
  loginshell:
    description: Login shell
    required: false
  mail:
    description:
    - List of mail addresses assigned to the user.
    - If an empty list is passed all assigned email addresses will be deleted.
    - If None is passed email addresses will not be checked or changed.
    required: false
  password:
    description:
    - Password
    required: false
  sn:
    description: Surname
    required: false
  sshpubkey:
    description:
    - List of public SSH key.
    - If an empty list is passed all assigned public keys will be deleted.
    - If None is passed SSH public keys will not be checked or changed.
    required: false
  state:
    description: State to ensure
    required: false
    default: "present"
    choices: ["present", "absent", "enabled", "disabled"]
  telephonenumber:
    description: List of telephone numbers assigned to the user.
    required: false
  mobile:
    description: List of mobile telephone numbers assigned to the user.
    required: false
  pager:
    description: List of pager numbers assigned to the user.
    required: false
  facsimiletelephonenumber:
    description: List of fax numbers assigned to the user.
    required: false
  title:
    description: Job Title
    required: false
  initials:
    description: initials
    required: false
  random:
    description:
    - Generate a random password if the user is created.
    - If the user is modified this parameter is ignored.
    - To enforce a new random password for a user set the new_random flag.
    required: false
    default: false
  new_random:
    description:
    - This parameter is ignored if the user is created.
    - If the user is modified and this flag is true, a new random password is generated each time Ansible runs.
    - Normally you don't want to set this true, since this resets the password when Ansible runs.
    required: false
    default: false
  street:
    description: Street address
    required: false
  l:
    description: City
    required: false
  st:
    description: State/Province
    required: false
  postalcode:
    description: ZIP
    required: false
  ou:
    description: Org. Unit
    required: false
  manager:
    description: Manager
    required: false
  carlicense:
    description: Car License
    required: false
  homedirectory:
    description: Home directory
    required: false
  uidnumber:
    description: User ID Number (system will assign one if not provided)
    required: false
  gidnumber:
    description: Group ID Number
    required: false
  noprivate:
    description: Don't create user private group
    required: false
    default: false
  uid:
    description: uid of the user
    required: true
    aliases: ["name"]
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
requirements:
- base64
- hashlib
'''

EXAMPLES = '''
# Ensure pinky is present
- ipa_user:
    name: pinky
    state: present
    givenname: Pinky
    sn: Acme
    mail:
    - pinky@acme.com
    telephonenumber:
    - '+555123456'
    sshpubkeyfp:
    - ssh-rsa ....
    - ssh-dsa ....
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure brain is absent
- ipa_user:
    name: brain
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Ensure Alice and Bob are present, and get a random password assigned.
# The generated password will be added to a file located on the host running Ansible.
- ipa_user: "{{ item|combine({'random':true, 'ipa_host':'ipa.example.com', 'ipa_pass':'admin'}) }}"
  register: ipa_user_result
  with_items:
  - { 'name':'alice' }
  - { 'name':'bob' }
- local_action: lineinfile create=yes dest=./random_passwd.txt line="{{ item.user.uid[0] }}, {{ item.user.randompassword }}" regexp="{{ item.user.uid[0] }}"
  when: item.user.uid is defined and item.user.randompassword is defined
  with_items: "{{ ipa_user_result.results|default([]) }}"
'''

RETURN = '''
user:
  description: User as returned by IPA API
  returned: always
  type: dict
'''

import base64
import hashlib

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.ipa import IPAClient
from ansible.module_utils.ipa import ANSIBLE_INT_IPA_KEYS


class UserIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(UserIPAClient, self).__init__(module, host, port, protocol)

    def user_find(self, name):
        return self._post_json(method='user_find', name=None, item={'all': True, 'uid': name})

    def user_add(self, name, item):
        return self._post_json(method='user_add', name=name, item=item)

    def user_mod(self, name, item):
        return self._post_json(method='user_mod', name=name, item=item)

    def user_del(self, name):
        return self._post_json(method='user_del', name=name)

    def user_disable(self, name):
        return self._post_json(method='user_disable', name=name)

    def user_enable(self, name):
        return self._post_json(method='user_enable', name=name)


def ensure(module, client):
    state = module.params['state']
    name = module.params['name']
    new_random = module.params['new_random']

    # Fetch the user from FreeIPA if already existing
    ipa_user = client.user_find(name=name)

    changed = True
    if state in ['present', 'enabled', 'disabled']:

        # Create a reduced copy of module.params containing only parameters forwarded to FreeIPA
        module_user = {}
        skipped_keys = ANSIBLE_INT_IPA_KEYS + ['name', 'uid', 'sshpubkey', 'new_random']
        if ipa_user:  # Remove user_add specific fields if user_mod will be called
            skipped_keys = skipped_keys + ['noprivate']
            # Do not generate a new random password until explicitly requested by new_random parameter
            if not new_random:
                skipped_keys = skipped_keys + ['random']

        if state == 'disabled':
            module_user['nsaccountlock'] = True
        for key,val in module.params.items():
            if val is None:
                continue
            if key in skipped_keys:
                continue
            module_user[key] = val

        if not module.check_mode:
            if not ipa_user:  # Add a new user (user_add)
                ipa_user = client.user_add(name=name, item=module_user)
            else:  # Modify an existing user (user_mod)
                ipa_user = client.user_mod(name=name, item=module_user)
                if 'ipa_changed' in ipa_user:
                    changed = ipa_user['ipa_changed']
    else:  # user_del
        if ipa_user:
            if not module.check_mode:
                client.user_del(name)
            ipa_user = None
        else:
            changed = False

    return changed, ipa_user


def main():
    module = AnsibleModule(
        argument_spec=dict(
            displayname=dict(type='str', required=False),
            givenname=dict(type='str', required=False),
            initials=dict(type='str', required=False),
            loginshell=dict(type='str', required=False),
            mail=dict(type='list', required=False),
            sn=dict(type='str', required=False),
            uid=dict(type='str', required=True, aliases=['name']),
            password=dict(type='str', required=False, no_log=True),
            random=dict(type='bool', required=False, default=False),
            new_random=dict(type='bool', required=False, default=False),
            uidnumber=dict(type='int', required=False),
            gidnumber=dict(type='int', required=False),
            ipasshpubkey=dict(type='list', required=False, aliases=['sshpubkey']),
            state=dict(type='str', required=False, default='present',
                       choices=['present', 'absent', 'enabled', 'disabled']),
            street=dict(type='str', required=False),
            l=dict(type='str', required=False),
            st=dict(type='str', required=False),
            postalcode=dict(type='str', required=False),
            telephonenumber=dict(type='list', required=False),
            mobile=dict(type='list', required=False),
            pager=dict(type='list', required=False),
            facsimiletelephonenumber=dict(type='list', required=False),
            ou=dict(type='str', required=False),
            title=dict(type='str', required=False),
            manager=dict(type='str', required=False),
            carlicense=dict(type='list', required=False),
            homedirectory=dict(type='str', required=False),
            noprivate=dict(type='bool', required=False, default=False),
            ipa_prot=dict(type='str', required=False, default='https', choices=['http', 'https']),
            ipa_host=dict(type='str', required=False, default='ipa.example.com'),
            ipa_port=dict(type='int', required=False, default=443),
            ipa_user=dict(type='str', required=False, default='admin'),
            ipa_pass=dict(type='str', required=True, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
        ),
        supports_check_mode=True,
    )

    client = UserIPAClient(module=module,
                           host=module.params['ipa_host'],
                           port=module.params['ipa_port'],
                           protocol=module.params['ipa_prot'])

    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, user = ensure(module, client)
        module.exit_json(changed=changed, user=user)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
