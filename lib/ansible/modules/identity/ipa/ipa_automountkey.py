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
module: ipa_automountkey
author: Damian Bicz (@b1czu)
short_description: Manage FreeIPA Automount Keys
description:
- Add, delete and modify an IPA Automount Key using IPA API.
options:
  state:
    description: State to ensure
    required: false
    type: str
    default: present
    choices: ["present", "absent"]
  key:
    description: Automount key name.
    required: true
    type: str
  locationcn:
    description: Automount location name.
    required: true
    type: str
    aliases: ["location"]
  mapname:
    description: Automount map name.
    required: true
    type: str
    aliases: ["map"]
  mountinformation:
    description: Mount information.
    required: false
    type: str
    aliases: ["information"]
extends_documentation_fragment: ipa.documentation
version_added: "2.10"
'''

EXAMPLES = '''
# Ensure that /exports/nas key in auto.direct map is present
- ipa_automountkey:
    state: present
    key: /exports/nas
    mountinformation: '-rw,soft,rsize=8192,wsize=8192 nas-server:/exports/nas/'
    location: default
    mapname: auto.direct
    ipa_host: localhost
    ipa_user: admin
    ipa_pass: topsecret

# Ensure that /exports/nas key in auto.direct map is absent
- ipa_automountkey:
    state: absent
    key: /exports/nas
    location: default
    mapname: auto.direct
    ipa_host: localhost
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
automountkey:
  description: Automount Key as returned by IPA API
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class AutoMountKeyIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(AutoMountKeyIPAClient, self).__init__(module, host, port, protocol)

    def automountkey_find(self, args):
        return self._post_json(method='automountkey_find', name=args, item={'all': True})

    def automountkey_show(self, args):
        return self._post_json(method='automountkey_show', name=args, item={'all': True})

    def automountkey_add(self, args, item):
        return self._post_json(method='automountkey_add', name=args, item=item)

    def automountkey_mod(self, args, item):
        return self._post_json(method='automountkey_mod', name=args, item=item)

    def automountkey_del(self, args, item):
        return self._post_json(method='automountkey_del', name=args, item=item)


def get_automountkey_dict(key=None, mountinformation=None):
    automountkey = {}
    if key is not None:
        automountkey['automountkey'] = key
    if mountinformation is not None:
        automountkey['automountinformation'] = mountinformation

    return automountkey


def get_automountkey_diff(client, ipa_automountkey, module_automountkey):
    return client.get_diff(ipa_data=ipa_automountkey, module_data=module_automountkey)


def ensure(module, client):
    state = module.params['state']

    module_automountkey = get_automountkey_dict(
        key=module.params.get('key'),
        mountinformation=module.params.get('mountinformation'),
    )

    args = [module.params['locationcn'], module.params['mapname'], module.params['key']]
    ipa_automountkey = client.automountkey_find(args)

    changed = False
    args = [module.params['locationcn'], module.params['mapname']]
    if state == 'present':
        if not ipa_automountkey:
            changed = True
            if not module.check_mode:
                ipa_automountkey = client.automountkey_add(args=args, item=module_automountkey)
        else:
            diff = get_automountkey_diff(client, ipa_automountkey, module_automountkey)
            if len(diff) > 0:
                changed = True
                if not module.check_mode:
                    ipa_automountkey = client.automountkey_mod(args=args, item=module_automountkey)
    else:
        if ipa_automountkey:
            changed = True
            if not module.check_mode:
                ipa_automountkey = client.automountkey_del(args=args, item=module_automountkey)

    return changed, ipa_automountkey


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(
        key=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        locationcn=dict(type='str', required=True, aliases=['location']),
        mapname=dict(type='str', required=True, aliases=['map']),
        mountinformation=dict(type='str', aliases=['information']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    client = AutoMountKeyIPAClient(
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
