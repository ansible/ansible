#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_ipsec_policy
short_description: Manage IPSec policies on a BIG-IP
description:
  - Manage IPSec policies on a BIG-IP.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the IPSec policy.
    type: str
    required: True
  description:
    description:
      - Description of the policy
    type: str
  protocol:
    description:
      - Specifies the IPsec protocol
      - Options include ESP (Encapsulating Security Protocol) or AH (Authentication Header).
    type: str
    choices:
      - esp
      - ah
  mode:
    description:
      - Specifies the processing mode.
      - When C(transport), specifies a mode that encapsulates only the payload (adding
        an ESP header, trailer, and authentication tag).
      - When C(tunnel), specifies a mode that includes encapsulation of the header as
        well as the payload (adding a new IP header, in addition to adding an ESP header,
        trailer, and authentication tag). If you select this option, you must also
        provide IP addresses for the local and remote endpoints of the IPsec tunnel.
      - When C(isession), specifies the use of iSession over an IPsec tunnel. To use
        this option, you must also configure the iSession endpoints with IPsec in the
        Acceleration section of the user interface.
      - When C(interface), specifies that the IPsec policy can be used in the tunnel
        profile for network interfaces.
    type: str
    choices:
      - transport
      - interface
      - isession
      - tunnel
  tunnel_local_address:
    description:
      - Specifies the local endpoint IP address of the IPsec tunnel.
      - This parameter is only valid when C(mode) is C(tunnel).
    type: str
  tunnel_remote_address:
    description:
      - Specifies the remote endpoint IP address of the IPsec tunnel.
      - This parameter is only valid when C(mode) is C(tunnel).
    type: str
  encrypt_algorithm:
    description:
      - Specifies the algorithm to use for IKE encryption.
    type: str
    choices:
      - none
      - 3des
      - aes128
      - aes192
      - aes256
      - aes-gmac256
      - aes-gmac192
      - aes-gmac128
      - aes-gcm256
      - aes-gcm192
      - aes-gcm256
      - aes-gcm128
  route_domain:
    description:
      - Specifies the route domain, when C(interface) is selected for the C(mode) setting.
    type: int
  auth_algorithm:
    description:
      - Specifies the algorithm to use for IKE authentication.
    type: str
    choices:
      - sha1
      - sha256
      - sha384
      - sha512
      - aes-gcm128
      - aes-gcm192
      - aes-gcm256
      - aes-gmac128
      - aes-gmac192
      - aes-gmac256
  ipcomp:
    description:
      - Specifies whether to use IPComp encapsulation.
      - When C(none), specifies that IPComp is disabled.
      - When C(deflate), specifies that IPComp is enabled and uses the Deflate
        compression algorithm.
    type: str
    choices:
      - none
      - "null"
      - deflate
  lifetime:
    description:
      - Specifies the length of time, in minutes, before the IKE security association
        expires.
    type: int
  kb_lifetime:
    description:
      - Specifies the length of time, in kilobytes, before the IKE security association
        expires.
    type: int
  perfect_forward_secrecy:
    description:
      - Specifies the Diffie-Hellman group to use for IKE Phase 2 negotiation.
    type: str
    choices:
      - none
      - modp768
      - modp1024
      - modp1536
      - modp2048
      - modp3072
      - modp4096
      - modp6144
      - modp8192
  ipv4_interface:
    description:
      - When C(mode) is C(interface) indicate if the IPv4 C(any) address should be used.
        By default C(BIG-IP) assumes C(any6) address for tunnel addresses when C(mode) is C(interface).
      - This option takes effect only when C(mode) is set to C(interface).
    type: bool
    version_added: 2.9
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the resource exists.
      - When C(absent), ensures the resource is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a IPSec policy
  bigip_ipsec_policy:
    name: policy1
    mode: tunnel
    tunnel_local_address: 1.1.1.1
    tunnel_remote_address: 2.2.2.
    auth_algorithm: sha1
    encrypt_algorithm: 3des
    protocol: esp
    perfect_forward_secrecy: modp1024
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
auth_algorithm:
  description: The new IKE Phase 2 Authentication Algorithm value.
  returned: changed
  type: str
  sample: sha512
encrypt_algorithm:
  description: The new IKE Phase 2 Encryption Algorithm value.
  returned: changed
  type: str
  sample: aes256
lifetime:
  description: The new IKE Phase 2 Lifetime value.
  returned: changed
  type: int
  sample: 1440
kb_lifetime:
  description: The new IKE Phase 2 KB Lifetime value.
  returned: changed
  type: int
  sample: 0
