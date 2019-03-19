#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_profile_client_ssl
short_description: Manages client SSL profiles on a BIG-IP
description:
  - Manages client SSL profiles on a BIG-IP.
version_added: 2.5
options:
  name:
    description:
      - Specifies the name of the profile.
    type: str
    required: True
  parent:
    description:
      - The parent template of this monitor template. Once this value has
        been set, it cannot be changed. By default, this value is the C(clientssl)
        parent on the C(Common) partition.
    type: str
    default: /Common/clientssl
  ciphers:
    description:
      - Specifies the list of ciphers that the system supports. When creating a new
        profile, the default cipher list is provided by the parent profile.
    type: str
  cert_key_chain:
    description:
      - One or more certificates and keys to associate with the SSL profile. This
        option is always a list. The keys in the list dictate the details of the
        client/key/chain combination. Note that BIG-IPs can only have one of each
        type of each certificate/key type. This means that you can only have one
        RSA, one DSA, and one ECDSA per profile. If you attempt to assign two
        RSA, DSA, or ECDSA certificate/key combo, the device will reject this.
      - This list is a complex list that specifies a number of keys.
    suboptions:
      cert:
        description:
          - Specifies a cert name for use.
        type: str
        required: True
      key:
        description:
          - Contains a key name.
        type: str
        required: True
      chain:
        description:
          - Contains a certificate chain that is relevant to the certificate and key
            mentioned earlier.
          - This key is optional.
        type: str
      passphrase:
        description:
          - Contains the passphrase of the key file, should it require one.
          - Passphrases are encrypted on the remote BIG-IP device. Therefore, there is no way
            to compare them when updating a client SSL profile. Due to this, if you specify a
            passphrase, this module will always register a C(changed) event.
        type: str
    type: list
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
    version_added: 2.5
  options:
    description:
      - Options that the system uses for SSL processing in the form of a list. When
        creating a new profile, the list is provided by the parent profile.
      - When a C('') or C(none) value is provided all options for SSL processing are disabled.
    type: list
    choices:
      - netscape-reuse-cipher-change-bug
      - microsoft-big-sslv3-buffer
      - msie-sslv2-rsa-padding
      - ssleay-080-client-dh-bug
      - tls-d5-bug
      - tls-block-padding-bug
      - dont-insert-empty-fragments
      - no-ssl
      - no-dtls
      - no-session-resumption-on-renegotiation
      - no-tlsv1.1
      - no-tlsv1.2
      - single-dh-use
      - ephemeral-rsa
      - cipher-server-preference
      - tls-rollback-bug
      - no-sslv2
      - no-sslv3
      - no-tls
      - no-tlsv1
      - pkcs1-check-1
      - pkcs1-check-2
      - netscape-ca-dn-bug
      - netscape-demo-cipher-change-bug
      - "none"
    version_added: 2.7
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
    version_added: 2.7
  allow_non_ssl:
    description:
      - Enables or disables acceptance of non-SSL connections.
      - When creating a new profile, the setting is provided by the parent profile.
    type: bool
    version_added: 2.7
  server_name:
    description:
      - Specifies the fully qualified DNS hostname of the server used in Server Name Indication communications.
        When creating a new profile, the setting is provided by the parent profile.
      - The server name can also be a wildcard string containing the asterisk C(*) character.
    version_added: 2.8
  sni_default:
    description:
      - Indicates that the system uses this profile as the default SSL profile when there is no match to the
        server name, or when the client provides no SNI extension support.
      - When creating a new profile, the setting is provided by the parent profile.
      - There can be only one SSL profile with this setting enabled.
    type: bool
    version_added: 2.8
  sni_require:
    description:
      - Requires that the network peers also provide SNI support, this setting only takes effect when C(sni_default) is
        set to C(true).
      - When creating a new profile, the setting is provided by the parent profile.
    type: bool
    version_added: 2.8
  strict_resume:
    description:
      - Enables or disables the resumption of SSL sessions after an unclean shutdown.
      - When creating a new profile, the setting is provided by the parent profile.
    type: bool
    version_added: 2.8
  client_certificate:
    description:
      - Specifies the way the system handles client certificates.
      - When C(ignore), specifies that the system ignores certificates from client
        systems.
      - When C(require), specifies that the system requires a client to present a
        valid certificate.
      - When C(request), specifies that the system requests a valid certificate from a
        client but always authenticate the client.
    type: str
    choices:
      - ignore
      - require
      - request
    version_added: 2.8
  client_auth_frequency:
    description:
      - Specifies the frequency of client authentication for an SSL session.
      - When C(once), specifies that the system authenticates the client once for an
        SSL session.
      - When C(always), specifies that the system authenticates the client once for an
        SSL session and also upon reuse of that session.
    type: str
    choices:
      - once
      - always
    version_added: 2.8
  renegotiation:
    description:
      - Enables or disables SSL renegotiation.
      - When creating a new profile, the setting is provided by the parent profile.
    type: bool
    version_added: 2.8
  retain_certificate:
    description:
      - When C(yes), client certificate is retained in SSL session.
    type: bool
    version_added: 2.8
  cert_auth_depth:
    description:
      - Specifies the maximum number of certificates to be traversed in a client
        certificate chain.
    type: int
    version_added: 2.8
  trusted_cert_authority:
    description:
      - Specifies a client CA that the system trusts.
    type: str
    version_added: 2.8
  advertised_cert_authority:
    description:
      - Specifies that the CAs that the system advertises to clients is being trusted
        by the profile.
    type: str
    version_added: 2.8
  client_auth_crl:
    description:
      - Specifies the name of a file containing a list of revoked client certificates.
    type: str
    version_added: 2.8
  allow_expired_crl:
    description:
      - Instructs the system to use the specified CRL file even if it has expired.
    type: bool
    version_added: 2.8
  state:
    description:
      - When C(present), ensures that the profile exists.
      - When C(absent), ensures the profile is removed.
    type: str
    choices:
      - present
      - absent
    default: present
    version_added: 2.5
