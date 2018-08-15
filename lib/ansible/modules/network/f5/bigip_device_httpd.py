#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_device_httpd
short_description: Manage HTTPD related settings on BIG-IP
description:
  - Manages HTTPD related settings on the BIG-IP. These settings are interesting
    to change when you want to set GUI timeouts and other TMUI related settings.
version_added: 2.5
options:
  allow:
    description:
      - Specifies, if you have enabled HTTPD access, the IP address or address
        range for other systems that can communicate with this system.
      - To specify all addresses, use the value C(all).
      - IP address can be specified, such as 172.27.1.10.
      - IP rangees can be specified, such as 172.27.*.* or 172.27.0.0/255.255.0.0.
  auth_name:
    description:
      - Sets the BIG-IP authentication realm name.
  auth_pam_idle_timeout:
    description:
      - Sets the GUI timeout for automatic logout, in seconds.
  auth_pam_validate_ip:
    description:
      - Sets the authPamValidateIp setting.
    type: bool
  auth_pam_dashboard_timeout:
    description:
      - Sets whether or not the BIG-IP dashboard will timeout.
    type: bool
  fast_cgi_timeout:
    description:
      - Sets the timeout of FastCGI.
  hostname_lookup:
    description:
      - Sets whether or not to display the hostname, if possible.
    type: bool
  log_level:
    description:
      - Sets the minimum httpd log level.
    choices: ['alert', 'crit', 'debug', 'emerg', 'error', 'info', 'notice', 'warn']
  max_clients:
    description:
      - Sets the maximum number of clients that can connect to the GUI at once.
  redirect_http_to_https:
    description:
      - Whether or not to redirect http requests to the GUI to https.
    type: bool
  ssl_port:
    description:
      - The HTTPS port to listen on.
  ssl_cipher_suite:
    description:
      - Specifies the ciphers that the system uses.
      - The values in the suite are separated by colons (:).
      - Can be specified in either a string or list form. The list form is the
        recommended way to provide the cipher suite. See examples for usage.
      - Use the value C(default) to set the cipher suite to the system default.
        This value is equivalent to specifying a list of C(ECDHE-RSA-AES128-GCM-SHA256,
        ECDHE-RSA-AES256-GCM-SHA384,ECDHE-RSA-AES128-SHA,ECDHE-RSA-AES256-SHA,
        ECDHE-RSA-AES128-SHA256,ECDHE-RSA-AES256-SHA384,ECDHE-ECDSA-AES128-GCM-SHA256,
        ECDHE-ECDSA-AES256-GCM-SHA384,ECDHE-ECDSA-AES128-SHA,ECDHE-ECDSA-AES256-SHA,
        ECDHE-ECDSA-AES128-SHA256,ECDHE-ECDSA-AES256-SHA384,AES128-GCM-SHA256,
        AES256-GCM-SHA384,AES128-SHA,AES256-SHA,AES128-SHA256,AES256-SHA256,
        ECDHE-RSA-DES-CBC3-SHA,ECDHE-ECDSA-DES-CBC3-SHA,DES-CBC3-SHA).
    version_added: 2.6
  ssl_protocols:
    description:
      - The list of SSL protocols to accept on the management console.
      - A space-separated list of tokens in the format accepted by the Apache
        mod_ssl SSLProtocol directive.
      - Can be specified in either a string or list form. The list form is the
        recommended way to provide the cipher suite. See examples for usage.
      - Use the value C(default) to set the SSL protocols to the system default.
        This value is equivalent to specifying a list of C(all,-SSLv2,-SSLv3).
    version_added: 2.6
notes:
  - Requires the requests Python package on the host. This is as easy as
    C(pip install requests).
requirements:
  - requests
extends_documentation_fragment: f5
author:
  - Joe Reifel (@JoeReifel)
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Set the BIG-IP authentication realm name
  bigip_device_httpd:
    auth_name: BIG-IP
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost

