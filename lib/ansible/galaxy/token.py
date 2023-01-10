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
import json
import os
import string

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
except ImportError:
    HAS_CRYPTO = False
else:
    HAS_CRYPTO = True
from datetime import datetime, timedelta, timezone
from stat import S_IRUSR, S_IWUSR
from urllib.error import HTTPError, URLError

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.galaxy.user_agent import user_agent
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.module_utils.common.yaml import yaml_dump, yaml_load
from ansible.module_utils.urls import open_url
from ansible.utils.display import Display

display = Display()

AH_TOKEN_EXPIRES_N_MIN_EARLY = 1

# https://www.rfc-editor.org/rfc/rfc7518#section-3.1
REQUIRED_JWT_HEADER_KEYS = {'alg', 'typ', 'kid'}
REQUIRED_JWT_HEADER_VALUES = {
    'alg': ['RS256'],
    'typ': ['JWT'],
}


def assert_jwt_structure(raw_jwt_string):
    """Test that given JWT string looks valid.

    :raises InvalidSignature: If it isn't.
    """
    if raw_jwt_string.count('.') != 2:
        raise InvalidSignature(f"unsupported format: {raw_jwt_string}")

    if any(
        possible_whitespace in string.whitespace
        for possible_whitespace in raw_jwt_string.rsplit('.')[0]
    ):
        raise InvalidSignature(f"JWS header and payload should not contain line breaks or whitespace: {raw_jwt_string.rsplit('.')[0]}")


def assert_jwt_header(header):
    """Test that given JWT header looks valid.

    :raises InvalidSignature: If it isn't.
    """
    if (
        set(header) != REQUIRED_JWT_HEADER_KEYS
        or any(header[key] not in value for key, value in REQUIRED_JWT_HEADER_VALUES.items())
    ):
        raise InvalidSignature(f"unsupported header: {header}")


def b64urlsafe_to_long(data):
    decoded_bytes = base64.urlsafe_b64decode(
        to_bytes(data, errors="surrogate_or_strict") + b"=="
    )
    return int(decoded_bytes.hex(), 16)


def parse_b64urlsafe_as_json(data):
    decoded_bytes = base64.urlsafe_b64decode(
        to_bytes(data, errors="surrogate_or_strict") + b"=="
    )
    return json.loads(decoded_bytes)


def normalize_datetime_fields(token_info):
    for datetime_field in ['exp', 'iat', 'auth_time']:
        if datetime_field not in token_info:
            continue
        token_info[datetime_field] = datetime.fromtimestamp(token_info[datetime_field], timezone.utc)
    return token_info


def get_public_numbers(header, jwks):
    """Return the public key numbers matching the key ID in the JWT header.

    :raises InvalidSignature: If the expected key isn't found.
    """
    public_key_id = header['kid']
    for key in jwks:
        if key['kid'] == public_key_id:
            return key['e'], key['n']
    raise InvalidSignature(f"Public key {public_key_id} was not found in JWKS")


def parse_bearer_token(data, jwks=None):
    assert_jwt_structure(data)

    data = to_bytes(data)
    signing_input, b64signature = data.rsplit(b".", 1)
    b64header_data, b64payload_data = signing_input.split(b".")

    header = parse_b64urlsafe_as_json(b64header_data)
    assert_jwt_header(header)

    token_info = parse_b64urlsafe_as_json(b64payload_data)
    signature = base64.urlsafe_b64decode(b64signature + b"==")

    e, n = get_public_numbers(header, jwks)
    public_key = RSAPublicNumbers(
        b64urlsafe_to_long(e),
        b64urlsafe_to_long(n),
    ).public_key()

    try:
        result = public_key.verify(signature, signing_input, PKCS1v15(), SHA256())
    except InvalidSignature as e:
        if not e.args:
            # give some debug info for clues
            display.vvvv(f"{signing_input} could not be verified with signature {signature}")
            display.vvvv(f"Public key exponent: {e}")
            display.vvvv(f"Public key modulus: {n}")
        raise

    display.vvvv("Successfully validated JWT signature")
    return normalize_datetime_fields(token_info)