perfect_forward_secrecy:
  description: The new IKE Phase 2 Perfect Forward Secrecy value.
  returned: changed
  type: str
  sample: modp2048
tunnel_local_address:
  description: The new Tunnel Local Address value.
  returned: changed
  type: str
  sample: 1.2.2.1
tunnel_remote_address:
  description: The new Tunnel Remote Address value.
  returned: changed
  type: str
  sample: 2.1.1.2
mode:
  description: The new Mode value.
  returned: changed
  type: str
  sample: tunnel
protocol:
  description: The new IPsec Protocol value.
  returned: changed
  type: str
  sample: ah
ipcomp:
  description: The new IKE Phase 2 IPComp value.
  returned: changed
  type: str
  sample: deflate
description:
  description: The new description value.
  returned: changed
  type: str
  sample: My policy
route_domain:
  description: The new Route Domain value when in Tunnel mode.
  returned: changed
  type: int
  sample: 2
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {
        'ikePhase2AuthAlgorithm': 'auth_algorithm',
        'ikePhase2EncryptAlgorithm': 'encrypt_algorithm',
        'ikePhase2Lifetime': 'lifetime',
        'ikePhase2LifetimeKilobytes': 'kb_lifetime',
        'ikePhase2PerfectForwardSecrecy': 'perfect_forward_secrecy',
        'tunnelLocalAddress': 'tunnel_local_address',
        'tunnelRemoteAddress': 'tunnel_remote_address',
    }

    api_attributes = [
        'ikePhase2AuthAlgorithm',
        'ikePhase2EncryptAlgorithm',
        'ikePhase2Lifetime',
        'ikePhase2LifetimeKilobytes',
        'ikePhase2PerfectForwardSecrecy',
        'tunnelLocalAddress',
        'tunnelRemoteAddress',
        'mode',
        'protocol',
        'ipcomp',
        'description',
    ]

    returnables = [
        'auth_algorithm',
        'encrypt_algorithm',
        'lifetime',
        'kb_lifetime',
        'perfect_forward_secrecy',
        'tunnel_local_address',
        'tunnel_remote_address',
        'mode',
        'protocol',
        'ipcomp',
        'description',
        'route_domain',
    ]

    updatables = [
        'auth_algorithm',
        'encrypt_algorithm',
        'lifetime',
        'kb_lifetime',
        'perfect_forward_secrecy',
        'tunnel_local_address',
        'tunnel_remote_address',
        'mode',
        'protocol',
        'ipcomp',
        'description',
        'route_domain',
    ]

    @property
    def tunnel_local_address(self):
        if self._values['tunnel_local_address'] is None:
            return None
        result = self._values['tunnel_local_address'].split('%')[0]
        return result

    @property
    def tunnel_remote_address(self):
        if self._values['tunnel_remote_address'] is None:
            return None
        result = self._values['tunnel_remote_address'].split('%')[0]
        return result


class ApiParameters(Parameters):
    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def encrypt_algorithm(self):
        if self._values['encrypt_algorithm'] is None:
            return None
        elif self._values['encrypt_algorithm'] == 'null':
            return 'none'
        return self._values['encrypt_algorithm']

    @property
    def route_domain(self):
        if self._values['tunnel_local_address'] is None and self._values['tunnel_remote_address'] is None:
            return None
        elif self._values['tunnel_local_address'] is None and self._values['tunnel_remote_address'] is not None:
            if self._values['tunnel_remote_address'] == 'any6':
                result = 'any6'
            elif self._values['tunnel_remote_address'] == 'any':
                result = 'any'
            else:
                result = int(self._values['tunnel_remote_address'].split('%')[1])
        elif self._values['tunnel_remote_address'] is None and self._values['tunnel_local_address'] is not None:
            if self._values['tunnel_local_address'] == 'any6':
                result = 'any6'
            elif self._values['tunnel_local_address'] == 'any':
                result = 'any'
            else:
                result = int(self._values['tunnel_local_address'].split('%')[1])
        else:
            try:
                result = int(self._values['tunnel_local_address'].split('%')[1])
            except Exception:
                if self._values['tunnel_local_address'] in ['any6', 'any']:
                    return 0
                return None
        try:
            if result in ['any6', 'any']:
                return 0
            return int(self._values['tunnel_local_address'].split('%')[1])
        except Exception:
            return None