- name: Set the auth pam timeout to 3600 seconds
  bigip_device_httpd:
    auth_pam_idle_timeout: 1200
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost

- name: Set the validate IP settings
  bigip_device_httpd:
    auth_pam_validate_ip: on
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost

- name: Set SSL cipher suite by list
  bigip_device_httpd:
    password: secret
    server: lb.mydomain.com
    user: admin
    ssl_cipher_suite:
      - ECDHE-RSA-AES128-GCM-SHA256
      - ECDHE-RSA-AES256-GCM-SHA384
      - ECDHE-RSA-AES128-SHA
      - AES256-SHA256
  delegate_to: localhost

- name: Set SSL cipher suite by string
  bigip_device_httpd:
    password: secret
    server: lb.mydomain.com
    user: admin
    ssl_cipher_suite: ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA:AES256-SHA256
  delegate_to: localhost

- name: Set SSL protocols by list
  bigip_device_httpd:
    password: secret
    server: lb.mydomain.com
    user: admin
    ssl_protocols:
      - all
      - -SSLv2
      - -SSLv3
  delegate_to: localhost

- name: Set SSL protocols by string
  bigip_device_httpd:
    password: secret
    server: lb.mydomain.com
    user: admin
    ssl_cipher_suite: all -SSLv2 -SSLv3
  delegate_to: localhost
'''

RETURN = r'''
auth_pam_idle_timeout:
  description: The new number of seconds for GUI timeout.
  returned: changed
  type: string
  sample: 1200
auth_name:
  description: The new authentication realm name.
  returned: changed
  type: string
  sample: 'foo'
auth_pam_validate_ip:
  description: The new authPamValidateIp setting.
  returned: changed
  type: bool
  sample: on
auth_pam_dashboard_timeout:
  description: Whether or not the BIG-IP dashboard will timeout.
  returned: changed
  type: bool
  sample: off
fast_cgi_timeout:
  description: The new timeout of FastCGI.
  returned: changed
  type: int
  sample: 500
hostname_lookup:
  description: Whether or not to display the hostname, if possible.
  returned: changed
  type: bool
  sample: on
log_level:
  description: The new minimum httpd log level.
  returned: changed
  type: string
  sample: crit
max_clients:
  description: The new maximum number of clients that can connect to the GUI at once.
  returned: changed
  type: int
  sample: 20
redirect_http_to_https:
  description: Whether or not to redirect http requests to the GUI to https.
  returned: changed
  type: bool
  sample: on
ssl_port:
  description: The new HTTPS port to listen on.
  returned: changed
  type: int
  sample: 10443
ssl_cipher_suite:
  description: The new ciphers that the system uses.
  returned: changed
  type: string
  sample: ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA
ssl_protocols:
  description: The new list of SSL protocols to accept on the management console.
  returned: changed
  type: string
  sample: all -SSLv2 -SSLv3