notes:
  - Requires BIG-IP software version >= 12
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create client SSL profile
  bigip_profile_client_ssl:
    state: present
    name: my_profile
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Create client SSL profile with specific ciphers
  bigip_profile_client_ssl:
    state: present
    name: my_profile
    ciphers: "!SSLv3:!SSLv2:ECDHE+AES-GCM+SHA256:ECDHE-RSA-AES128-CBC-SHA"
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Create client SSL profile with specific SSL options
  bigip_profile_client_ssl:
    state: present
    name: my_profile
    options:
      - no-sslv2
      - no-sslv3
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Create client SSL profile require secure renegotiation
  bigip_profile_client_ssl:
    state: present
    name: my_profile
    secure_renegotiation: request
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Create a client SSL profile with a cert/key/chain setting
  bigip_profile_client_ssl:
    state: present
    name: my_profile
    cert_key_chain:
      - cert: bigip_ssl_cert1
        key: bigip_ssl_key1
        chain: bigip_ssl_cert1
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
ciphers:
  description: The ciphers applied to the profile.
  returned: changed
  type: str
  sample: "!SSLv3:!SSLv2:ECDHE+AES-GCM+SHA256:ECDHE-RSA-AES128-CBC-SHA"
options:
  description: The list of options for SSL processing.
  returned: changed
  type: list
  sample: ['no-sslv2', 'no-sslv3']
secure_renegotiation:
  description: The method of secure SSL renegotiation.
  returned: changed
  type: str
  sample: request
allow_non_ssl:
  description: Acceptance of non-SSL connections.
  returned: changed
  type: bool
  sample: yes
strict_resume:
  description: Resumption of SSL sessions after an unclean shutdown.
  returned: changed
  type: bool
  sample: yes
renegotiation:
  description: Renegotiation of SSL sessions.
  returned: changed
  type: bool
  sample: yes