class ModuleParameters(Parameters):
    @property
    def ipv4_interface(self):
        result = flatten_boolean(self._values['ipv4_interface'])
        if result == 'yes':
            return True
        return False

    @property
    def description(self):
        if self._values['description'] is None:
            return None
        elif self._values['description'] in ['none', '']:
            return ''
        return self._values['description']


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    @property
    def encrypt_algorithm(self):
        if self._values['encrypt_algorithm'] is None:
            return None
        elif self._values['encrypt_algorithm'] == 'none':
            return 'null'
        return self._values['encrypt_algorithm']

    @property
    def tunnel_local_address(self):
        if self._values['tunnel_local_address'] is None:
            return None
        if self._values['route_domain'] and len(self._values['tunnel_local_address'].split('%')) == 1:
            result = '{0}%{1}'.format(self._values['tunnel_local_address'], self._values['route_domain'])
            return result
        return self._values['tunnel_local_address']

    @property
    def tunnel_remote_address(self):
        if self._values['tunnel_remote_address'] is None:
            return None
        if self._values['route_domain'] and len(self._values['tunnel_remote_address'].split('%')) == 1:
            result = '{0}%{1}'.format(self._values['tunnel_remote_address'], self._values['route_domain'])
            return result
        return self._values['tunnel_remote_address']


class ReportableChanges(Changes):
    @property
    def encrypt_algorithm(self):
        if self._values['encrypt_algorithm'] is None:
            return None
        elif self._values['encrypt_algorithm'] == 'null':
            return 'none'
        return self._values['encrypt_algorithm']


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def description(self):
        return cmp_str_with_none(self.want.description, self.have.description)

    @property
    def route_domain(self):
        if self.want.route_domain is None:
            return None
        if self.have.route_domain != self.want.route_domain:
            if self.want.route_domain == 0 and self.want.ipv4_interface:
                return dict(
                    tunnel_local_address='any',
                    tunnel_remote_address='any',
                    route_domain=self.want.route_domain,
                )
            elif self.want.route_domain == 0 and not self.want.ipv4_interface:
                return dict(
                    tunnel_local_address='any6',
                    tunnel_remote_address='any6',
                    route_domain=self.want.route_domain,
                )
            else:
                return dict(
                    tunnel_local_address='any%{0}'.format(self.want.route_domain),
                    tunnel_remote_address='any%{0}'.format(self.want.route_domain),
                    route_domain=self.want.route_domain,
                )


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/net/ipsec/ipsec-policy/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        if self.want.mode == 'interface':
            if self.want.ipv4_interface:
                self._set_any_on_interface(ip='ipv4')
            else:
                self._set_any_on_interface()
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def _set_any_on_interface(self, ip='ipv6'):
        if ip == 'ipv4':
            self.want.update({'tunnel_local_address': 'any'})
            self.want.update({'tunnel_remote_address': 'any'})
        else:
            self.want.update({'tunnel_local_address': 'any6'})
            self.want.update({'tunnel_remote_address': 'any6'})

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/net/ipsec/ipsec-policy/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/net/ipsec/ipsec-policy/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/ipsec/ipsec-policy/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/ipsec/ipsec-policy/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return ApiParameters(params=response)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            description=dict(),
            protocol=dict(
                choices=['esp', 'ah']
            ),
            mode=dict(
                choices=['transport', 'interface', 'isession', 'tunnel']
            ),
            ipv4_interface=dict(type='bool'),
            tunnel_local_address=dict(),
            tunnel_remote_address=dict(),
            encrypt_algorithm=dict(
                choices=[
                    'none', '3des', 'aes128', 'aes192', 'aes256', 'aes-gmac256',
                    'aes-gmac192', 'aes-gmac128', 'aes-gcm256', 'aes-gcm192',
                    'aes-gcm256', 'aes-gcm128'
                ]
            ),
            route_domain=dict(type='int'),
            auth_algorithm=dict(
                choices=[
                    'sha1', 'sha256', 'sha384', 'sha512', 'aes-gcm128',
                    'aes-gcm192', 'aes-gcm256', 'aes-gmac128', 'aes-gmac192',
                    'aes-gmac256',
                ]
            ),
            ipcomp=dict(
                choices=['none', 'null', 'deflate']
            ),
            lifetime=dict(type='int'),
            kb_lifetime=dict(type='int'),
            perfect_forward_secrecy=dict(
                choices=[
                    'none', 'modp768', 'modp1024', 'modp1536', 'modp2048', 'modp3072',
                    'modp4096', 'modp6144', 'modp8192'
                ]
            ),
            state=dict(default='present', choices=['absent', 'present']),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['mode', 'tunnel', ['tunnel_local_address', 'tunnel_remote_address']],
            ['mode', 'interface', ['route_domain']]
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