'''

import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False

try:
    from requests.exceptions import ConnectionError
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'authPamIdleTimeout': 'auth_pam_idle_timeout',
        'authPamValidateIp': 'auth_pam_validate_ip',
        'authName': 'auth_name',
        'authPamDashboardTimeout': 'auth_pam_dashboard_timeout',
        'fastcgiTimeout': 'fast_cgi_timeout',
        'hostnameLookup': 'hostname_lookup',
        'logLevel': 'log_level',
        'maxClients': 'max_clients',
        'redirectHttpToHttps': 'redirect_http_to_https',
        'sslPort': 'ssl_port',
        'sslCiphersuite': 'ssl_cipher_suite',
        'sslProtocol': 'ssl_protocols'
    }

    api_attributes = [
        'authPamIdleTimeout', 'authPamValidateIp', 'authName', 'authPamDashboardTimeout',
        'fastcgiTimeout', 'hostnameLookup', 'logLevel', 'maxClients', 'sslPort',
        'redirectHttpToHttps', 'allow', 'sslCiphersuite', 'sslProtocol'
    ]

    returnables = [
        'auth_pam_idle_timeout', 'auth_pam_validate_ip', 'auth_name',
        'auth_pam_dashboard_timeout', 'fast_cgi_timeout', 'hostname_lookup',
        'log_level', 'max_clients', 'redirect_http_to_https', 'ssl_port',
        'allow', 'ssl_cipher_suite', 'ssl_protocols'
    ]

    updatables = [
        'auth_pam_idle_timeout', 'auth_pam_validate_ip', 'auth_name',
        'auth_pam_dashboard_timeout', 'fast_cgi_timeout', 'hostname_lookup',
        'log_level', 'max_clients', 'redirect_http_to_https', 'ssl_port',
        'allow', 'ssl_cipher_suite', 'ssl_protocols'
    ]

    _ciphers = "ECDHE-RSA-AES128-GCM-SHA256:" \
        "ECDHE-RSA-AES256-GCM-SHA384:" \
        "ECDHE-RSA-AES128-SHA:" \
        "ECDHE-RSA-AES256-SHA:" \
        "ECDHE-RSA-AES128-SHA256:" \
        "ECDHE-RSA-AES256-SHA384:" \
        "ECDHE-ECDSA-AES128-GCM-SHA256:" \
        "ECDHE-ECDSA-AES256-GCM-SHA384:" \
        "ECDHE-ECDSA-AES128-SHA:" \
        "ECDHE-ECDSA-AES256-SHA:" \
        "ECDHE-ECDSA-AES128-SHA256:" \
        "ECDHE-ECDSA-AES256-SHA384:" \
        "AES128-GCM-SHA256:" \
        "AES256-GCM-SHA384:" \
        "AES128-SHA:" \
        "AES256-SHA:" \
        "AES128-SHA256:" \
        "AES256-SHA256:" \
        "ECDHE-RSA-DES-CBC3-SHA:" \
        "ECDHE-ECDSA-DES-CBC3-SHA:" \
        "DES-CBC3-SHA"

    _protocols = 'all -SSLv2 -SSLv3'

    @property
    def auth_pam_idle_timeout(self):
        if self._values['auth_pam_idle_timeout'] is None:
            return None
        return int(self._values['auth_pam_idle_timeout'])

    @property
    def fast_cgi_timeout(self):
        if self._values['fast_cgi_timeout'] is None:
            return None
        return int(self._values['fast_cgi_timeout'])

    @property
    def max_clients(self):
        if self._values['max_clients'] is None:
            return None
        return int(self._values['max_clients'])

    @property
    def ssl_port(self):
        if self._values['ssl_port'] is None:
            return None
        return int(self._values['ssl_port'])


class ModuleParameters(Parameters):
    @property
    def auth_pam_validate_ip(self):
        if self._values['auth_pam_validate_ip'] is None:
            return None
        if self._values['auth_pam_validate_ip']:
            return "on"
        return "off"

    @property
    def auth_pam_dashboard_timeout(self):
        if self._values['auth_pam_dashboard_timeout'] is None:
            return None
        if self._values['auth_pam_dashboard_timeout']:
            return "on"
        return "off"

    @property
    def hostname_lookup(self):
        if self._values['hostname_lookup'] is None:
            return None
        if self._values['hostname_lookup']:
            return "on"
        return "off"

    @property
    def redirect_http_to_https(self):
        if self._values['redirect_http_to_https'] is None:
            return None
        if self._values['redirect_http_to_https']:
            return "enabled"
        return "disabled"

    @property
    def allow(self):
        if self._values['allow'] is None:
            return None
        if self._values['allow'][0] == 'all':
            return 'all'
        if self._values['allow'][0] == '':
            return ''
        allow = self._values['allow']
        result = list(set([str(x) for x in allow]))
        result = sorted(result)
        return result

    @property
    def ssl_cipher_suite(self):
        if self._values['ssl_cipher_suite'] is None:
            return None
        if isinstance(self._values['ssl_cipher_suite'], string_types):
            ciphers = self._values['ssl_cipher_suite'].strip()
        else:
            ciphers = self._values['ssl_cipher_suite']
        if not ciphers:
            raise F5ModuleError(
                "ssl_cipher_suite may not be set to 'none'"
            )
        if ciphers == 'default':
            ciphers = ':'.join(sorted(Parameters._ciphers.split(':')))
        elif isinstance(self._values['ssl_cipher_suite'], string_types):
            ciphers = ':'.join(sorted(ciphers.split(':')))
        else:
            ciphers = ':'.join(sorted(ciphers))
        return ciphers

    @property
    def ssl_protocols(self):
        if self._values['ssl_protocols'] is None:
            return None
        if isinstance(self._values['ssl_protocols'], string_types):
            protocols = self._values['ssl_protocols'].strip()
        else:
            protocols = self._values['ssl_protocols']
        if not protocols:
            raise F5ModuleError(
                "ssl_protocols may not be set to 'none'"
            )
        if protocols == 'default':
            protocols = ' '.join(sorted(Parameters._protocols.split(' ')))
        elif isinstance(protocols, string_types):
            protocols = ' '.join(sorted(protocols.split(' ')))
        else:
            protocols = ' '.join(sorted(protocols))
        return protocols


class ApiParameters(Parameters):
    @property
    def allow(self):
        if self._values['allow'] is None:
            return ''
        if self._values['allow'][0] == 'All':
            return 'all'
        allow = self._values['allow']
        result = list(set([str(x) for x in allow]))
        result = sorted(result)
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
    pass


class ReportableChanges(Changes):
    @property
    def ssl_cipher_suite(self):
        default = ':'.join(sorted(Parameters._ciphers.split(':')))
        if self._values['ssl_cipher_suite'] == default:
            return 'default'
        else:
            return self._values['ssl_cipher_suite']

    @property
    def ssl_protocols(self):
        default = ' '.join(sorted(Parameters._protocols.split(' ')))
        if self._values['ssl_protocols'] == default:
            return 'default'
        else:
            return self._values['ssl_protocols']


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
    def allow(self):
        if self.want.allow is None:
            return None
        if self.want.allow == 'all' and self.have.allow == 'all':
            return None
        if self.want.allow == 'all':
            return ['All']
        if self.want.allow == '' and self.have.allow == '':
            return None
        if self.want.allow == '':
            return []
        if self.want.allow != self.have.allow:
            return self.want.allow


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Changes(params=changed)

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
        result = dict()

        try:
            changed = self.present()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        return self.update()

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.sys.httpd.load()
        try:
            resource.modify(**params)
            return True
        except ConnectionError as ex:
            # BIG-IP will kill your management connection when you change the HTTP
            # redirect setting. So this catches that and handles it gracefully.
            if 'Connection aborted' in str(ex) and 'redirectHttpToHttps' in params:
                # Wait for BIG-IP web server to settle after changing this
                time.sleep(2)
                return True
            raise F5ModuleError(str(ex))

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.httpd.load()
        return ApiParameters(params=resource.attrs)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            allow=dict(
                type='list'
            ),
            auth_name=dict(),
            auth_pam_idle_timeout=dict(
                type='int'
            ),
            fast_cgi_timeout=dict(
                type='int'
            ),
            max_clients=dict(
                type='int'
            ),
            ssl_port=dict(
                type='int'
            ),
            auth_pam_validate_ip=dict(
                type='bool'
            ),
            auth_pam_dashboard_timeout=dict(
                type='bool'
            ),
            hostname_lookup=dict(
                type='bool'
            ),
            log_level=dict(
                choices=[
                    'alert', 'crit', 'debug', 'emerg',
                    'error', 'info', 'notice', 'warn'
                ]
            ),
            redirect_http_to_https=dict(
                type='bool'
            ),
            ssl_cipher_suite=dict(type='raw'),
            ssl_protocols=dict(type='raw')
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")
    if not HAS_REQUESTS:
        module.fail_json(msg="The python requests module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
