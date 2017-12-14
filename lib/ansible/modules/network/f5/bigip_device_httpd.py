#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_device_httpd
short_description: Manage HTTPD related settings on BIG-IP
description:
  - Manages HTTPD related settings on the BIG-IP. These settings are interesting
    to change when you want to set GUI timeouts and other TMUI related settings.
version_added: "2.5"
options:
  auth_name:
    description:
      - Sets the BIG-IP authentication realm name
  auth_pam_idle_timeout:
    description:
      - Sets the GUI timeout for automatic logout, in seconds.
  auth_pam_validate_ip:
    description:
      - Sets the authPamValidateIp setting.
    choices: ['on', 'off']
  auth_pam_dashboard_timeout:
    description:
      - Sets whether or not the BIG-IP dashboard will timeout.
    choices: ['on', 'off']
  fast_cgi_timeout:
    description:
      - Sets the timeout of FastCGI.
  hostname_lookup:
    description:
      - Sets whether or not to display the hostname, if possible.
    choices: ['on', 'off']
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
    choices: ['yes', 'no']
  ssl_port:
    description:
      - The HTTPS port to listen on.
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - Requires the requests Python package on the host. This is as easy as
    pip install requests.
requirements:
  - f5-sdk >= 3.0.4
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
'''

RETURN = r'''
auth_pam_idle_timeout:
  description: The new number of seconds for GUI timeout.
  returned: changed
  type: string
  sample: 1200
'''

import time

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError
from ansible.module_utils.six import iteritems
from collections import defaultdict

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
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
        'sslPort': 'ssl_port'
    }

    api_attributes = [
        'authPamIdleTimeout', 'authPamValidateIp', 'authName', 'authPamDashboardTimeout',
        'fastcgiTimeout', 'hostnameLookup', 'logLevel', 'maxClients', 'sslPort',
        'redirectHttpToHttps'
    ]

    returnables = [
        'auth_pam_idle_timeout', 'auth_pam_validate_ip', 'auth_name',
        'auth_pam_dashboard_timeout', 'fast_cgi_timeout', 'hostname_lookup',
        'log_level', 'max_clients', 'redirect_http_to_https', 'ssl_port'
    ]

    updatables = [
        'auth_pam_idle_timeout', 'auth_pam_validate_ip', 'auth_name',
        'auth_pam_dashboard_timeout', 'fast_cgi_timeout', 'hostname_lookup',
        'log_level', 'max_clients', 'redirect_http_to_https', 'ssl_port'
    ]

    def __init__(self, params=None):
        self._values = defaultdict(lambda: None)
        self._values['__warnings'] = []
        if params:
            self.update(params=params)

    def update(self, params=None):
        if params:
            for k, v in iteritems(params):
                if self.api_map is not None and k in self.api_map:
                    map_key = self.api_map[k]
                else:
                    map_key = k

                # Handle weird API parameters like `dns.proxy.__iter__` by
                # using a map provided by the module developer
                class_attr = getattr(type(self), map_key, None)
                if isinstance(class_attr, property):
                    # There is a mapped value for the api_map key
                    if class_attr.fset is None:
                        # If the mapped value does not have
                        # an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result

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


class ApiParameters(Parameters):
    pass


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
    pass


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


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.want = ModuleParameters(params=self.client.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Changes(changed)

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
            self.changes = UsableChanges(changed)
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

        reportable = ReportableChanges(self.changes.to_return())
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
        return self.update()

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.client.check_mode:
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
            pass

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
        self.argument_spec = dict(
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
            )
        )
        self.f5_product_name = 'bigip'


def cleanup_tokens(client):
    try:
        resource = client.api.shared.authz.tokens_s.token.load(
            name=client.api.icrs.token
        )
        resource.delete()
    except Exception:
        pass


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    if not HAS_REQUESTS:
        raise F5ModuleError("The python requests module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        cleanup_tokens(client)
        client.module.exit_json(**results)
    except F5ModuleError as e:
        cleanup_tokens(client)
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
