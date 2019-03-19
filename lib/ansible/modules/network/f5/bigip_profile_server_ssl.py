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
module: bigip_profile_server_ssl
short_description: Manages server SSL profiles on a BIG-IP
description:
  - Manages server SSL profiles on a BIG-IP.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the profile.
    type: str
    required: True
  parent:
    description:
      - The parent template of this monitor template. Once this value has
        been set, it cannot be changed.
    type: str
    default: /Common/serverssl
  ciphers:
    description:
      - Specifies the list of ciphers that the system supports. When creating a new
        profile, the default cipher list is provided by the parent profile.
    type: str
  secure_renegotiation:
    description:
      - Specifies the method of secure renegotiations for SSL connections. When
        creating a new profile, the setting is provided by the parent profile.
      - When C(request) is set the system request secure renegotation of SSL
        connections.
      - C(require) is a default setting and when set the system permits initial SSL
        handshakes from clients but terminates renegotiations from unpatched clients.
      - The C(require-strict) setting the system requires strict renegotiation of SSL
        connections. In this mode the system refuses connections to insecure servers,
        and terminates existing SSL connections to insecure servers.
    type: str
    choices:
      - require
      - require-strict
      - request
  server_name:
    description:
      - Specifies the fully qualified DNS hostname of the server used in Server Name
        Indication communications. When creating a new profile, the setting is provided
        by the parent profile.
    type: str
  sni_default:
    description:
      - Indicates that the system uses this profile as the default SSL profile when there
        is no match to the server name, or when the client provides no SNI extension support.
      - When creating a new profile, the setting is provided by the parent profile.
      - There can be only one SSL profile with this setting enabled.
    type: bool
  sni_require:
    description:
      - Requires that the network peers also provide SNI support, setting only takes
        effect when C(sni_default) is C(yes).
      - When creating a new profile, the setting is provided by the parent profile.
    type: bool
  server_certificate:
    description:
      - Specifies the way the system handles server certificates.
      - When C(ignore), specifies that the system ignores certificates from server systems.
      - When C(require), specifies that the system requires a server to present a valid
        certificate.
    type: str
    choices:
      - ignore
      - require
  certificate:
    description:
      - Specifies the name of the certificate that the system uses for server-side SSL
        processing.
    type: str
  key:
    description:
      - Specifies the file name of the SSL key.
    type: str
  chain:
    description:
      - Specifies the certificates-key chain to associate with the SSL profile.
    type: str
  passphrase:
    description:
      - Specifies a passphrase used to encrypt the key.
    type: str
  update_password:
    description:
      - C(always) will allow to update passwords if the user chooses to do so.
        C(on_create) will only set the password for newly created profiles.
    type: str
    choices:
      - always
      - on_create
    default: always
  ocsp_profile:
    description:
      - Specifies the name of the OCSP profile for purpose of validating status
        of server certificate.
    type: str
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the profile exists.
      - When C(absent), ensures the profile is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a new server SSL profile
  bigip_profile_server_ssl:
    name: foo
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
ciphers:
  description: The ciphers applied to the profile.
  returned: changed
  type: str
  sample: "!SSLv3:!SSLv2:ECDHE+AES-GCM+SHA256:ECDHE-RSA-AES128-CBC-SHA"
secure_renegotiation:
  description: The method of secure SSL renegotiation.
  returned: changed
  type: str
  sample: request
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import transform_name
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import transform_name


