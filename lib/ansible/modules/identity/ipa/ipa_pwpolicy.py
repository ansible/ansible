#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Damian Bicz <b1czuu@gmail.com>
# Based on ipa_config.py module developed by:
# Copyright: (c) 2018, Fran Fitzpatrick <francis.x.fitzpatrick@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_pwpolicy
author: Damian Bicz (@b1czu)
short_description: Manage FreeIPA Password Policies
description:
- Add, delete and modify an IPA Password Policies using IPA API. Ommited values are not changed during module execution.
options:
  cn:
    description: Policy name.
    required: true
    type: str
    aliases: ["group"]
  cospriority:
    description: Priority of the policy (higher number means lower priority). Ignored if group=global_policy
    required: true
    type: int
    aliases: ["priority"]
  state:
    description: State to ensure
    required: false
    type: str
    default: present
    choices: ["present", "absent"]
  krbminpwdlife:
    description: Minimum password lifetime (in hours).
    required: false
    type: int
    aliases: ["minlifetime"]
  krbmaxpwdlife:
    description: Maximum password lifetime (in days).
    required: false
    type: int
    aliases: ["maxlifetime"]
  krbpwdhistorylength:
    description: Password history size.
    required: false
    type: int
    aliases: ["historysize"]
  krbpwdmindiffchars:
    description: Minimum number of character classes.
    required: false
    type: int
    aliases: ["characterclasses"]
  krbpwdminlength:
    description: Minimum length of password.
    required: false
    type: int
    aliases: ["minlength"]
  krbpwdmaxfailure:
    description: Consecutive failures before lockout.
    required: false
    type: int
    aliases: ["maxfailures"]
  krbpwdfailurecountinterval:
    description: Period after which failure count will be reset (seconds).
    required: false
    type: int
    aliases: ["failureresetinterval"]
  krbpwdlockoutduration:
    description: Period for which lockout is enforced (seconds).
    required: false
    type: int
    aliases: ["lockoutduration"]

extends_documentation_fragment: ipa.documentation
version_added: "2.10"
'''

EXAMPLES = '''
# Modify default IPA password policy.
- ipa_pwpolicy:
    group: global_policy
    priority: 0
    minlifetime: 168
    maxlifetime: 180
    historysize: 5
    characterclasses: 3
    minlength: 8
    maxfailures: 5
    failureresetinterval: 60
    lockoutduration: 600
    ipa_host: localhost
    ipa_user: admin
    ipa_pass: supersecret

# Ensure minimum password length for group 'support'.
- ipa_pwpolicy:
    group: support
    priority: 10
    minlength: 16
    ipa_host: localhost
    ipa_user: admin
    ipa_pass: supersecret

# Ensure that password policy for group 'editors' does not exist.
- ipa_pwpolicy:
    state: absent
    group: editors
    priority: 10
    ipa_host: localhost
    ipa_user: admin
    ipa_pass: supersecret
'''

RETURN = '''
pwpolicy:
  description: Password policy as returned by IPA API
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class PwPolicyIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(PwPolicyIPAClient, self).__init__(module, host, port, protocol)

    def pwpolicy_find(self, cn):
        return self._post_json(method='pwpolicy_find', name=cn, item={'all': True})

    def pwpolicy_show(self, cn):
        return self._post_json(method='pwpolicy_show', name=cn, item={'all': True})

    def pwpolicy_add(self, cn, item):
        return self._post_json(method='pwpolicy_add', name=cn, item=item)

    def pwpolicy_mod(self, cn, item):
        return self._post_json(method='pwpolicy_mod', name=cn, item=item)

    def pwpolicy_del(self, cn):
        return self._post_json(method='pwpolicy_del', name=cn)


