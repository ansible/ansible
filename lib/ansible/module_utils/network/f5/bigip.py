# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import time

try:
    from f5.bigip import ManagementRoot
    from icontrol.exceptions import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False

try:
    from library.module_utils.network.f5.common import F5BaseClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.icontrol import iControlRestSession
except ImportError:
    from ansible.module_utils.network.f5.common import F5BaseClient
    from ansible.module_utils.network.f5.common import F5ModuleError
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

        for x in range(0, 60):
            try:
                result = ManagementRoot(
                    self.provider['server'],
                    self.provider['user'],
                    self.provider['password'],
                    port=self.provider['server_port'],
                    verify=self.provider['validate_certs'],
                    token='tmos'
                )
                self._client = result
                return self._client
            except Exception as ex:
                exc = ex
                time.sleep(1)
        error = 'Unable to connect to {0} on port {1}.'.format(
            self.params['server'], self.params['server_port']
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
                url = "https://{0}:{1}/mgmt/shared/authn/login".format(
                    self.provider['server'], self.provider['server_port']
                )
                payload = {
                    'username': self.provider['user'],
                    'password': self.provider['password'],
                    'loginProviderName': self.provider['auth_provider'] or 'tmos'
                }
                session = iControlRestSession()
                session.verify = self.provider['validate_certs']
                response = session.post(url, json=payload)

                if response.status not in [200]:
                    raise F5ModuleError('Status code: {0}. Unexpected Error: {1} for uri: {2}\nText: {3}'.format(
                        response.status, response.reason, response.url, response._content
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
