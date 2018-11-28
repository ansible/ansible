# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import os


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
        if err:
            raise F5ModuleError(err)
        self._client = session
        return session

    def connect_via_token_auth(self):
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
