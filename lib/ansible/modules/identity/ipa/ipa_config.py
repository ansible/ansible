#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Fran Fitzpatrick <francis.x.fitzpatrick@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_config
author: Fran Fitzpatrick (@fxfitz)
short_description: Manage Global FreeIPA Configuration Settings
description:
- Modify global configuration settings of a FreeIPA Server.
options:
  ipadefaultloginshell:
    description: Default shell for new users.
    aliases: ["loginshell"]
  ipadefaultemaildomain:
    description: Default e-mail domain for new users.
    aliases: ["emaildomain"]
extends_documentation_fragment: ipa.documentation
version_added: "2.7"
'''

EXAMPLES = '''
# Ensure the default login shell is bash.
- ipa_config:
    ipadefaultloginshell: /bin/bash
    ipa_host: localhost
    ipa_user: admin
    ipa_pass: supersecret

# Ensure the default e-mail domain is ansible.com.
- ipa_config:
    ipadefaultemaildomain: ansible.com
    ipa_host: localhost
    ipa_user: admin
    ipa_pass: supersecret
'''

RETURN = '''
config:
  description: Configuration as returned by IPA API.
  returned: always
  type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ipa import IPAClient, ipa_argument_spec
from ansible.module_utils._text import to_native


class ConfigIPAClient(IPAClient):
    def __init__(self, module, host, port, protocol):
        super(ConfigIPAClient, self).__init__(module, host, port, protocol)

    def config_show(self):
        return self._post_json(method='config_show', name=None)

    def config_mod(self, name, item):
        return self._post_json(method='config_mod', name=name, item=item)


def get_config_dict(ipadefaultloginshell=None, ipadefaultemaildomain=None):
    config = {}
    if ipadefaultloginshell is not None:
        config['ipadefaultloginshell'] = ipadefaultloginshell
    if ipadefaultemaildomain is not None:
        config['ipadefaultemaildomain'] = ipadefaultemaildomain

    return config


def get_config_diff(client, ipa_config, module_config):
    return client.get_diff(ipa_data=ipa_config, module_data=module_config)


def ensure(module, client):
    module_config = get_config_dict(
        ipadefaultloginshell=module.params.get('ipadefaultloginshell'),
        ipadefaultemaildomain=module.params.get('ipadefaultemaildomain'),
    )
    ipa_config = client.config_show()
    diff = get_config_diff(client, ipa_config, module_config)

    changed = False
    new_config = {}
    for module_key in diff:
        if module_config.get(module_key) != ipa_config.get(module_key, None):
            changed = True
            new_config.update({module_key: module_config.get(module_key)})

    if changed and not module.check_mode:
        client.config_mod(name=None, item=new_config)

    return changed, client.config_show()


def main():
    argument_spec = ipa_argument_spec()
    argument_spec.update(
        ipadefaultloginshell=dict(type='str', aliases=['loginshell']),
        ipadefaultemaildomain=dict(type='str', aliases=['emaildomain']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    client = ConfigIPAClient(
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
