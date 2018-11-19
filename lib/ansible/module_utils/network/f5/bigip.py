# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


try:
    from library.module_utils.network.f5.common import F5BaseClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.icontrol import iControlRestSession
except ImportError:
    from ansible.module_utils.network.f5.common import F5BaseClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.icontrol import iControlRestSession


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
