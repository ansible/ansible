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
    description:
    - List of telephone numbers assigned to the user.
    - If an empty list is passed all assigned telephone numbers will be deleted.
    - If None is passed telephone numbers will not be checked or changed.
    required: false
  title:
    description: Title
    required: false
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
'''

RETURN = '''
user:
  description: User as returned by IPA API
  returned: always
  type: dict
'''

import base64
import hashlib
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient
from ansible.module_utils._text import to_native


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


def get_user_dict(displayname=None, givenname=None, loginshell=None, mail=None, nsaccountlock=False, sn=None,
                  sshpubkey=None, telephonenumber=None, title=None, userpassword=None):
    user = {}
    if displayname is not None:
        user['displayname'] = displayname
    if givenname is not None:
        user['givenname'] = givenname
    if loginshell is not None:
        user['loginshell'] = loginshell
    if mail is not None:
        user['mail'] = mail
    user['nsaccountlock'] = nsaccountlock
    if sn is not None:
        user['sn'] = sn
    if sshpubkey is not None:
        user['ipasshpubkey'] = sshpubkey
    if telephonenumber is not None:
        user['telephonenumber'] = telephonenumber
    if title is not None:
        user['title'] = title
    if userpassword is not None:
        user['userpassword'] = userpassword

    return user


def get_user_diff(client, ipa_user, module_user):
    """
        Return the keys of each dict whereas values are different. Unfortunately the IPA
        API returns everything as a list even if only a single value is possible.
        Therefore some more complexity is needed.
        The method will check if the value type of module_user.attr is not a list and
        create a list with that element if the same attribute in ipa_user is list. In this way I hope that the method
        must not be changed if the returned API dict is changed.
    :param ipa_user:
    :param module_user:
    :return:
    """
    # sshpubkeyfp is the list of ssh key fingerprints. IPA doesn't return the keys itself but instead the fingerprints.
    # These are used for comparison.
    sshpubkey = None
    if 'ipasshpubkey' in module_user:
        module_user['sshpubkeyfp'] = [get_ssh_key_fingerprint(pubkey) for pubkey in module_user['ipasshpubkey']]
        # Remove the ipasshpubkey element as it is not returned from IPA but save it's value to be used later on
        sshpubkey = module_user['ipasshpubkey']
        del module_user['ipasshpubkey']

    result = client.get_diff(ipa_data=ipa_user, module_data=module_user)

    # If there are public keys, remove the fingerprints and add them back to the dict
    if sshpubkey is not None:
        del module_user['sshpubkeyfp']
        module_user['ipasshpubkey'] = sshpubkey
    return result


def get_ssh_key_fingerprint(ssh_key):
    """
    Return the public key fingerprint of a given public SSH key
    in format "FB:0C:AC:0A:07:94:5B:CE:75:6E:63:32:13:AD:AD:D7 [user@host] (ssh-rsa)"
    :param ssh_key:
    :return:
    """
    parts = ssh_key.strip().split()
    if len(parts) == 0:
        return None
    key_type = parts[0]
    key = base64.b64decode(parts[1].encode('ascii'))

    fp_plain = hashlib.md5(key).hexdigest()
    key_fp = ':'.join(a + b for a, b in zip(fp_plain[::2], fp_plain[1::2])).upper()
    if len(parts) < 3:
        return "%s (%s)" % (key_fp, key_type)
    else:
        user_host = parts[2]
        return "%s %s (%s)" % (key_fp, user_host, key_type)


def ensure(module, client):
    state = module.params['state']
    name = module.params['name']
    nsaccountlock = state == 'disabled'

    module_user = get_user_dict(displayname=module.params.get('displayname'),
                                givenname=module.params.get('givenname'),
                                loginshell=module.params['loginshell'],
                                mail=module.params['mail'], sn=module.params['sn'],
                                sshpubkey=module.params['sshpubkey'], nsaccountlock=nsaccountlock,
                                telephonenumber=module.params['telephonenumber'], title=module.params['title'],
                                userpassword=module.params['password'])

    ipa_user = client.user_find(name=name)

    changed = False
    if state in ['present', 'enabled', 'disabled']:
        if not ipa_user:
            changed = True
            if not module.check_mode:
                ipa_user = client.user_add(name=name, item=module_user)
        else:
            diff = get_user_diff(client, ipa_user, module_user)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    ipa_user = client.user_mod(name=name, item=module_user)
    else:
        if ipa_user:
            changed = True
            if not module.check_mode:
                client.user_del(name)

    return changed, ipa_user


def main():
    module = AnsibleModule(
        argument_spec=dict(
            displayname=dict(type='str', required=False),
            givenname=dict(type='str', required=False),
            loginshell=dict(type='str', required=False),
            mail=dict(type='list', required=False),
            sn=dict(type='str', required=False),
            uid=dict(type='str', required=True, aliases=['name']),
            password=dict(type='str', required=False, no_log=True),
            sshpubkey=dict(type='list', required=False),
            state=dict(type='str', required=False, default='present',
                       choices=['present', 'absent', 'enabled', 'disabled']),
            telephonenumber=dict(type='list', required=False),
            title=dict(type='str', required=False),
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

    # If sshpubkey is defined as None than module.params['sshpubkey'] is [None]. IPA itself returns None (not a list).
    # Therefore a small check here to replace list(None) by None. Otherwise get_user_diff() would return sshpubkey
    # as different which should be avoided.
    if module.params['sshpubkey'] is not None:
        if len(module.params['sshpubkey']) == 1 and module.params['sshpubkey'][0] is "":
            module.params['sshpubkey'] = None

    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, user = ensure(module, client)
        module.exit_json(changed=changed, user=user)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
