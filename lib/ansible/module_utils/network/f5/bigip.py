# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import re

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
        if self._client:
            return self._client

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
            error = 'Unable to connect to {0} on port {1}. The reported error was "{0}".'.format(
                self.provider['server'], self.provider['server_port'], str(ex)
            )
            raise F5ModuleError(error)


class F5RestClient(F5BaseClient):
    def __init__(self, *args, **kwargs):
        super(F5RestClient, self).__init__(*args, **kwargs)
        self.provider = self.merge_provider_params()
        self.headers = {
            'Content-Type': 'application/json'
        }

    @property
    def api(self):
        if self._client:
            return self._client
        session, err = self.connect_via_token_auth()
        if err or session is None:
            session, err = self.connect_via_basic_auth()
            if err or session is None:
                raise F5ModuleError(err)
        self._client = session
        return session

    def connect_via_token_auth(self):
        url = "https://{0}:{1}/mgmt/shared/authn/login".format(
            self.provider['server'], self.provider['server_port']
        )
        payload = {
            'username': self.provider['user'],
            'password': self.provider['password'],
            'loginProviderName': self.provider['auth_provider'] or 'tmos'
        }
        session = iControlRestSession(
            validate_certs=self.provider['validate_certs']
        )

        response = session.post(
            url,
            json=payload,
            headers=self.headers
        )

        if response.status not in [200]:
            return None, response.content

        session.request.headers['X-F5-Auth-Token'] = response.json()['token']['token']
        return session, None

    def connect_via_basic_auth(self):
        url = "https://{0}:{1}/mgmt/tm/sys".format(
            self.provider['server'], self.provider['server_port']
        )
        session = iControlRestSession(
            url_username=self.provider['user'],
            url_password=self.provider['password'],
            validate_certs=self.provider['validate_certs'],
        )

        response = session.get(
            url,
            headers=self.headers
        )

        if response.status not in [200]:
            return None, response.content
        return session, None

    def get_identifier(self, proxy_to):
        if re.search(r'([0-9-a-z]+\-){4}[0-9-a-z]+', proxy_to, re.I):
            return proxy_to
        return self.get_device_uuid(proxy_to)

    def get_device_uuid(self, proxy_to):
        uri = "https://{0}:{1}/mgmt/shared/resolver/device-groups/cm-cloud-managed-devices/devices/?$filter=hostname+eq+'{2}'&$select=uuid".format(
            self.provider['server'], self.provider['server_port'], proxy_to
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

        if len(collection) > 1:
            raise F5ModuleError(
                "More that one managed device was found with this hostname. "
                "'proxy_to' devices must be unique. Consider specifying the UUID of the device."
            )
        elif len(collection) == 0:
            raise F5ModuleError(
                "No device was found with that hostname"
            )
        else:
            resource = collection.pop()
            return resource.pop('uuid', None)