class Parameters(AnsibleF5Parameters):
    api_map = {
        'cert': 'certificate',
        'ocsp': 'ocsp_profile',
        'defaultsFrom': 'parent',
        'secureRenegotiation': 'secure_renegotiation',
        'sniDefault': 'sni_default',
        'sniRequire': 'sni_require',
        'serverName': 'server_name',
        'peerCertMode': 'server_certificate',
    }

    api_attributes = [
        'cert',
        'chain',
        'ciphers',
        'defaultsFrom',
        'key',
        'ocsp',
        'secureRenegotiation',
        'sniDefault',
        'sniRequire',
        'serverName',
        'peerCertMode',
    ]

    returnables = [
        'certificate',
        'chain',
        'ciphers',
        'key',
        'ocsp_profile',
        'secure_renegotiation',
        'parent',
        'sni_default',
        'sni_require',
        'server_name',
        'server_certificate',
    ]

    updatables = [
        'certificate',
        'chain',
        'ciphers',
        'key',
        'ocsp_profile',
        'secure_renegotiation',
        'sni_default',
        'sni_require',
        'server_name',
        'server_certificate',
    ]

    @property
    def sni_default(self):
        return flatten_boolean(self._values['sni_default'])

    @property
    def certificate(self):
        if self._values['certificate'] is None:
            return None
        if self._values['certificate'] in ['', 'none']:
            return ''
        result = fq_name(self.partition, self._values['certificate'])
        return result

    @property
    def key(self):
        if self._values['key'] is None:
            return None
        if self._values['key'] in ['', 'none']:
            return ''
        result = fq_name(self.partition, self._values['key'])
        return result

    @property
    def chain(self):
        if self._values['chain'] is None:
            return None
        if self._values['chain'] in ['', 'none']:
            return ''
        result = fq_name(self.partition, self._values['chain'])
        return result

    @property
    def ocsp_profile(self):
        if self._values['ocsp_profile'] is None:
            return None
        if self._values['ocsp_profile'] in ['', 'none']:
            return ''
        result = fq_name(self.partition, self._values['ocsp_profile'])
        return result


class ApiParameters(Parameters):
    @property
    def sni_require(self):
        return flatten_boolean(self._values['sni_require'])

    @property
    def server_name(self):
        if self._values['server_name'] in [None, 'none']:
            return None
        return self._values['server_name']


class ModuleParameters(Parameters):
    @property
    def server_name(self):
        if self._values['server_name'] is None:
            return None
        if self._values['server_name'] in ['', 'none']:
            return ''
        return self._values['server_name']

    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        if self._values['parent'] == 'serverssl':
            return '/Common/serverssl'
        result = fq_name(self.partition, self._values['parent'])
        return result

    @property
    def sni_require(self):
        require = flatten_boolean(self._values['sni_require'])
        default = self.sni_default
        if require is None:
            return None
        if default in [None, 'no']:
            if require == 'yes':
                raise F5ModuleError(
                    "Cannot set 'sni_require' to {0} if 'sni_default' is set as {1}".format(require, default))
        return require


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
    def sni_default(self):
        if self._values['sni_default'] is None:
            return None
        elif self._values['sni_default'] == 'yes':
            return 'true'
        else:
            return 'false'

    @property
    def sni_require(self):
        if self._values['sni_require'] is None:
            return None
        elif self._values['sni_require'] == 'yes':
            return 'true'
        else:
            return 'false'


class ReportableChanges(Changes):
    @property
    def sni_default(self):
        result = flatten_boolean(self._values['sni_default'])
        return result

    @property
    def sni_require(self):
        result = flatten_boolean(self._values['sni_require'])
        return result


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

    @property
    def parent(self):
        if self.want.parent != self.have.parent:
            raise F5ModuleError(
                "The parent profile cannot be changed"
            )

    @property
    def sni_require(self):
        if self.want.sni_require is None:
            return None
        if self.want.sni_require == 'no':
            if self.have.sni_default == 'yes' and self.want.sni_default is None:
                raise F5ModuleError(
                    "Cannot set 'sni_require' to {0} if 'sni_default' is {1}".format(
                        self.want.sni_require, self.have.sni_default
                    )
                )
        if self.want.sni_require != self.have.sni_require:
            return self.want.sni_require

    @property
    def server_name(self):
        if self.want.server_name is None:
            return None
        if self.want.server_name == '' and self.have.server_name is None:
            return None
        if self.want.server_name != self.have.server_name:
            return self.want.server_name

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1


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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/server-ssl/{2}".format(
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

        if self.want.update_password == 'always':
            self.want.update({'passphrase': self.want.passphrase})
        else:
            if self.want.passphrase:
                del self.want._values['passphrase']

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
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/server-ssl/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/server-ssl/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/server-ssl/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/server-ssl/{2}".format(
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
            certificate=dict(),
            chain=dict(),
            key=dict(),
            passphrase=dict(no_log=True),
            parent=dict(default='/Common/serverssl'),
            ciphers=dict(),
            secure_renegotiation=dict(
                choices=['require', 'require-strict', 'request']
            ),
            server_certificate=dict(
                choices=['ignore', 'require']
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            update_password=dict(
                default='always',
                choices=['always', 'on_create']
            ),
            sni_default=dict(type='bool'),
            sni_require=dict(type='bool'),
            server_name=dict(),
            ocsp_profile=dict(),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_together = [
            ['certificate', 'key']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_together=spec.required_together,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
