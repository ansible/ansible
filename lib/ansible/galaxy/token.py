########################################################################
#
# (C) 2015, Chris Houseknecht <chouse@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import os
import json
from stat import S_IRUSR, S_IWUSR

import yaml

from ansible import constants as C
from ansible.galaxy.user_agent import user_agent
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.urls import open_url
from ansible.utils.display import Display

display = Display()


class NoTokenSentinel(object):
    """ Represents an ansible.cfg server with not token defined (will ignore cmdline and GALAXY_TOKEN_PATH. """
    def __new__(cls, *args, **kwargs):
        return cls


class KeycloakToken(object):
    '''A token granted by a Keycloak server.

    Like sso.redhat.com as used by cloud.redhat.com
    ie Automation Hub'''

    token_type = 'Bearer'

    def __init__(self, access_token=None, auth_url=None, validate_certs=True):
        self.access_token = access_token
        self.auth_url = auth_url
        self._token = None
        self.validate_certs = validate_certs

    def _form_payload(self):
        return 'grant_type=refresh_token&client_id=cloud-services&refresh_token=%s' % self.access_token

    def get(self):
        if self._token:
            return self._token

        # - build a request to POST to auth_url
        #  - body is form encoded
        #    - 'request_token' is the offline token stored in ansible.cfg
        #    - 'grant_type' is 'refresh_token'
        #    - 'client_id' is 'cloud-services'
        #       - should probably be based on the contents of the
        #         offline_ticket's JWT payload 'aud' (audience)
        #         or 'azp' (Authorized party - the party to which the ID Token was issued)
        payload = self._form_payload()

        resp = open_url(to_native(self.auth_url),
                        data=payload,
                        validate_certs=self.validate_certs,
                        method='POST',
                        http_agent=user_agent())

        # TODO: handle auth errors

        data = json.loads(to_text(resp.read(), errors='surrogate_or_strict'))

        # - extract 'access_token'
        self._token = data.get('access_token')

        return self._token

    def headers(self):
        headers = {}
        headers['Authorization'] = '%s %s' % (self.token_type, self.get())
        return headers


class GalaxyToken(object):
    ''' Class to storing and retrieving local galaxy token '''

    token_type = 'Token'

    def __init__(self, token=None):
        self.b_file = to_bytes(C.GALAXY_TOKEN_PATH, errors='surrogate_or_strict')
        # Done so the config file is only opened when set/get/save is called
        self._config = None
        self._token = token

    @property
    def config(self):
        if self._config is None:
            self._config = self._read()

        # Prioritise the token passed into the constructor
        if self._token:
            self._config['token'] = None if self._token is NoTokenSentinel else self._token

        return self._config

    def _read(self):
        action = 'Opened'
        if not os.path.isfile(self.b_file):
            # token file not found, create and chmod u+rw
            open(self.b_file, 'w').close()
            os.chmod(self.b_file, S_IRUSR | S_IWUSR)  # owner has +rw
            action = 'Created'

        with open(self.b_file, 'r') as f:
            config = yaml.safe_load(f)

        display.vvv('%s %s' % (action, to_text(self.b_file)))

        if config and not isinstance(config, dict):
            display.vvv('Galaxy token file %s malformed, unable to read it' % to_text(self.b_file))
            return {}

        return config or {}

    def set(self, token):
        self._token = token
        self.save()

    def get(self):
        return self.config.get('token', None)

    def save(self):
        with open(self.b_file, 'w') as f:
            yaml.safe_dump(self.config, f, default_flow_style=False)

    def headers(self):
        headers = {}
        token = self.get()
        if token:
            headers['Authorization'] = '%s %s' % (self.token_type, self.get())
        return headers


class BasicAuthToken(object):
    token_type = 'Basic'

    def __init__(self, username, password=None):
        self.username = username
        self.password = password
        self._token = None

    @staticmethod
    def _encode_token(username, password):
        token = "%s:%s" % (to_text(username, errors='surrogate_or_strict'),
                           to_text(password, errors='surrogate_or_strict', nonstring='passthru') or '')
        b64_val = base64.b64encode(to_bytes(token, encoding='utf-8', errors='surrogate_or_strict'))
        return to_text(b64_val)

    def get(self):
        if self._token:
            return self._token

        self._token = self._encode_token(self.username, self.password)

        return self._token

    def headers(self):
        headers = {}
        headers['Authorization'] = '%s %s' % (self.token_type, self.get())
        return headers
