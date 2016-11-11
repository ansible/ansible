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

DOCUMENTATION = '''
---
module: ipa_user
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
- json
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

try:
    import json
except ImportError:
    import simplejson as json


class IPAClient:
    def __init__(self, module, host, port, protocol):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.module = module
        self.headers = None

    def get_base_url(self):
        return '%s://%s/ipa' % (self.protocol, self.host)

    def get_json_url(self):
        return '%s/session/json' % self.get_base_url()

    def login(self, username, password):
        url = '%s/session/login_password' % self.get_base_url()
        data = 'user=%s&password=%s' % (username, password)
        headers = {'referer': self.get_base_url(),
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'Accept': 'text/plain'}
        try:
            resp, info = fetch_url(module=self.module, url=url, data=data, headers=headers)
            status_code = info['status']
            if status_code not in [200, 201, 204]:
                self._fail('login', info['body'])

            self.headers = {'referer': self.get_base_url(),
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'Cookie': resp.info().getheader('Set-Cookie')}
        except Exception:
            e = get_exception()
            self._fail('login', str(e))

    def _fail(self, msg, e):
        if 'message' in e:
            err_string = e.get('message')
        else:
            err_string = e
        self.module.fail_json(msg='%s: %s' % (msg, err_string))

    def _post_json(self, method, name, item=None):
        if item is None:
            item = {}
        url = '%s/session/json' % self.get_base_url()
        data = {'method': method, 'params': [[name], item]}
        try:
            resp, info = fetch_url(module=self.module, url=url, data=json.dumps(data), headers=self.headers)
            status_code = info['status']
            if status_code not in [200, 201, 204]:
                self._fail(method, info['body'])
        except Exception:
            e = get_exception()
            self._fail('post %s' % method, str(e))

        resp = json.loads(resp.read())
        err = resp.get('error')
        if err is not None:
            self._fail('repsonse %s' % method, err)

        if 'result' in resp:
            result = resp.get('result')
            if 'result' in result:
                result = result.get('result')
                if isinstance(result, list):
                    if len(result) > 0:
                        return result[0]
                    else:
                        return {}
            return result
        return None

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


def get_user_dict(givenname=None, loginshell=None, mail=None, nsaccountlock=False, sn=None, sshpubkey=None,
                  telephonenumber=None,
                  title=None):
    user = {}
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

    return user


def get_user_diff(ipa_user, module_user):
    """
        Return the keys of each dict whereas values are different. Unfortunately the IPA
        API returns everything as a list even if only a single value is possible.
        Therefore some more complexity is needed.
        The method will check if the value type of module_user.attr is not a list and
        create a list with that element if the same attribute in ipa_user is list. In this way i hope that the method
        must not be changed if the returned API dict is changed.
    :param ipa_user:
    :param module_user:
    :return:
    """
    #    return [item for item in module_user.keys() if module_user.get(item, None) != ipa_user.get(item, None)]
    result = []
    # sshpubkeyfp is the list of ssh key fingerprints. IPA doesn't return the keys itself but instead the fingerprints.
    # These are used for comparison.
    sshpubkey = None
    if 'ipasshpubkey' in module_user:
        module_user['sshpubkeyfp'] = [get_ssh_key_fingerprint(pubkey) for pubkey in module_user['ipasshpubkey']]
        # Remove the ipasshpubkey element as it is not returned from IPA but save it's value to be used later on
        sshpubkey = module_user['ipasshpubkey']
        del module_user['ipasshpubkey']
    for key in module_user.keys():
        mod_value = module_user.get(key, None)
        ipa_value = ipa_user.get(key, None)
        if isinstance(ipa_value, list) and not isinstance(mod_value, list):
            mod_value = [mod_value]
        if isinstance(ipa_value, list) and isinstance(mod_value, list):
            mod_value = sorted(mod_value)
            ipa_value = sorted(ipa_value)
        if mod_value != ipa_value:
            result.append(key)
    # If there are public keys, remove the fingerprints and add them back to the dict
    if sshpubkey is not None:
        del module_user['sshpubkeyfp']
        module_user['ipasshpubkey'] = sshpubkey
    return result


def get_ssh_key_fingerprint(ssh_key):
    """
    Return the public key fingerprint of a given public SSH key
    in format "FB:0C:AC:0A:07:94:5B:CE:75:6E:63:32:13:AD:AD:D7 (ssh-rsa)"
    :param ssh_key:
    :return:
    """
    parts = ssh_key.strip().split()
    if len(parts) == 0:
        return None
    key_type = parts[0]
    key = base64.b64decode(parts[1].encode('ascii'))

    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join(a + b for a, b in zip(fp_plain[::2], fp_plain[1::2])).upper() + ' (%s)' % key_type


def ensure(module, client):
    state = module.params['state']
    name = module.params['name']
    nsaccountlock = state == 'disabled'

    module_user = get_user_dict(givenname=module.params.get('givenname'), loginshell=module.params['loginshell'],
                                mail=module.params['mail'], sn=module.params['sn'],
                                sshpubkey=module.params['sshpubkey'], nsaccountlock=nsaccountlock,
                                telephonenumber=module.params['telephonenumber'], title=module.params['title'])

    ipa_user = client.user_find(name=name)

    changed = False
    if state in ['present', 'enabled', 'disabled']:
        if not ipa_user:
            changed = True
            if not module.check_mode:
                ipa_user = client.user_add(name=name, item=module_user)
        else:
            diff = get_user_diff(ipa_user, module_user)
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

    client = IPAClient(module=module,
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
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.urls import fetch_url

if __name__ == '__main__':
    main()
