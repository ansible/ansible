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
module: bigip_ssl_ocsp
short_description: Manage OCSP configurations on BIG-IP
description:
  - Manage OCSP configurations on BIG-IP.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the OCSP certificate validator.
    type: str
    required: True
  cache_error_timeout:
    description:
      - Specifies the lifetime of an error response in the cache, in seconds.
    type: int
  proxy_server_pool:
    description:
      - Specifies the proxy server pool the BIG-IP system uses to fetch the OCSP
        response.
      - This involves creating a pool with proxy-servers.
      - Use this option when either the OCSP responder cannot be reached on any of
        BIG-IP system's interfaces or one or more servers can proxy an HTTP request
        to an external server and fetch the response.
    type: str
  cache_timeout:
    description:
      - Specifies the lifetime of the OCSP response in the cache, in seconds.
    type: str
  clock_skew:
    description:
      - Specifies the tolerable absolute difference in the clocks of the responder
        and the BIG-IP system, in seconds.
    type: int
  connections_limit:
    description:
      - Specifies the maximum number of connections per second allowed for the
        OCSP certificate validator.
    type: int
  dns_resolver:
    description:
      - Specifies the internal DNS resolver the BIG-IP system uses to fetch the
        OCSP response.
      - This involves specifying one or more DNS servers in the DNS resolver
        configuration.
      - Use this option when either there is a DNS server that can do the
        name-resolution of the OCSP responders or the OCSP responder can be
        reached on one of BIG-IP system's interfaces.
    type: str
  route_domain:
    description:
      - Specifies the route domain for fetching an OCSP response using HTTP
        forward proxy.
    type: str
  hash_algorithm:
    description:
      - Specifies a hash algorithm used to sign an OCSP request.
    type: str
    choices:
      - sha256
      - sha1
  certificate:
    description:
      - Specifies a certificate used to sign an OCSP request.
    type: str
  key:
    description:
      - Specifies a key used to sign an OCSP request.
    type: str
  passphrase:
    description:
      - Specifies a passphrase used to sign an OCSP request.
    type: str
  status_age:
    description:
      - Specifies the maximum allowed lag time that the BIG-IP system accepts for
        the 'thisUpdate' time in the OCSP response.
    type: int
  strict_responder_checking:
    description:
      - Specifies whether the responder's certificate is checked for an OCSP
        signing extension.
    type: bool
  connection_timeout:
    description:
      - Specifies the time interval that the BIG-IP system waits for before
        ending the connection to the OCSP responder, in seconds.
    type: int
  trusted_responders:
    description:
      - Specifies the certificates used for validating the OCSP response
        when the responder's certificate has been omitted from the response.
    type: str
  responder_url:
    description:
      - Specifies the absolute URL that overrides the OCSP responder URL
        obtained from the certificate's AIA extensions. This should be an
        HTTP-based URL.
    type: str
  update_password:
    description:
      - C(always) will allow to update passwords if the user chooses to do so.
        C(on_create) will only set the password for newly created OCSP validators.
    type: str
    choices:
      - always
      - on_create
    default: always
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
    version_added: 2.5
  state:
    description:
      - When C(present), ensures that the resource exists.
      - When C(absent), ensures that the resource does not exist.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
notes:
  - Requires BIG-IP >= 13.x.
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a OCSP validator
  bigip_ssl_ocsp:
    name: foo
    proxy_server_pool: validators-pool
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
cache_error_timeout:
  description: The new Response Caching Error Timeout value.
  returned: changed
  type: int
  sample: 3600
cache_timeout:
  description: The new Response Caching Timeout value.
  returned: changed
  type: str
  sample: indefinite
clock_skew:
  description: The new Response Validation Clock Skew value.
  returned: changed
  type: int
  sample: 300
connections_limit:
  description: The new Concurrent Connections Limit value.
  returned: changed
  type: int
  sample: 50
dns_resolver:
  description: The new DNS Resolver value.
  returned: changed
  type: str
  sample: /Common/resolver1
route_domain:
  description: The new Route Domain value.
  returned: changed
  type: str
  sample: /Common/0
hash_algorithm:
  description: The new Request Signing Hash Algorithm value.
  returned: changed
  type: str
  sample: sha256
certificate:
  description: The new Request Signing Certificate value.
  returned: changed
  type: str
  sample: /Common/cert1
key:
  description: The new Request Signing Key value.
  returned: changed
  type: str
  sample: /Common/key1
proxy_server_pool:
  description: The new Proxy Server Pool value.
  returned: changed
  type: str
  sample: /Common/pool1
responder_url:
  description: The new Connection Responder URL value.
  returned: changed
  type: str
  sample: "http://responder.site.com"
status_age:
  description: The new Response Validation Status Age value.
  returned: changed
  type: int
  sample: 0
strict_responder_checking:
  description: The new Response Validation Strict Responder Certificate Checking value.
  returned: changed
  type: bool
  sample: yes
connection_timeout:
  description: The new Connection Timeout value.
  returned: changed
  type: int
  sample: 8
trusted_responders:
  description: The new Response Validation Trusted Responders value.
  returned: changed
  type: int
  sample: /Common/default
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.icontrol import tmos_version
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.icontrol import tmos_version


