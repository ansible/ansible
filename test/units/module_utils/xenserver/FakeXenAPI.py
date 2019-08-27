# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

FAKE_API_VERSION = "1.1"


class Failure(Exception):
    def __init__(self, details):
        self.details = details

    def __str__(self):
        return str(self.details)


class Session(object):
    def __init__(self, uri, transport=None, encoding=None, verbose=0,
                 allow_none=1, ignore_ssl=False):

        self.transport = transport
        self._session = None
        self.last_login_method = None
        self.last_login_params = None
        self.API_version = FAKE_API_VERSION

    def _get_api_version(self):
        return FAKE_API_VERSION

    def _login(self, method, params):
        self._session = "OpaqueRef:fake-xenapi-session-ref"
        self.last_login_method = method
        self.last_login_params = params
        self.API_version = self._get_api_version()

    def _logout(self):
        self._session = None
        self.last_login_method = None
        self.last_login_params = None
        self.API_version = FAKE_API_VERSION

    def xenapi_request(self, methodname, params):
        if methodname.startswith('login'):
            self._login(methodname, params)
            return None
        elif methodname == 'logout' or methodname == 'session.logout':
            self._logout()
            return None
        else:
            # Should be patched with mocker.patch().
            return None

    def __getattr__(self, name):
        if name == 'handle':
            return self._session
        elif name == 'xenapi':
            # Should be patched with mocker.patch().
            return None
        elif name.startswith('login') or name.startswith('slave_local'):
            return lambda *params: self._login(name, params)
        elif name == 'logout':
            return self._logout


def xapi_local():
    return Session("http://_var_lib_xcp_xapi/")