class NoTokenSentinel(object):
    """ Represents an ansible.cfg server with not token defined (will ignore cmdline and GALAXY_TOKEN_PATH. """
    def __new__(cls, *args, **kwargs):
        return cls


class KeycloakToken(object):
    '''A token granted by a Keycloak server.

    Like sso.redhat.com as used by cloud.redhat.com
    ie Automation Hub'''

    token_type = 'Bearer'

    def __init__(self, access_token=None, auth_url=None, validate_certs=True, client_id=None, openid_configuration=None):
        self.access_token = access_token
        self._token = None
        self._expires_at = None
        self.validate_certs = validate_certs
        self.client_id = client_id
        if self.client_id is None:
            self.client_id = 'cloud-services'

        self._auth_url = auth_url
        self._jwks_url = None
        self._openid_url = openid_configuration

        self.jwks = None

    @property
    def auth_url(self):
        if self._auth_url is None:
            try:
                with open_url(
                    to_native(self._openid_url),
                    data=f"client_id={self.client_id!s}",
                    validate_certs=self.validate_certs,
                    method='GET',
                    http_agent=user_agent()
                ) as openid_config:
                    openid_config_data = openid_config.read()
            except (HTTPError, URLError) as e:
                raise AnsibleOptionsError(f"Unable to load OpenID configuration from {self._openid_url!s}: {e!s}") from e

            try:
                openid_config_data = json.loads(openid_config_data)
            except ValueError as e:
                raise AnsibleError(f"OpenID configuration is not valid json: {e!s}") from e

            try:
                self._auth_url = openid_config_data['token_endpoint']
                self._jwks_url = openid_config_data['jwks_uri']
            except KeyError as e:
                raise AnsibleError(f"OpenID configuration is missing required fields: {e!s}") from e

        return self._auth_url

    @property
    def expired(self):
        if self._expires_at is None:
            return False
        # expire early to handle refreshing proactively
        return datetime.now(tz=timezone.utc) > self._expires_at - timedelta(minutes=AH_TOKEN_EXPIRES_N_MIN_EARLY)

    def _form_payload(self):
        return 'grant_type=refresh_token&client_id=%s&refresh_token=%s' % (self.client_id,
                                                                           self.access_token)

    def get(self):
        if self._token and not self.expired:
            return self._token
        if self._token:
            display.vvv("Refreshing KeycloakToken")

        # - build a request to POST to auth_url
        #  - body is form encoded
        #    - 'refresh_token' is the offline token stored in ansible.cfg
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

        if self.jwks is None and self._jwks_url is not None:
            if not HAS_CRYPTO:
                raise AnsibleError('The python library cryptography is required for token validation.')

            try:
                with open_url(
                    to_native(self._jwks_url),
                    data=payload,
                    validate_certs=self.validate_certs,
                    method='GET',
                    http_agent=user_agent()
                ) as jwks_resp:
                    jwks_data = jwks_resp.read()
            except (HTTPError, URLError) as e:
                raise AnsibleError(f"Error fetching public keys for token validation: {e!s}") from e

            try:
                self.jwks = json.loads(jwks_data).get('keys', [])
            except ValueError as e:
                raise AnsibleError(f"Invalid public keys for token validation: {e!s}") from e

        # - extract token details
        self._token = data.get('access_token')

        if self.jwks is not None:
            try:
                token_data = parse_bearer_token(data['id_token'], jwks=self.jwks)
            except InvalidSignature as e:
                # something went wrong parsing or validating the JWT, this is unexpected
                # might need to support other algorithms?
                # this isn't fatal to keep backwards compat, just won't get to use proactive token refreshing
                orig_error = f': {e}' if e.args else ''
                display.warning(f'Failed to verify JWS{orig_error}. The token will not be refreshed during long-running operations.')
            else:
                self._expires_at = token_data.get('exp')

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
            config = yaml_load(f)

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
            yaml_dump(self.config, f, default_flow_style=False)

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
