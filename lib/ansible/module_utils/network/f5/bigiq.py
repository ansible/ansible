# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import os
import time

try:
    from f5.bigiq import ManagementRoot
    from icontrol.exceptions import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False

try:
    from library.module_utils.network.f5.common import F5BaseClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import is_ansible_debug
    from library.module_utils.network.f5.icontrol import iControlRestSession
except ImportError:
    from ansible.module_utils.network.f5.common import F5BaseClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import is_ansible_debug
    from ansible.module_utils.network.f5.icontrol import iControlRestSession


class F5Client(F5BaseClient):
    def __init__(self, *args, **kwargs):
        super(F5Client, self).__init__(*args, **kwargs)
        self.provider = self.merge_provider_params()

    @property
    def api(self):
        exc = None
        if self._client:
            return self._client
        for x in range(0, 10):
            try:
                result = ManagementRoot(
                    self.provider['server'],
                    self.provider['user'],
                    self.provider['password'],
                    port=self.provider['server_port'],
                    verify=self.provider['validate_certs']
                )
                self._client = result
                return self._client
            except Exception as ex:
                exc = ex
                time.sleep(1)
        error = 'Unable to connect to {0} on port {1}.'.format(
            self.provider['server'], self.provider['server_port']
        )

        if exc is not None:
            error += ' The reported error was "{0}".'.format(str(exc))
        raise F5ModuleError(error)


class F5RestClient(F5BaseClient):
    def __init__(self, *args, **kwargs):
        super(F5RestClient, self).__init__(*args, **kwargs)
        self.provider = self.merge_provider_params()

    @property
    def api(self):
        exc = None
        if self._client:
            return self._client
        for x in range(0, 10):
            try:
                provider = self.provider['auth_provider'] or 'local'
                url = "https://{0}:{1}/mgmt/shared/authn/login".format(
                    self.provider['server'], self.provider['server_port']
                )
                payload = {
                    'username': self.provider['user'],
                    'password': self.provider['password'],
                }

                # - local is a special provider that is baked into the system and
                #   has no loginReference
                if provider != 'local':
                    login_ref = self.get_login_ref(provider)
                    payload.update(login_ref)

                session = iControlRestSession()
                session.verify = self.provider['validate_certs']
                response = session.post(url, json=payload)

                if response.status not in [200]:
                    raise F5ModuleError('Status code: {0}. Unexpected Error: {1} for uri: {2}\nText: {3}'.format(
                        response.status, response.reason, response.url, response.content
                    ))

                session.headers['X-F5-Auth-Token'] = response.json()['token']['token']
                self._client = session
                return self._client
            except Exception as ex:
                exc = ex
                time.sleep(1)
        error = 'Unable to connect to {0} on port {1}.'.format(
            self.provider['server'], self.provider['server_port']
        )
        if exc is not None:
            error += ' The reported error was "{0}".'.format(str(exc))
        raise F5ModuleError(error)

    def get_login_ref(self, provider):
        info = self.read_provider_info_from_device()
        uuids = [os.path.basename(os.path.dirname(x['link'])) for x in info['providers'] if '-' in x['link']]
        if provider in uuids:
            name = self.get_name_of_provider_id(info, provider)
            if not name:
                raise F5ModuleError(
                    "No name found for the provider '{0}'".format(provider)
                )
            return dict(
                loginReference=dict(
                    link="https://localhost/mgmt/cm/system/authn/providers/{0}/{1}/login".format(name, provider)
                )
            )
        names = [os.path.basename(os.path.dirname(x['link'])) for x in info['providers'] if '-' in x['link']]
        if names.count(provider) > 1:
            raise F5ModuleError(
                "Ambiguous auth_provider provided. Please specify a specific provider ID."
            )
        uuid = self.get_id_of_provider_name(info, provider)
        if not uuid:
            raise F5ModuleError(
                "No name found for the provider '{0}'".format(provider)
            )
        return dict(
            loginReference=dict(
                link="https://localhost/mgmt/cm/system/authn/providers/{0}/{1}/login".format(provider, uuid)
            )
        )

    def get_name_of_provider_id(self, info, provider):
        # Add slashes to the provider name so that it specifically finds the provider
        # as part of the URL and not a part of another substring
        provider = '/' + provider + '/'
        for x in info['providers']:
            if x['link'].find(provider) > -1:
                return x['name']
        return None

    def get_id_of_provider_name(self, info, provider):
        for x in info['providers']:
            if x['name'] == provider:
                return os.path.basename(os.path.dirname(x['link']))
        return None

    def read_provider_info_from_device(self):
        uri = "https://{0}:{1}/info/system".format(
            self.provider['server'], self.provider['server_port']
        )
        session = iControlRestSession()
        session.verify = self.provider['validate_certs']

        resp = session.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response