'''

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import iteritems

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import is_empty_list
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import is_empty_list


class Parameters(AnsibleF5Parameters):
    api_map = {
        'certKeyChain': 'cert_key_chain',
        'defaultsFrom': 'parent',
        'allowNonSsl': 'allow_non_ssl',
        'secureRenegotiation': 'secure_renegotiation',
        'tmOptions': 'options',
        'sniDefault': 'sni_default',
        'sniRequire': 'sni_require',
        'serverName': 'server_name',
        'peerCertMode': 'client_certificate',
        'authenticate': 'client_auth_frequency',
        'retainCertificate': 'retain_certificate',
        'authenticateDepth': 'cert_auth_depth',
        'caFile': 'trusted_cert_authority',
        'clientCertCa': 'advertised_cert_authority',
        'crlFile': 'client_auth_crl',
        'allowExpiredCrl': 'allow_expired_crl',
        'strictResume': 'strict_resume',
        'renegotiation': 'renegotiation',
    }

    api_attributes = [
        'ciphers',
        'certKeyChain',
        'defaultsFrom',
        'tmOptions',
        'secureRenegotiation',
        'allowNonSsl',
        'sniDefault',
        'sniRequire',
        'serverName',
        'peerCertMode',
        'authenticate',
        'retainCertificate',
        'authenticateDepth',
        'caFile',
        'clientCertCa',
        'crlFile',
        'allowExpiredCrl',
        'strictResume',
        'renegotiation',
    ]

    returnables = [
        'ciphers',
        'allow_non_ssl',
        'options',
        'secure_renegotiation',
        'cert_key_chain',
        'parent',
        'sni_default',
        'sni_require',
        'server_name',
        'client_certificate',
        'client_auth_frequency',
        'retain_certificate',
        'cert_auth_depth',
        'trusted_cert_authority',
        'advertised_cert_authority',
        'client_auth_crl',
        'allow_expired_crl',
        'strict_resume',
        'renegotiation',
    ]

    updatables = [
        'ciphers',
        'cert_key_chain',
        'allow_non_ssl',
        'options',
        'secure_renegotiation',
        'sni_default',
        'sni_require',
        'server_name',
        'client_certificate',
        'client_auth_frequency',
        'retain_certificate',
        'cert_auth_depth',
        'trusted_cert_authority',
        'advertised_cert_authority',
        'client_auth_crl',
        'allow_expired_crl',
        'strict_resume',
        'renegotiation',
    ]

    @property
    def retain_certificate(self):
        return flatten_boolean(self._values['retain_certificate'])

    @property
    def allow_expired_crl(self):
        return flatten_boolean(self._values['allow_expired_crl'])


class ModuleParameters(Parameters):
    def _key_filename(self, name):
        if name.endswith('.key'):
            return name
        else:
            return name + '.key'

    def _cert_filename(self, name):
        if name.endswith('.crt'):
            return name
        else:
            return name + '.crt'

    def _get_chain_value(self, item):
        if 'chain' not in item or item['chain'] == 'none':
            result = 'none'
        else:
            result = self._cert_filename(fq_name(self.partition, item['chain']))
        return result

    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        if self._values['parent'] == 'clientssl':
            return '/Common/clientssl'
        result = fq_name(self.partition, self._values['parent'])
        return result

    @property
    def cert_key_chain(self):
        if self._values['cert_key_chain'] is None:
            return None
        result = []
        for item in self._values['cert_key_chain']:
            if 'key' in item and 'cert' not in item:
                raise F5ModuleError(
                    "When providing a 'key', you must also provide a 'cert'"
                )
            if 'cert' in item and 'key' not in item:
                raise F5ModuleError(
                    "When providing a 'cert', you must also provide a 'key'"
                )
            key = self._key_filename(item['key'])
            cert = self._cert_filename(item['cert'])
            chain = self._get_chain_value(item)
            name = os.path.basename(cert)
            filename, ex = os.path.splitext(name)
            tmp = {
                'name': filename,
                'cert': fq_name(self.partition, cert),
                'key': fq_name(self.partition, key),
                'chain': chain
            }
            if 'passphrase' in item:
                tmp['passphrase'] = item['passphrase']
            result.append(tmp)
        result = sorted(result, key=lambda x: x['name'])
        return result

    @property
    def allow_non_ssl(self):
        result = flatten_boolean(self._values['allow_non_ssl'])
        if result is None:
            return None
        if result == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def strict_resume(self):
        result = flatten_boolean(self._values['strict_resume'])
        if result is None:
            return None
        if result == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def renegotiation(self):
        result = flatten_boolean(self._values['renegotiation'])
        if result is None:
            return None
        if result == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def options(self):
        options = self._values['options']
        if options is None:
            return None
        if is_empty_list(options):
            return []
        return options

    @property
    def sni_require(self):
        require = flatten_boolean(self._values['sni_require'])
        default = self.sni_default
        if require is None:
            return None
        if default in [None, False]:
            if require == 'yes':
                raise F5ModuleError(
                    "Cannot set 'sni_require' to {0} if 'sni_default' is set as {1}".format(require, default))
        if require == 'yes':
            return True
        else:
            return False

    @property
    def trusted_cert_authority(self):
        if self._values['trusted_cert_authority'] is None:
            return None
        if self._values['trusted_cert_authority'] in ['', 'none']:
            return ''
        result = fq_name(self.partition, self._values['trusted_cert_authority'])
        return result

    @property
    def advertised_cert_authority(self):
        if self._values['advertised_cert_authority'] is None:
            return None
        if self._values['advertised_cert_authority'] in ['', 'none']:
            return ''
        result = fq_name(self.partition, self._values['advertised_cert_authority'])
        return result

    @property
    def client_auth_crl(self):
        if self._values['client_auth_crl'] is None:
            return None
        if self._values['client_auth_crl'] in ['', 'none']:
            return ''
        result = fq_name(self.partition, self._values['client_auth_crl'])
        return result


class ApiParameters(Parameters):
    @property
    def cert_key_chain(self):
        if self._values['cert_key_chain'] is None:
            return None
        result = []
        for item in self._values['cert_key_chain']:
            tmp = dict(
                name=item['name'],
            )
            for x in ['cert', 'key', 'chain', 'passphrase']:
                if x in item:
                    tmp[x] = item[x]
                if 'chain' not in item:
                    tmp['chain'] = 'none'
            result.append(tmp)
        result = sorted(result, key=lambda y: y['name'])
        return result

    @property
    def sni_default(self):
        result = self._values['sni_default']
        if result is None:
            return None
        if result == 'true':
            return True
        else:
            return False

    @property
    def sni_require(self):
        result = self._values['sni_require']
        if result is None:
            return None
        if result == 'true':
            return True
        else:
            return False

    @property
    def trusted_cert_authority(self):
        if self._values['trusted_cert_authority'] in [None, 'none']:
            return None
        return self._values['trusted_cert_authority']

    @property
    def advertised_cert_authority(self):
        if self._values['advertised_cert_authority'] in [None, 'none']:
            return None
        return self._values['advertised_cert_authority']

    @property
    def client_auth_crl(self):
        if self._values['client_auth_crl'] in [None, 'none']:
            return None
        return self._values['client_auth_crl']


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
    def retain_certificate(self):
        if self._values['retain_certificate'] is None:
            return None
        elif self._values['retain_certificate'] == 'yes':
            return 'true'
        return 'false'

    @property
    def allow_expired_crl(self):
        if self._values['allow_expired_crl'] is None:
            return None
        elif self._values['allow_expired_crl'] == 'yes':
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def allow_non_ssl(self):
        if self._values['allow_non_ssl'] is None:
            return None
        elif self._values['allow_non_ssl'] == 'enabled':
            return 'yes'
        return 'no'

    @property
    def strict_resume(self):
        if self._values['strict_resume'] is None:
            return None
        elif self._values['strict_resume'] == 'enabled':
            return 'yes'
        return 'no'

    @property
    def retain_certificate(self):
        return flatten_boolean(self._values['retain_certificate'])

    @property
    def allow_expired_crl(self):
        return flatten_boolean(self._values['allow_expired_crl'])


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            result = self.__default(param)
            return result

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    def to_tuple(self, items):
        result = []
        for x in items:
            tmp = [(str(k), str(v)) for k, v in iteritems(x)]
            result += tmp
        return result

    def _diff_complex_items(self, want, have):
        if want == [] and have is None:
            return None
        if want is None:
            return None
        w = self.to_tuple(want)
        h = self.to_tuple(have)
        if set(w).issubset(set(h)):
            return None
        else:
            return want

    @property
    def parent(self):
        if self.want.parent != self.have.parent:
            raise F5ModuleError(
                "The parent profile cannot be changed"
            )

    @property
    def cert_key_chain(self):
        result = self._diff_complex_items(self.want.cert_key_chain, self.have.cert_key_chain)
        return result

    @property
    def options(self):
        if self.want.options is None:
            return None
        if not self.want.options:
            if self.have.options is None:
                return None
            if not self.have.options:
                return None
            if self.have.options is not None:
                return self.want.options
        if self.have.options is None:
            return self.want.options
        if set(self.want.options) != set(self.have.options):
            return self.want.options

    @property
    def sni_require(self):
        if self.want.sni_require is None:
            return None
        if self.want.sni_require is False:
            if self.have.sni_default is True and self.want.sni_default is None:
                raise F5ModuleError(
                    "Cannot set 'sni_require' to {0} if 'sni_default' is {1}".format(
                        self.want.sni_require, self.have.sni_default)
                )
        if self.want.sni_require == self.have.sni_require:
            return None
        return self.want.sni_require

    @property
    def trusted_cert_authority(self):
        if self.want.trusted_cert_authority is None:
            return None
        if self.want.trusted_cert_authority == '' and self.have.trusted_cert_authority is None:
            return None
        if self.want.trusted_cert_authority != self.have.trusted_cert_authority:
            return self.want.trusted_cert_authority

    @property
    def advertised_cert_authority(self):
        if self.want.advertised_cert_authority is None:
            return None
        if self.want.advertised_cert_authority == '' and self.have.advertised_cert_authority is None:
            return None
        if self.want.advertised_cert_authority != self.have.advertised_cert_authority:
            return self.want.advertised_cert_authority

    @property
    def client_auth_crl(self):
        if self.want.client_auth_crl is None:
            return None
        if self.want.client_auth_crl == '' and self.have.client_auth_crl is None:
            return None
        if self.want.client_auth_crl != self.have.client_auth_crl:
            return self.want.client_auth_crl


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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/client-ssl/{2}".format(
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
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/client-ssl/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/client-ssl/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/client-ssl/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/client-ssl/{2}".format(
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
            parent=dict(default='/Common/clientssl'),
            ciphers=dict(),
            allow_non_ssl=dict(type='bool'),
            secure_renegotiation=dict(
                choices=['require', 'require-strict', 'request']
            ),
            options=dict(
                type='list',
                choices=[
                    'netscape-reuse-cipher-change-bug',
                    'microsoft-big-sslv3-buffer',
                    'msie-sslv2-rsa-padding',
                    'ssleay-080-client-dh-bug',
                    'tls-d5-bug',
                    'tls-block-padding-bug',
                    'dont-insert-empty-fragments',
                    'no-ssl',
                    'no-dtls',
                    'no-session-resumption-on-renegotiation',
                    'no-tlsv1.1',
                    'no-tlsv1.2',
                    'single-dh-use',
                    'ephemeral-rsa',
                    'cipher-server-preference',
                    'tls-rollback-bug',
                    'no-sslv2',
                    'no-sslv3',
                    'no-tls',
                    'no-tlsv1',
                    'pkcs1-check-1',
                    'pkcs1-check-2',
                    'netscape-ca-dn-bug',
                    'netscape-demo-cipher-change-bug',
                    'none',
                ]
            ),
            cert_key_chain=dict(
                type='list',
                options=dict(
                    cert=dict(required=True),
                    key=dict(required=True),
                    chain=dict(),
                    passphrase=dict()
                )
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            sni_default=dict(type='bool'),
            sni_require=dict(type='bool'),
            server_name=dict(),
            client_certificate=dict(
                choices=['require', 'ignore', 'request']
            ),
            client_auth_frequency=dict(
                choices=['once', 'always']
            ),
            cert_auth_depth=dict(type='int'),
            retain_certificate=dict(type='bool'),
            trusted_cert_authority=dict(),
            advertised_cert_authority=dict(),
            client_auth_crl=dict(),
            allow_expired_crl=dict(type='bool'),
            strict_resume=dict(type='bool'),
            renegotiation=dict(type='bool'),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