class Parameters(AnsibleF5Parameters):
    api_map = {
        'cacheErrorTimeout': 'cache_error_timeout',
        'cacheTimeout': 'cache_timeout',
        'clockSkew': 'clock_skew',
        'concurrentConnectionsLimit': 'connections_limit',
        'dnsResolver': 'dns_resolver',
        'proxyServerPool': 'proxy_server_pool',
        'responderUrl': 'responder_url',
        'routeDomain': 'route_domain',
        'signHash': 'hash_algorithm',
        'signerCert': 'certificate',
        'signerKey': 'key',
        'signerKeyPassphrase': 'passphrase',
        'statusAge': 'status_age',
        'strictRespCertCheck': 'strict_responder_checking',
        'timeout': 'connection_timeout',
        'trustedResponders': 'trusted_responders',
    }

    api_attributes = [
        'cacheErrorTimeout',
        'cacheTimeout',
        'clockSkew',
        'concurrentConnectionsLimit',
        'dnsResolver',
        'routeDomain',
        'proxyServerPool',
        'responderUrl',
        'signHash',
        'signerCert',
        'signerKey',
        'signerKeyPassphrase',
        'statusAge',
        'strictRespCertCheck',
        'timeout',
        'trustedResponders',
    ]

    returnables = [
        'cache_error_timeout',
        'cache_timeout',
        'clock_skew',
        'connections_limit',
        'dns_resolver',
        'route_domain',
        'hash_algorithm',
        'certificate',
        'key',
        'passphrase',
        'proxy_server_pool',
        'responder_url',
        'status_age',
        'strict_responder_checking',
        'connection_timeout',
        'trusted_responders',
    ]

    updatables = [
        'cache_error_timeout',
        'cache_timeout',
        'clock_skew',
        'connections_limit',
        'dns_resolver',
        'route_domain',
        'hash_algorithm',
        'certificate',
        'key',
        'passphrase',
        'proxy_server_pool',
        'responder_url',
        'status_age',
        'strict_responder_checking',
        'connection_timeout',
        'trusted_responders',
    ]

    @property
    def strict_responder_checking(self):
        return flatten_boolean(self._values['strict_responder_checking'])

    @property
    def cache_timeout(self):
        if self._values['cache_timeout'] is None:
            return None
        try:
            return int(self._values['cache_timeout'])
        except ValueError:
            return self._values['cache_timeout']


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def route_domain(self):
        if self._values['route_domain'] is None:
            return None
        result = fq_name(self.partition, self._values['route_domain'])
        return result

    @property
    def dns_resolver(self):
        if self._values['dns_resolver'] is None:
            return None
        result = fq_name(self.partition, self._values['dns_resolver'])
        return result

    @property
    def proxy_server_pool(self):
        if self._values['proxy_server_pool'] is None:
            return None
        result = fq_name(self.partition, self._values['proxy_server_pool'])
        return result

    @property
    def responder_url(self):
        if self._values['responder_url'] is None:
            return None
        if self._values['responder_url'] in ['', 'none']:
            return ''
        return self._values['responder_url']

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
    def trusted_responders(self):
        if self._values['trusted_responders'] is None:
            return None
        if self._values['trusted_responders'] in ['', 'none']:
            return ''
        result = fq_name(self.partition, self._values['trusted_responders'])
        return result


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
    def strict_responder_checking(self):
        if self._values['strict_responder_checking'] == 'yes':
            return 'enabled'
        elif self._values['strict_responder_checking'] == 'no':
            return 'disabled'


class ReportableChanges(Changes):
    @property
    def strict_responder_checking(self):
        result = flatten_boolean(self._values['strict_responder_checking'])
        return result

    @property
    def passphrase(self):
        return None


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
    def responder_url(self):
        if self.want.responder_url is None:
            return None
        if self.want.responder_url == '' and self.have.responder_url is None:
            return None
        if self.want.responder_url != self.have.responder_url:
            return self.want.responder_url

    @property
    def certificate(self):
        if self.want.certificate is None:
            return None
        if self.want.certificate == '' and self.have.certificate is None:
            return None
        if self.want.certificate != self.have.certificate:
            return self.want.certificate

    @property
    def key(self):
        if self.want.key is None:
            return None
        if self.want.key == '' and self.have.key is None:
            return None
        if self.want.key != self.have.key:
            return self.want.key

    @property
    def trusted_responders(self):
        if self.want.trusted_responders is None:
            return None
        if self.want.trusted_responders == '' and self.have.trusted_responders is None:
            return None
        if self.want.trusted_responders != self.have.trusted_responders:
            return self.want.trusted_responders


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
        tmos = tmos_version(self.client)
        if LooseVersion(tmos) < LooseVersion('13.0.0'):
            raise F5ModuleError(
                "BIG-IP v13 or greater is required to use this module."
            )
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
        uri = "https://{0}:{1}/mgmt/tm/sys/crypto/cert-validator/ocsp/{2}".format(
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

        # these two params are mutually exclusive, and so one must be zeroed
        # out so that the other can be set. This zeros the non-specified values
        # out so that the PATCH can happen
        if self.want.dns_resolver:
            self.changes.update({'proxy_server_pool': ''})
        if self.want.proxy_server_pool:
            self.changes.update({'dns_resolver': ''})

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
        uri = "https://{0}:{1}/mgmt/tm/sys/crypto/cert-validator/ocsp/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/sys/crypto/cert-validator/ocsp/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/sys/crypto/cert-validator/ocsp/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/crypto/cert-validator/ocsp/{2}".format(
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
            cache_error_timeout=dict(type='int'),
            proxy_server_pool=dict(),
            cache_timeout=dict(),
            clock_skew=dict(type='int'),
            connections_limit=dict(type='int'),
            dns_resolver=dict(),
            route_domain=dict(),
            hash_algorithm=dict(
                choices=['sha256', 'sha1']
            ),
            certificate=dict(),
            key=dict(),
            passphrase=dict(no_log=True),
            status_age=dict(type='int'),
            strict_responder_checking=dict(type='bool'),
            connection_timeout=dict(type='int'),
            trusted_responders=dict(),
            responder_url=dict(),
            update_password=dict(
                default='always',
                choices=['always', 'on_create']
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['dns_resolver', 'proxy_server_pool']
        ]
        self.required_together = [
            ['certificate', 'key']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive,
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