def get_pwpolicy_dict(krbminpwdlife=None, krbmaxpwdlife=None, krbpwdhistorylength=None,
                      krbpwdmindiffchars=None, krbpwdminlength=None, krbpwdmaxfailure=None,
                      krbpwdfailurecountinterval=None, krbpwdlockoutduration=None, cospriority=None):
    pwpolicy = {}
    if krbminpwdlife is not None:
        pwpolicy['krbminpwdlife'] = str(krbminpwdlife)
    if krbmaxpwdlife is not None:
        pwpolicy['krbmaxpwdlife'] = str(krbmaxpwdlife)
    if krbpwdhistorylength is not None:
        pwpolicy['krbpwdhistorylength'] = str(krbpwdhistorylength)
    if krbpwdmindiffchars is not None:
        pwpolicy['krbpwdmindiffchars'] = str(krbpwdmindiffchars)
    if krbpwdminlength is not None:
        pwpolicy['krbpwdminlength'] = str(krbpwdminlength)
    if krbpwdmaxfailure is not None:
        pwpolicy['krbpwdmaxfailure'] = str(krbpwdmaxfailure)
    if krbpwdfailurecountinterval is not None:
        pwpolicy['krbpwdfailurecountinterval'] = str(krbpwdfailurecountinterval)
    if krbpwdlockoutduration is not None:
        pwpolicy['krbpwdlockoutduration'] = str(krbpwdlockoutduration)
    if cospriority is not None:
        pwpolicy['cospriority'] = str(cospriority)

    return pwpolicy


def get_pwpolicy_diff(client, ipa_pwpolicy, module_pwpolicy):
    return client.get_diff(ipa_data=ipa_pwpolicy, module_data=module_pwpolicy)


def ensure(module, client):
    cn = module.params['cn']
    state = module.params['state']
    if cn == 'global_policy':
        cospriority = None
    else:
        cospriority = module.params.get('cospriority')

    module_pwpolicy = get_pwpolicy_dict(
        krbminpwdlife=module.params.get('krbminpwdlife'),
        krbmaxpwdlife=module.params.get('krbmaxpwdlife'),
        krbpwdhistorylength=module.params.get('krbpwdhistorylength'),
        krbpwdmindiffchars=module.params.get('krbpwdmindiffchars'),
        krbpwdminlength=module.params.get('krbpwdminlength'),
        krbpwdmaxfailure=module.params.get('krbpwdmaxfailure'),
        krbpwdfailurecountinterval=module.params.get('krbpwdfailurecountinterval'),
        krbpwdlockoutduration=module.params.get('krbpwdlockoutduration'),
        cospriority=cospriority,
    )
    ipa_pwpolicy = client.pwpolicy_find(cn)

    changed = False
    if state == 'present':
        if not ipa_pwpolicy:
            changed = True
            if not module.check_mode:
                ipa_pwpolicy = client.pwpolicy_add(cn=cn, item=module_pwpolicy)
        else:
            diff = get_pwpolicy_diff(client, ipa_pwpolicy, module_pwpolicy)
            if len(diff) > 0:
                changed = True
                changed_pwpolicy = {k: module_pwpolicy.get(k, None) for k in diff}
                if not module.check_mode:
                    ipa_pwpolicy = client.pwpolicy_mod(cn=cn, item=changed_pwpolicy)
    else:
        if ipa_pwpolicy:
            changed = True
            if not module.check_mode:
                ipa_pwpolicy = client.pwpolicy_del(cn=cn)

    return changed, ipa_pwpolicy


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(
        cn=dict(type='str', required=True, aliases=['group']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        krbminpwdlife=dict(type='int', aliases=['minlifetime']),
        krbmaxpwdlife=dict(type='int', aliases=['maxlifetime']),
        krbpwdhistorylength=dict(type='int', aliases=['historysize']),
        krbpwdmindiffchars=dict(type='int', aliases=['characterclasses']),
        krbpwdminlength=dict(type='int', aliases=['minlength']),
        krbpwdmaxfailure=dict(type='int', aliases=['maxfailures']),
        krbpwdfailurecountinterval=dict(type='int', aliases=['failureresetinterval']),
        krbpwdlockoutduration=dict(type='int', aliases=['lockoutduration']),
        cospriority=dict(type='int', required=True, aliases=['priority']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    client = PwPolicyIPAClient(
        module=module,
        host=module.params['ipa_host'],
        port=module.params['ipa_port'],
        protocol=module.params['ipa_prot']
    )

    try:
        client.login(
            username=module.params['ipa_user'],
            password=module.params['ipa_pass']
        )
        changed, user = ensure(module, client)
        module.exit_json(changed=changed, user=user)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
