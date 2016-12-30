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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: ipa_service
author: Adrian Freihofer
short_description: Manage FreeIPA services
description:
- Add, modify and delete a service within IPA server
options:
  user_certificate:
    description: service certificate (Base-64 encoded by ansible)
    required: false
  ipa_krb_authz_data:
    description:
    - Override default list of supported PAC types.
    - Use 'NONE' to disable PAC support for this service, e.g. this might be necessary for NFS services.
    required: false
  krb_principal_auth_ind:
    description:
    - Defines a whitelist for Authentication Indicators.
    - Use 'otp' to allow OTP-based 2FA authentications.
    - Use 'radius' to allow RADIUS-based 2FA authentications.
    - Other values may be used for custom configurations.
    required: false
  ipa_krb_requires_pre_auth:
    description: Pre-authentication is required for the service
    required: false
  ipa_krb_okas_delegate:
    description: Client credentials may be delegated to the service
    required: false
  ipa_krb_okto_auth_as_delegate:
    description: The service is allowed to authenticate on behalf of a client
    required: false
  force:
    description: force principal name even if not in DNS
    required: false
  no_members:
    description: Suppress processing of membership attributes.
    required: false
version_added: "2.3"
'''

EXAMPLES = '''
# Ensure service is present
- ipa_service:
    name: "cifs/samba.example.com@EXAMPLE.COM"
    force: True
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
service:
  description: Service as returned by IPA API
  returned: always
  type: dict
'''

from ansible.module_utils.ipa import IPAClient
from ansible.module_utils.ipa import ANSIBLE_INT_IPA_KEYS

class ServiceIPAClient(IPAClient):

    def __init__(self, module, host, port, protocol):
        super(ServiceIPAClient, self).__init__(module, host, port, protocol)

    def service_find(self, name):
        return self._post_json(method='service_find', name=None, item={'all': True, 'krbcanonicalname': name})

    def service_add(self, name, item):
        return self._post_json(method='service_add', name=name, item=item)

    def service_mod(self, name, item):
        return self._post_json(method='service_mod', name=name, item=item)

    def service_del(self, name):
        return self._post_json(method='service_del', name=name)


def ensure(module, client):
    state = module.params['state']
    name = module.params['name']

    # Fetch the service from FreeIPA if already existing
    ipa_service = client.service_find(name=name)

    changed = True
    if state == 'present':
        # Create a reduced copy of module.params containing only parameters forwarded to FreeIPA
        module_service = {}
        skipped_keys = ANSIBLE_INT_IPA_KEYS + ['name', 'krbcanonicalname', 'user_certificate', 'ipa_krb_authz_data',
                                               'krb_principal_auth_ind', 'ipa_krb_requires_pre_auth',
                                               'ipa_krb_okas_delegate', 'ipa_krb_okto_auth_as_delegate']
        if ipa_service:  # Remove service_add specific fields if service_mod will be called
            skipped_keys.extend(['force'])

        for key,val in module.params.items():
            if val is None:
                continue
            if key in skipped_keys:
                continue
            module_service[key] = val

        if not module.check_mode:
            if not ipa_service:  # service_add
                ipa_service = client.service_add(name, item=module_service)
            else:  # service_mod
                ipa_service = client.service_mod(name=name, item=module_service)
                if 'ipa_changed' in ipa_service:
                    changed = ipa_service['ipa_changed']

    else:  # service_del
        if ipa_service:
            if not module.check_mode:
                client.service_del(name)
            ipa_service = None
        else:
            changed = False

    return changed, ipa_service


def main():
    module = AnsibleModule(
        argument_spec=dict(
            krbcanonicalname=dict(type='str', required=True, aliases=['name']),
            user_certificate=dict(type='list', required=False, aliases=['usercertificate']),
            ipa_krb_authz_data=dict(type='list', required=False, aliases=['ipakrbauthzdata']),
            krb_principal_auth_ind=dict(type='list', required=False, aliases=['krbprincipalauthind']),
            ipa_krb_requires_pre_auth=dict(type='bool', required=False, default=True, aliases=['ipakrbrequirespreauth']),
            ipa_krb_okas_delegate=dict(type='bool', required=False, default=False, aliases=['ipakrbokasdelegate']),
            ipa_krb_okto_auth_as_delegate=dict(type='bool', required=False, default=False, aliases=['ipakrboktoauthasdelegate']),
            force=dict(type='bool', default=False),
            no_members=dict(type='bool', default=False),
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

    client = ServiceIPAClient(module=module,
                            host=module.params['ipa_host'],
                            port=module.params['ipa_port'],
                            protocol=module.params['ipa_prot'])
    try:
        client.login(username=module.params['ipa_user'],
                     password=module.params['ipa_pass'])
        changed, service = ensure(module, client)
        module.exit_json(changed=changed, service=service)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception

if __name__ == '__main__':
    main()
